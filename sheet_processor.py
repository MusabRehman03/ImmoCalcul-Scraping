"""
Optimized Google Sheets processor with OAuth support
Updates Google Sheet immediately after each row is processed
"""
import os
import json
import subprocess
import shutil
import logging
import asyncio
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pydantic import BaseModel

from config import Config
from logger_config import set_step, add_run_log_handler

class SheetRow(BaseModel):
    """Model for a sheet row"""
    row_index: int
    lead_source: str = ""
    reference_number: str = ""
    type_propriete: str = ""
    price: float = 0.0
    cadastral_lot: str = ""
    street_number: str = ""
    street: str = ""
    city: str = ""
    postal_code: str = ""
    other_unit: str = ""
    mailing_unit: str = ""
    immocalcul_status: str = ""
    analyse_risque: str = ""
    picture_1: str = ""
    drive_folder_url: str = ""

class ProcessingResult(BaseModel):
    """Model for processing result"""
    row_index: int
    reference: str
    status: str  # success, failed, skipped
    picture_url: Optional[str] = None
    drive_folder: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 1
    updated_cells: int = 0

def extract_drive_folder_id(url: str) -> Optional[str]:
    """Extract folder ID from Google Drive URL"""
    if not url:
        return None
    
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            folder_id = match.group(1)
            if Config.VERBOSE_LOGGING:
                logging.debug(f"Extracted folder ID: {folder_id}")
            return folder_id
    
    logging.warning(f"Could not extract folder ID from URL: {url}")
    return None

def get_google_sheets_client():
    """
    Initialize and return Google Sheets client using OAuth credentials.
    Uses existing token.json and credentials.json files.
    """
    try:
        if not hasattr(get_google_sheets_client, '_client'):
            token_file = Path("token.json")
            
            if not token_file.exists():
                raise FileNotFoundError(
                    "token.json not found. Please run the scraper first to generate OAuth token."
                )
            
            # Load token data
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            # Create credentials from token
            creds = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes', Config.GOOGLE_SCOPES)
            )
            
            # Refresh token if expired
            if creds.expired and creds.refresh_token:
                logging.info("Refreshing expired OAuth token...")
                creds.refresh(Request())
                
                # Save refreshed token
                token_data['token'] = creds.token
                if creds.expiry:
                    token_data['expiry'] = creds.expiry.isoformat()
                
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                logging.info("✓ Token refreshed successfully")
            
            # Authorize gspread client
            get_google_sheets_client._client = gspread.authorize(creds)
            logging.info("✓ Google Sheets client authenticated with OAuth")
        
        return get_google_sheets_client._client
    
    except FileNotFoundError as e:
        logging.error(f"OAuth token file not found: {e}")
        logging.error("Please run the scraper once manually to generate token.json")
        raise
    except Exception as e:
        logging.error(f"Failed to authenticate with Google Sheets: {e}")
        raise

def get_cell_value(row: List, index: int) -> str:
    """Safely get cell value from row"""
    if index >= len(row):
        return ""
    return str(row[index]).strip()

def parse_row(row: List, row_index: int) -> Optional[SheetRow]:
    """Parse spreadsheet row into SheetRow model"""
    try:
        return SheetRow(
            row_index=row_index,
            lead_source=get_cell_value(row, Config.COL_LEAD_SOURCE),
            reference_number=get_cell_value(row, Config.COL_REFERENCE),
            type_propriete=get_cell_value(row, Config.COL_TYPE_PROPRIETE),
            price=float(get_cell_value(row, Config.COL_PRICE) or 0),
            cadastral_lot=get_cell_value(row, Config.COL_CADASTRAL),
            street_number=get_cell_value(row, Config.COL_STREET_NUM),
            street=get_cell_value(row, Config.COL_STREET),
            city=get_cell_value(row, Config.COL_CITY),
            postal_code=get_cell_value(row, Config.COL_POSTAL_CODE),
            other_unit=get_cell_value(row, Config.COL_OTHER_UNIT),
            mailing_unit=get_cell_value(row, Config.COL_MAILING_UNIT),
            immocalcul_status=get_cell_value(row, Config.COL_IMMOCALCUL),
            analyse_risque=get_cell_value(row, Config.COL_ANALYSE_RISQUE),
            picture_1=get_cell_value(row, Config.COL_PICTURE_1),
            drive_folder_url=get_cell_value(row, Config.COL_DRIVE_FOLDER)
        )
    except Exception as e:
        if Config.VERBOSE_LOGGING:
            logging.error(f"Failed to parse row {row_index}: {e}")
        return None

