"""
Optimized FastAPI application for Google Sheets batch processing
Triggers ImmoCalcul scraper for eligible rows and updates sheet with results
"""
import os
import uuid
import logging
import threading
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from config import Config
from logger_config import set_step
from sheet_processor import process_all_sheet_rows
from docker_manager import run_container, stop_container, remove_container

# Validate configuration on startup
if not Config.validate():
    raise RuntimeError("Invalid configuration. Check logs for details.")

app = FastAPI(
    title="ImmoCalcul Sheet Processor",
    description="Batch process Google Sheets with ImmoCalcul scraper",
    version="1.0.0",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track active jobs (in-memory; use Redis for production)
active_jobs = {}
job_lock = threading.Lock()
active_job_id = None
CONTAINER_NAME = "immocalcul-batch"

def run_async_job(job_id: str):
    """Run the batch processor inside a Docker container in the background."""
    global active_job_id
    try:
        active_jobs[job_id] = {
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }

        container_name = CONTAINER_NAME
        volumes = {
            f"{os.getcwd()}/run_steps": "/app/run_steps",
            f"{os.getcwd()}/logs": "/app/logs",
        }
        env = {
            "IMMOCALCUL_EMAIL": Config.IMMOCALCUL_EMAIL or "",
            "IMMOCALCUL_PASSWORD": Config.IMMOCALCUL_PASSWORD or "",
            "PARENT_DRIVE_FOLDER_ID": Config.PARENT_DRIVE_FOLDER_ID or "",
            "USE_EXISTING_DRIVE_URL": str(Config.USE_EXISTING_DRIVE_URL),
            "SPREADSHEET_ID": str(Config.SPREADSHEET_ID),
            "WORKSHEET_GID": str(Config.WORKSHEET_GID),
        }
        command = ["python3", "sheet_processor.py", job_id]

        result = run_container(
            name=container_name,
            image="immocalcul-scraper",
            command=command,
            volumes=volumes,
            env=env,
        )

        if result.returncode == 0:
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            logging.info(f"✓ Job {job_id} completed successfully (Docker)")
        else:
            active_jobs[job_id]["status"] = "failed"
            active_jobs[job_id]["error"] = result.stderr or result.stdout
            active_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()
            logging.error(f"✗ Job {job_id} failed in Docker: {result.stderr}")

    except Exception as e:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["failed_at"] = datetime.utcnow().isoformat()
        logging.error(f"✗ Job {job_id} failed to launch Docker: {e}", exc_info=True)
    finally:
        active_job_id = None
        if job_lock.locked():
            job_lock.release()

@app.get("/immocalcul/run")
async def run_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Trigger batch processing of all eligible Google Sheet rows via GET request.
    
    Eligible rows:
    - Drive folder URL is present
    - Picture 1 is empty
    
    Returns immediately with job_id. Processing happens in background.
    Monitor progress via server logs.
    
    Returns:
        {
            "message": "Batch processing initiated successfully",
            "job_id": "uuid",
            "status": "running",
            "instructions": "Monitor server logs for progress"
        }
    """
    set_step("trigger")
    logging.info("="*60)
    logging.info("Received batch processing request")
    logging.info(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logging.info("="*60)
    
    global active_job_id
    previous_job_id = None
    if not job_lock.acquire(blocking=False):
        previous_job_id = active_job_id
        logging.info("New request received while job %s is running. Stopping previous container.", previous_job_id)
        if previous_job_id and previous_job_id in active_jobs:
            active_jobs[previous_job_id]["status"] = "superseded"
            active_jobs[previous_job_id]["superseded_at"] = datetime.utcnow().isoformat()
        stop_container(CONTAINER_NAME)
        remove_container(CONTAINER_NAME)
        acquired = job_lock.acquire(timeout=30)
        if not acquired:
            raise HTTPException(status_code=409, detail={
                "message": "Previous job is still shutting down",
                "active_job_id": active_job_id,
            })

    # Generate job ID
    job_id = str(uuid.uuid4())
    active_job_id = job_id
    
    # Schedule background task
    background_tasks.add_task(run_async_job, job_id)
    
    logging.info(f"✓ Job {job_id} initiated and queued for processing")
    logging.info("="*60)
    
    response = {
        "message": "Batch processing initiated successfully",
        "job_id": job_id,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "instructions": "Monitor server logs for real-time progress. Processing runs in background."
    }
    if previous_job_id:
        response["previous_job"] = {
            "job_id": previous_job_id,
            "status": "stopped_and_removed",
        }
    return response

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        {
            "status": "healthy",
            "timestamp": "ISO timestamp",
            "active_jobs": number of running jobs,
            "config_valid": true/false,
            "settings": {...}
        }
    """
    running_jobs = len([j for j in active_jobs.values() if j.get("status") == "running"])
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_jobs": running_jobs,
        "total_jobs": len(active_jobs),
        "config_valid": Config.validate(),
        "settings": {
            "spreadsheet_id": Config.SPREADSHEET_ID,
            "max_concurrent_scrapers": Config.MAX_CONCURRENT_SCRAPERS,
            "use_existing_drive_url": Config.USE_EXISTING_DRIVE_URL,
            "headless": Config.HEADLESS,
            "verbose_logging": Config.VERBOSE_LOGGING
        }
    }

@app.get("/jobs")
async def list_jobs():
    """
    List all jobs
    
    Returns:
        {
            "total": number,
            "jobs": [{job details}, ...]
        }
    """
    return {
        "total": len(active_jobs),
        "jobs": [
            {
                "job_id": job_id,
                **details
            }
            for job_id, details in active_jobs.items()
        ]
    }

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a specific job
    
    Parameters:
        job_id: UUID of the job
    
    Returns:
        {
            "job_id": "uuid",
            "status": "running|completed|failed",
            "started_at": "ISO timestamp",
            ...
        }
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        **active_jobs[job_id]
    }

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "ImmoCalcul Sheet Processor API",
        "version": "1.0.0",
        "description": "Automated batch processing for Google Sheets with ImmoCalcul scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "GET /immocalcul/run": {
                "description": "Trigger batch processing",
                "authentication": "Not required"
            },
            "GET /health": {
                "description": "Health check and system status",
                "authentication": "Not required"
            },
            "GET /jobs": {
                "description": "List all jobs",
                "authentication": "Not required"
            },
            "GET /jobs/{job_id}": {
                "description": "Get specific job status",
                "authentication": "Not required"
            },
            "GET /": {
                "description": "This page - API information",
                "authentication": "Not required"
            }
        },
        "documentation": {
            "interactive_docs": "/docs",
            "openapi_schema": "/openapi.json"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logging.info("="*60)
    logging.info("ImmoCalcul Sheet Processor API - Starting Up")
    logging.info("="*60)
    Config.log_config()
    logging.info("✓ Application started successfully")
    logging.info("="*60)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logging.info("="*60)
    logging.info("ImmoCalcul Sheet Processor API - Shutting Down")
    logging.info(f"Total jobs processed: {len(active_jobs)}")
    logging.info("="*60)

if __name__ == "__main__":
    port = Config.PORT
    log_level = Config.LOG_LEVEL.lower()
    
    logging.info("="*60)
    logging.info("Starting ImmoCalcul Sheet Processor API")
    logging.info(f"Port: {port}")
    logging.info(f"Log level: {log_level}")
    logging.info("="*60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        access_log=True
    )
