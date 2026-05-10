## Image Compression (Lossless, VPS & Simple Mode)

This project uses **lossless image compression** for screenshots and exported images:

- **PNG:** [optipng](http://optipng.sourceforge.net/) (lossless, open source)
- **JPEG:** [jpegoptim](https://github.com/tjko/jpegoptim) (lossless, open source)

These tools are installed automatically in the Docker image. If you run outside Docker (simple mode), install them on your VPS for best results:

```bash
sudo apt-get install optipng jpegoptim
# or
brew install optipng jpegoptim
```

If these tools are not available, the script will fallback to Pillow for basic optimization (not always lossless).

Compression is applied automatically after screenshots are saved and before PDF creation. Logs will show before/after file sizes.

# Docker Setup for ImmoCalcul Scraper (Docker CLI, no Compose)

This project uses **plain Docker commands** (not docker‑compose). The helper script
`docker-run.sh` is the recommended way to run locally or on a VPS.

## Quick Start (Docker CLI)

### 1. Build the Docker Image

```bash
docker build -t immocalcul-scraper .
```

### 2. Run the Scraper Inside Docker

**Option A: With virtual display (Xvfb)**

```bash
./docker-run.sh --lot 2607802 --virtual-display --record-video --trace
```

**Option B: Run the entrypoint directly**

```bash
docker run --rm -it \
   -v "$(pwd):/app" \
   -v "$(pwd)/logs:/app/logs" \
   -e IMMOCALCUL_EMAIL="$IMMOCALCUL_EMAIL" \
   -e IMMOCALCUL_PASSWORD="$IMMOCALCUL_PASSWORD" \
   -e PARENT_DRIVE_FOLDER_ID="$PARENT_DRIVE_FOLDER_ID" \
   immocalcul-scraper /app/docker-entrypoint.sh --lot 2607802
```

**Option C: Interactive bash (debugging)**

```bash
docker run --rm -it \
   -v "$(pwd):/app" \
   -v "$(pwd)/logs:/app/logs" \
   immocalcul-scraper bash
```

### 3. Output Files

All output (videos, traces, screenshots, summary.json) will be saved to:

```
./run_steps/<run_id>/
```

These are shared between your host and the Docker container via volume mount.

### 4. Logs

Logs are written under `/app/logs` in the container. The `./logs` folder is mounted
by `docker-run.sh`, so you should see files like:

- `logs/sc-immocalcul.log`
- `logs/sc-immocalcul-<run_id>.log`
- `logs/error.log`

## Environment Variables

The Docker CLI commands and `docker-run.sh` rely on these environment variables:

- `IMMOCALCUL_EMAIL`
- `IMMOCALCUL_PASSWORD`
- `PARENT_DRIVE_FOLDER_ID`
- `PROXY_HOST`, `PROXY_PORT`, `PROXY_USER`, `PROXY_PASS` (optional)

Load them via `.env` (supported by `docker-run.sh`) or export in your shell.

## FastAPI Triggered Batch Runs (VPS)

When the FastAPI service is running (via systemd/gunicorn), calling:

```
GET /immocalcul/run
```

will start a **fresh Docker container** that runs `sheet_processor.py`. The
application enforces **singleton execution**:

- If a container named `immocalcul-batch` is already running, it is **stopped**
   and **removed** before the new run starts.
- The response includes the new job ID and (if applicable) the previous job ID
   that was stopped and removed.

**Example response when a previous run was replaced:**

```json
{
   "message": "Batch processing initiated successfully",
   "job_id": "NEW_JOB_ID",
   "status": "running",
   "previous_job": {
      "job_id": "OLD_JOB_ID",
      "status": "stopped_and_removed"
   }
}
```

### Container Name (Fixed)

The application always uses the same container name:

```
immocalcul-batch
```

This is how singleton behavior is enforced and why older runs are safely
terminated when a new request comes in.

## Manually Stop a Running Container (VPS)

If you want to stop a run mid‑execution on the VPS, use:

```bash
docker stop immocalcul-batch
docker rm -f immocalcul-batch
```

To verify whether it is still running:

```bash
docker ps --filter "name=immocalcul-batch"
```

If you want to stop **all** related containers:

```bash
docker ps --filter "name=immocalcul" -q | xargs -r docker stop
docker ps --filter "name=immocalcul" -q | xargs -r docker rm -f
```

## Troubleshooting

### Display Issues
If you see "Cannot connect to display" errors, Xvfb may not have started. Check:

```bash
docker run --rm -it immocalcul-scraper bash
ps aux | grep Xvfb
```

### Permission Issues
If you get permission errors accessing `run_steps/`, run:

```bash
chmod -R 777 run_steps/
```

### Container Won't Start
Rebuild and check logs:

```bash
docker build --no-cache -t immocalcul-scraper .
docker run --rm -it immocalcul-scraper bash
```

## Development Workflow

1. **Test on macOS first** (fast iteration):
    ```bash
    python3 full_step_scraper.py --lot 2607802 --record-video --trace
    ```

2. **Test in Docker** (simulate VPS):
    ```bash
    ./docker-run.sh --lot 2607802 --virtual-display --record-video --trace
    ```

3. **Deploy to VPS** (with `--virtual-display` flag if using Xvfb there too)

## Useful Docker Commands

### View running containers
```bash
docker ps
```

### Stop all containers
```bash
docker stop $(docker ps -q)
```

### Remove all stopped containers
```bash
docker container prune
```

### Access container shell
```bash
docker run --rm -it immocalcul-scraper bash
```