def get_rows_to_process(worksheet) -> List[SheetRow]:
    """Get all eligible rows from sheet (Drive URL present, Picture 1 empty)"""
    try:
        all_values = worksheet.get_all_values()
        
        if not all_values:
            logging.warning("No data found in worksheet")
            return []
        
        rows_to_process = []
        
        # Skip header row (index 0), start from row 2 (index 1)
        for i, row in enumerate(all_values[1:], start=2):
            sheet_row = parse_row(row, i)
            
            if sheet_row:
                # Filter: drive_folder_url present AND picture_1 is empty
                if sheet_row.immocalcul_status:
                    logging.info(
                        f"Row {i} skipped - Immocalcul already set ({sheet_row.immocalcul_status})"
                    )
                    continue

                if sheet_row.drive_folder_url and not sheet_row.picture_1:
                    rows_to_process.append(sheet_row)
                    
                    if Config.VERBOSE_LOGGING:
                        logging.info(
                            f"Row {i} queued - "
                            f"Ref: {sheet_row.reference_number}, "
                            f"Lot: {sheet_row.cadastral_lot}, "
                            f"Address: {sheet_row.street_number} {sheet_row.street}, {sheet_row.city}"
                        )
        
        logging.info(f"✓ Found {len(rows_to_process)} eligible rows to process")
        return rows_to_process
    
    except Exception as e:
        logging.error(f"Failed to read rows from sheet: {e}")
        raise

def update_single_cell(worksheet, row_idx: int, col_idx: int, value: str) -> bool:
    """
    Update a single cell in the Google Sheet immediately.
    Returns True if successful, False otherwise.
    """
    try:
        col_letter = Config._col_to_letter(col_idx)
        value_preview = str(value)[:60] if value else ""
        logging.info(f"   📝 Updating {col_letter}{row_idx} = {value_preview}...")
        
        # gspread uses 1-based indexing for columns
        worksheet.update_cell(row_idx, col_idx + 1, value)
        
        if Config.VERBOSE_LOGGING:
            logging.info(f"   ✅ Cell {col_letter}{row_idx} updated successfully!")
        return True
    except Exception as e:
        logging.error(f"   ❌ Failed to update cell {col_letter}{row_idx}: {e}")
        return False

def extract_updates_from_summary(summary: dict) -> Dict[int, any]:
    """
    Extract all update values from scraper summary JSON.
    Matches the logic from your JavaScript code.
    Uses risk_issues field for risk analysis.
    
    Args:
        summary: The parsed JSON summary from scraper
        
    Returns:
        Dictionary mapping column indices to values
    """
    updates = {}
    
    # Type Propriete (Column G - index 6)
    if summary.get('classification'):
        updates[Config.COL_TYPE_PROPRIETE] = summary['classification']
    
    # Price (Column H - index 7) - sum amounts array or use Price field
    if summary.get('amounts') and isinstance(summary['amounts'], list):
        total_price = sum(summary['amounts'])
        updates[Config.COL_PRICE] = total_price
    elif summary.get('Price'):
        updates[Config.COL_PRICE] = summary['Price']
    
    # Analyse risque (Column BA - index 52) - ALWAYS use risk_issues array
    # This is the normalized list from the scraper with mapped values
    if summary.get('risk_issues') and isinstance(summary['risk_issues'], list):
        # Filter out empty values and join with comma
        risk_items = [str(x).strip() for x in summary['risk_issues'] if x]
        if risk_items:
            risk_text = ", ".join(risk_items)
            updates[Config.COL_ANALYSE_RISQUE] = risk_text
            logging.info(f"   ✓ Risk analysis: {risk_text}")
    
    # Picture 1 (Column BB - index 53)
    if summary.get('Picture 1'):
        updates[Config.COL_PICTURE_1] = summary['Picture 1']
    elif summary.get('main_photo'):
        updates[Config.COL_PICTURE_1] = summary['main_photo']
    
    # Google Drive (Column BC - index 54)
    if summary.get('Google Drive'):
        updates[Config.COL_DRIVE_FOLDER] = summary['Google Drive']
    
    # Other Street Number (Column AK - index 36)
    if summary.get('Other Street Number'):
        updates[Config.COL_STREET_NUM] = summary['Other Street Number']
    
    # Other Street (Column AL - index 37)
    if summary.get('Other Street'):
        updates[Config.COL_STREET] = summary['Other Street']
    
    # Other City (Column AM - index 38)
    if summary.get('Other City'):
        updates[Config.COL_CITY] = summary['Other City']
    
    # Other Zip (Column AN - index 39)
    if summary.get('Other Zip'):
        updates[Config.COL_POSTAL_CODE] = summary['Other Zip']
    
    # Other State (Column AO - index 40) - hardcoded to Quebec in scraper
    if summary.get('Other State'):
        updates[Config.COL_STATE] = summary['Other State']
    
    # Other Country (Column AP - index 41) - hardcoded to Canada in scraper
    if summary.get('Other Country'):
        updates[Config.COL_COUNTRY] = summary['Other Country']
    
    # Other Unit (Column AJ - index 35)
    if summary.get('Other Unit'):
        updates[Config.COL_OTHER_UNIT] = summary['Other Unit']
    
    return updates

