import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
DEFAULT_LOG_DIR = Path(__file__).resolve().parent / 'logs'
LOG_DIR = Path(os.getenv('LOG_DIR', DEFAULT_LOG_DIR)).expanduser().resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
MAIN_LOG_PATH = None

def setup_logging():
    """
    Sets up the logging system as per the project requirements.
    - Single log file with timestamp in the name (all levels)
    - Custom format: [YYYY-MM-DD HH:MM:SS] LEVEL=... step=... msg="..."
    - Log rotation: 5 files of 5MB each.
    """
    # Use a dictionary to hold step context, with a default value
    log_context = {'step': 'general'}

    # Custom formatter class to handle the 'step' field
    class ContextualFormatter(logging.Formatter):
        def format(self, record):
            # Inject the step from our context dictionary into the record
            record.step = log_context.get('step', 'general')
            return super().format(record)

    log_format = '[%(asctime)s] LEVEL=%(levelname)s step=%(step)s msg="%(message)s"'
    formatter = ContextualFormatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

    # --- Main Logger ---
    # Handles all logs from INFO level and up
    run_ts = os.getenv("LOG_RUN_ID") or datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_env = os.getenv("LOG_FILE")
    global MAIN_LOG_PATH
    MAIN_LOG_PATH = Path(log_file_env).expanduser().resolve() if log_file_env else LOG_DIR / f"sc-immocalcul-{run_ts}.log"
    main_handler = logging.handlers.RotatingFileHandler(
        MAIN_LOG_PATH,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(logging.INFO)

    # Get the root logger and attach the handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set the lowest level to capture
    
    # Avoid adding handlers if they already exist (e.g., in interactive sessions)
    if not root_logger.handlers:
        root_logger.addHandler(main_handler)
        # Also log to console for easier debugging during development
        root_logger.addHandler(logging.StreamHandler())

    return log_context

# Initialize logging and get the context manager
log_context = setup_logging()

def set_step(step_name: str):
    """Updates the current logging step."""
    log_context['step'] = step_name

def add_run_log_handler(run_label: str) -> Path:
    """Return the current main log path (no extra per-run handler)."""
    if MAIN_LOG_PATH:
        return MAIN_LOG_PATH
    fallback_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"sc-immocalcul-{fallback_ts}.log"