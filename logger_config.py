import logging
import logging.handlers
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).resolve().parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    """
    Sets up the logging system as per the project requirements.
    - Two log files: sc-immocalcul.log and error.log
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

    # --- Main Info Logger ---
    # Handles all logs from INFO level and up
    main_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'sc-immocalcul.log',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(logging.INFO)

    # --- Error Logger ---
    # Handles only ERROR level logs
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / 'error.log',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Get the root logger and attach the handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set the lowest level to capture
    
    # Avoid adding handlers if they already exist (e.g., in interactive sessions)
    if not root_logger.handlers:
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        # Also log to console for easier debugging during development
        root_logger.addHandler(logging.StreamHandler())

    return log_context

# Initialize logging and get the context manager
log_context = setup_logging()

def set_step(step_name: str):
    """Updates the current logging step."""
    log_context['step'] = step_name