def update_multiple_cells(worksheet, row_idx: int, updates: Dict[int, any]) -> int:
    """
    Update multiple cells in a row.
    
    Args:
        worksheet: The worksheet object
        row_idx: Row index (1-based for display, but we handle internally)
        updates: Dict mapping column indices to values
        
    Returns:
        Number of successfully updated cells
    """
    updated_count = 0
    
    for col_idx, value in updates.items():
        # Convert value to string, handling None
        str_value = str(value) if value is not None else ""
        
        # Skip completely empty values (but allow "0" or "Canada")
        if str_value == "":
            continue
        
        # Update the cell
        if update_single_cell(worksheet, row_idx, col_idx, str_value):
            updated_count += 1
        else:
            # Log failure but continue with other updates
            col_letter = Config._col_to_letter(col_idx)
            logging.warning(f"   ⚠️ Failed to update {col_letter}{row_idx}, continuing...")
    
    return updated_count

def cleanup_run_artifacts(summary_path: Path) -> None:
    """Remove scraper output directory after processing is complete."""
    if not summary_path:
        return

    try:
        out_dir = summary_path.parent
        run_steps_dir = Path("run_steps").resolve()
        out_dir_resolved = out_dir.resolve()

        if not str(out_dir_resolved).startswith(str(run_steps_dir) + os.sep):
            logging.warning(f"Skipping cleanup for unexpected path: {out_dir_resolved}")
            return

        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
            logging.info(f"   🧹 Cleaned up artifacts in {out_dir}")
    except Exception as e:
        logging.warning(f"   ⚠️ Cleanup failed for {summary_path}: {e}")

async def run_scraper_async(row: SheetRow, worksheet, attempt: int = 1) -> ProcessingResult:
    """
    Run scraper asynchronously for a single row.
    Updates the Google Sheet immediately upon completion with ALL fields.
    """
    try:
        if row.other_unit or row.mailing_unit:
            unit_value = row.other_unit or row.mailing_unit
            logging.info(
                f"   ⏭️ Skipping row {row.row_index} (Ref: {row.reference_number}) - Unit present: {unit_value}"
            )
            updates = {Config.COL_IMMOCALCUL: 2}
            updated_count = update_multiple_cells(worksheet, row.row_index, updates)
            return ProcessingResult(
                row_index=row.row_index,
                reference=row.reference_number,
                status="skipped",
                attempts=attempt,
                updated_cells=updated_count
            )

        if Config.VERBOSE_LOGGING:
            logging.info(
                f"[Attempt {attempt}] Starting scraper for row {row.row_index} "
                f"- Ref: {row.reference_number}"
            )
        else:
            logging.info(f"🔄 Processing row {row.row_index} (Ref: {row.reference_number})")
        
        # Generate unique run ID for this scraper execution
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        run_id = f"{timestamp}_row{row.row_index}_ref{row.reference_number or 'none'}_attempt{attempt}"
        
        logging.info(f"   🆔 Run ID: {run_id}")
        
        # Build scraper command
        cmd = ["python3", Config.SCRAPER_SCRIPT]
        cmd.extend(["--run-id", run_id])
        
        # Address/Lot selection
        if row.cadastral_lot:
            cmd.extend(["--lot", row.cadastral_lot])
            logging.info(f"   Using cadastral lot: {row.cadastral_lot}")
        elif row.street_number and row.street and row.city:
            cmd.extend([
                "--address-number", row.street_number,
                "--address-street", row.street,
                "--address-city", row.city
            ])
            logging.info(f"   Using address: {row.street_number} {row.street}, {row.city}")
        else:
            raise ValueError("Missing required fields (lot or full address)")
        
        # Add credentials
        if Config.IMMOCALCUL_EMAIL:
            cmd.extend(["--email", Config.IMMOCALCUL_EMAIL])
        if Config.IMMOCALCUL_PASSWORD:
            cmd.extend(["--password", Config.IMMOCALCUL_PASSWORD])
        
        # Determine which Drive folder to use
        if Config.USE_EXISTING_DRIVE_URL and row.drive_folder_url:
            drive_folder_id = extract_drive_folder_id(row.drive_folder_url)
            if drive_folder_id:
                cmd.extend(["--parent-folder-id", "11LA7oGwYLDcOVqmDCco_wWVDjMrlYjmSy"])
                cmd.extend(["--sub-folder-id", drive_folder_id])
                logging.info(f"   ✓ Using existing Drive subfolder: {drive_folder_id}")
            else:
                logging.warning(f"   ⚠ Could not extract folder ID, using default")
                if Config.PARENT_DRIVE_FOLDER_ID:
                    cmd.extend(["--parent-folder-id", Config.PARENT_DRIVE_FOLDER_ID])
        elif Config.PARENT_DRIVE_FOLDER_ID:
            cmd.extend(["--parent-folder-id", Config.PARENT_DRIVE_FOLDER_ID])
            logging.info(f"   Using parent folder (will create subfolder)")
        
        # Add delay settings
        cmd.extend([
            "--delay-min", str(Config.RANDOM_DELAY_MIN),
            "--delay-max", str(Config.RANDOM_DELAY_MAX)
        ])
        
        # Add headless setting
        if Config.HEADLESS:
            cmd.append("--headless")
        
        # Run scraper subprocess
        logging.info(f"   🚀 Launching scraper subprocess for row {row.row_index}...")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=Config.SCRAPER_TIMEOUT
            )
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"Scraper timeout after {Config.SCRAPER_TIMEOUT}s")
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            if Config.VERBOSE_LOGGING:
                logging.error(f"Scraper stderr: {error_msg}")
            raise RuntimeError(f"Scraper failed with return code {process.returncode}")
        
        # Parse summary file path
        summary_path_str = stdout.decode().strip()
        if not summary_path_str:
            raise RuntimeError("Scraper did not return summary path")
        
        summary_path_lines = summary_path_str.strip().split('\n')
        summary_path_str = summary_path_lines[-1].strip()
        summary_path = Path(summary_path_str)
        
        if not summary_path.exists():
            raise RuntimeError(f"Summary file not found: {summary_path}")
        
        # Load summary
        logging.info(f"   📄 Reading summary from: {summary_path.name}")
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        # Extract all updates from summary (including normalized risk_issues)
        updates = extract_updates_from_summary(summary)
        updates[Config.COL_IMMOCALCUL] = 1
        
        # Try to extract Picture 1 from uploaded_files if not in updates
        if Config.COL_PICTURE_1 not in updates and 'uploaded_files' in summary:
            uploaded = summary.get('uploaded_files', {})
            if 'main_photo' in uploaded:
                photo_info = uploaded['main_photo']
                if isinstance(photo_info, dict) and 'id' in photo_info:
                    updates[Config.COL_PICTURE_1] = f"https://drive.google.com/uc?id={photo_info['id']}"
                    logging.info(f"   ✓ Extracted Picture 1 from uploaded_files")
        
        # Log what we're about to update
        logging.info(f"   📊 Found {len(updates)} fields to update:")
        for col_idx, value in updates.items():
            col_letter = Config._col_to_letter(col_idx)
            value_str = str(value)[:50]
            logging.info(f"      • {col_letter} ({col_idx}): {value_str}")
        
        # ⭐ UPDATE ALL CELLS IN SHEET IMMEDIATELY ⭐
        logging.info(f"   🔄 Updating Google Sheet with all fields...")
        updated_count = update_multiple_cells(worksheet, row.row_index, updates)
        
        logging.info(f"   ✅ Successfully updated {updated_count}/{len(updates)} cells in sheet")
        cleanup_run_artifacts(summary_path)
        logging.info(f"✅ Row {row.row_index} completed successfully")
        
        return ProcessingResult(
            row_index=row.row_index,
            reference=row.reference_number,
            status="success",
            picture_url=updates.get(Config.COL_PICTURE_1),
            drive_folder=updates.get(Config.COL_DRIVE_FOLDER),
            attempts=attempt,
            updated_cells=updated_count
        )
    
    except Exception as e:
        error_msg = str(e)
        logging.error(f"❌ Row {row.row_index} [Attempt {attempt}] failed: {error_msg[:200]}")
        
        return ProcessingResult(
            row_index=row.row_index,
            reference=row.reference_number,
            status="failed",
            error=error_msg,
            attempts=attempt,
            updated_cells=0
        )

async def process_row_with_retry(row: SheetRow, worksheet, semaphore: asyncio.Semaphore, row_number: int, total_rows: int) -> ProcessingResult:
    """Process a row with retry logic and concurrency control"""
    async with semaphore:
        logging.info(f"\n{'='*60}")
        logging.info(f"Processing Row {row_number}/{total_rows}")
        logging.info(f"Sheet Row Index: {row.row_index}")
        logging.info(f"Reference: {row.reference_number}")
        if row.cadastral_lot:
            logging.info(f"Lot: {row.cadastral_lot}")
        elif row.street_number or row.street or row.city:
            logging.info(f"Address: {row.street_number} {row.street}, {row.city}")
        logging.info(f"{'='*60}")
        
        for attempt in range(1, Config.MAX_RETRIES_PER_ROW + 1):
            result = await run_scraper_async(row, worksheet, attempt)
            
            if result.status in ("success", "skipped"):
                return result
            
            if attempt < Config.MAX_RETRIES_PER_ROW:
                logging.info(
                    f"⟳ Row {row.row_index}: Retrying in {Config.RETRY_DELAY}s "
                    f"(attempt {attempt + 1}/{Config.MAX_RETRIES_PER_ROW})"
                )
                await asyncio.sleep(Config.RETRY_DELAY)
        
        if result.status == "failed":
            updated_count = update_multiple_cells(
                worksheet,
                row.row_index,
                {Config.COL_IMMOCALCUL: 0}
            )
            result.updated_cells = updated_count
            if result.error:
                match = re.search(r"Summary file not found: (.+)$", result.error)
                if match:
                    try:
                        cleanup_run_artifacts(Path(match.group(1).strip()))
                    except Exception:
                        pass

        return result

async def process_all_sheet_rows(job_id: str):
    """
    Main async function to process all eligible rows from Google Sheet.
    Updates the sheet immediately after each row is processed with ALL fields.
    """

    start_time = datetime.utcnow()

    # --- EARLY DEBUG PRINTS (before logging setup) ---
    print("[EARLY-DEBUG] Entered process_all_sheet_rows")
    print(f"[EARLY-DEBUG] Job ID: {job_id}")
    try:
        print("[EARLY-DEBUG] About to validate config...")
        print(f"[EARLY-DEBUG] SPREADSHEET_ID: {Config.SPREADSHEET_ID}")
        print(f"[EARLY-DEBUG] WORKSHEET_GID: {Config.WORKSHEET_GID}")
        print(f"[EARLY-DEBUG] GOOGLE_CREDENTIALS_FILE exists: {Config.GOOGLE_CREDENTIALS_FILE.exists()}")
        print(f"[EARLY-DEBUG] token.json exists: {Path('token.json').exists()}")

        # Validate configuration
        if not Config.validate():
            print("[EARLY-DEBUG] Config validation failed!")
            raise RuntimeError("Configuration validation failed. Check logs.")

        print("[EARLY-DEBUG] Config validated. Authenticating with Google Sheets...")
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(Config.SPREADSHEET_ID)

        # Get the worksheet
        worksheet = None
        for ws in spreadsheet.worksheets():
            print(f"[EARLY-DEBUG] Worksheet candidate: id={ws.id}, title={ws.title}")
            if str(ws.id) == Config.WORKSHEET_GID:
                worksheet = ws
                break

        if not worksheet:
            worksheet = spreadsheet.get_worksheet(0)
            print(f"[EARLY-DEBUG] Defaulted to first worksheet: id={worksheet.id}, title={worksheet.title}")
        else:
            print(f"[EARLY-DEBUG] Selected worksheet: id={worksheet.id}, title={worksheet.title}")

        all_values = worksheet.get_all_values()
        print(f"[EARLY-DEBUG] Sheet has {len(all_values)} rows (including header)")
        if all_values:
            print(f"[EARLY-DEBUG] Sheet header: {all_values[0]}")
            for i, row in enumerate(all_values[1:4], start=2):
                print(f"[EARLY-DEBUG] Row {i}: {row}")
        else:
            print("[EARLY-DEBUG] No data found in worksheet (all_values is empty)")

        # --- END EARLY DEBUG PRINTS ---

        run_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        run_log_path = add_run_log_handler(run_label)
        logging.info(f"Run log: {run_log_path}")
        logging.info("STARTED SHEET PROCESSOR - Entered process_all_sheet_rows")
        set_step("start")
        logging.info(f"{'='*60}")
        logging.info(f"Job {job_id}: Starting batch processing")
        logging.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logging.info(f"{'='*60}")

        Config.log_config()

        # Get rows to process
        rows_to_process = get_rows_to_process(worksheet)
        
        if not rows_to_process:
            logging.info(f"ℹ Job {job_id}: No eligible rows found")
            set_step("done")
            return
        
        # Process rows with controlled concurrency
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_SCRAPERS)
        
        logging.info(f"{'='*60}")
        logging.info(f"Processing {len(rows_to_process)} rows")
        logging.info(f"Concurrency: {Config.MAX_CONCURRENT_SCRAPERS} rows at a time")
        logging.info(f"Sheet updates: IMMEDIATE (all fields after each row completes)")
        logging.info(f"{'='*60}")
        
        # Create tasks
        tasks = [
            process_row_with_retry(row, worksheet, semaphore, idx + 1, len(rows_to_process))
            for idx, row in enumerate(rows_to_process)
        ]
        
        # Process all rows concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate statistics
        successful = 0
        failed = 0
        skipped = 0
        total_cells_updated = 0
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Unexpected error: {result}")
                failed += 1
            elif result.status == "success":
                successful += 1
                total_cells_updated += result.updated_cells
            elif result.status == "skipped":
                skipped += 1
            else:
                failed += 1
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Log final summary
        set_step("done")
        logging.info(f"\n{'='*60}")
        logging.info(f"Job {job_id}: BATCH PROCESSING COMPLETED")
        logging.info(f"{'='*60}")
        logging.info(f"  Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logging.info(f"  Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logging.info(f"  Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logging.info(f"  Total rows: {len(rows_to_process)}")
        logging.info(f"  ✅ Successful: {successful}")
        logging.info(f"  ⏭️ Skipped: {skipped}")
        logging.info(f"  ❌ Failed: {failed}")
        logging.info(f"  📝 Total cells updated: {total_cells_updated}")
        
        if successful > 0:
            avg_time = duration / len(rows_to_process)
            avg_cells = total_cells_updated / successful
            logging.info(f"  ⏱  Avg time/row: {avg_time:.1f}s")
            logging.info(f"  📊 Avg cells/row: {avg_cells:.1f}")
        
        logging.info(f"{'='*60}\n")
    
    except Exception as e:
        import traceback
        set_step("error")
        error_message = f"Batch processing failed: {e}\n{traceback.format_exc()}"
        logging.error(f"Job {job_id}: {error_message}")
        raise


if __name__ == "__main__":
    import sys
    job_id = sys.argv[1] if len(sys.argv) > 1 else "manual-test"
    import asyncio
    asyncio.run(process_all_sheet_rows(job_id))