"""
Configuration management for ImmoCalcul Sheet Processor
Centralizes all settings and validates environment variables
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    """Application configuration"""
    
    # API Settings
    API_KEY: str = os.getenv("API_KEY", "devapikey")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Google Sheets Settings
    SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "10izV_Hjs8rjbJxDjvzTnU_7afnt2ZhK4HRRA81Hq8is")
    WORKSHEET_GID: str = os.getenv("WORKSHEET_GID", "1850964650")
    
    # OAuth credentials files
    GOOGLE_CREDENTIALS_FILE: Path = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
    
    # Google Drive Settings
    PARENT_DRIVE_FOLDER_ID: Optional[str] = os.getenv("PARENT_DRIVE_FOLDER_ID")
    USE_EXISTING_DRIVE_URL: bool = os.getenv("USE_EXISTING_DRIVE_URL", "True").lower() in ('true', '1', 'yes')
    
    # ImmoCalcul Credentials
    IMMOCALCUL_EMAIL: Optional[str] = os.getenv("IMMOCALCUL_EMAIL")
    IMMOCALCUL_PASSWORD: Optional[str] = os.getenv("IMMOCALCUL_PASSWORD")
    
    # Scraper Settings
    SCRAPER_SCRIPT: str = os.getenv("SCRAPER_SCRIPT", "full_step_scraper.py")
    SCRAPER_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "900"))  # 15 minutes
    MAX_CONCURRENT_SCRAPERS: int = int(os.getenv("MAX_CONCURRENT_SCRAPERS", "3"))
    HEADLESS: bool = os.getenv("HEADLESS", "False").lower() in ('true', '1', 'yes')
    CLASSIFICATION_STYLE: str = os.getenv("CLASSIFICATION_STYLE", "spec")
    
    # Delay Settings
    RANDOM_DELAY_MIN: float = float(os.getenv("RANDOM_DELAY_MIN", "3"))
    RANDOM_DELAY_MAX: float = float(os.getenv("RANDOM_DELAY_MAX", "6"))
    
    # Column Indices (0-based) - Based on your exact column order
    # Reference: https://docs.google.com/spreadsheets/d/10izV_Hjs8rjbJxDjvzTnU_7afnt2ZhK4HRRA81Hq8is
    
    # Column mapping (0-based index):
    # 0: Scripte
    # 1: Contact Id
    # 2: Scores
    # 3: Type
    # 4: Lead Source
    # 5: Reference Number
    # 6: Type Propriete
    # 7: Price
    # 8: Verification
    # 9: Numero lot (Cadastral)
    # 10: Contact Owner.id
    # 11: Contact Owner
    # 12: First Name
    # 13: Last Name
    # 14: Email
    # 15: Date of Birth
    # 16: Company Name.id
    # 17: Company Name
    # 18: Mobile
    # 19: Phone
    # 20: Other Phone
    # 21: Home Phone
    # 22: Email Opt Out
    # 23: Tag
    # 24: Description
    # 25: Created By.id
    # 26: Created By
    # 27: Modified By.id
    # 28: Modified By
    # 29: Created Time
    # 30: Modified Time
    # 31: Contact Name
    # 32: Last Activity Time
    # 33: Unsubscribed Mode
    # 34: Unsubscribed Time
    # 35: Other Unit
    # 36: Other Street Number
    # 37: Other Street
    # 38: Other City
    # 39: Other Zip
    # 40: Other State
    # 41: Other Country
    # 42: Mailing Unit
    # 43: Mailing Street Number
    # 44: Mailing Street
    # 45: Mailing City
    # 46: Mailing Zip
    # 47: Mailing State
    # 48: Mailing Country
    # 49: Source motivation
    # 50: Equity
    # 51: Mortgage
    # 52: Analyse risque
    # 53: Picture 1
    # 54: Google Drive
    # 55: Direct Mail Date
    # 56: Direct Mail Number
    # 57: Visite
    # 58: Date Visite
    # 59: Call
    # 60: Date Call
    # 61: Reponse
    
    COL_SCRIPTE: int = 0                # Column A - "SC-Google Drive", "SC-ImmoCalcul", etc.
    COL_CONTACT_ID: int = 1             # Column B
    COL_SCORES: int = 2                 # Column C
    COL_TYPE: int = 3                   # Column D
    COL_LEAD_SOURCE: int = 4            # Column E - Lead Source
    COL_REFERENCE: int = 5              # Column F - Reference Number
    COL_TYPE_PROPRIETE: int = 6         # Column G - Type Propriete (R-House, C-Commercial, etc.)
    COL_PRICE: int = 7                  # Column H - Price
    COL_VERIFICATION: int = 8           # Column I
    COL_CADASTRAL: int = 9              # Column J - Numero lot (Cadastral)
    
    # Contact fields
    COL_CONTACT_OWNER_ID: int = 10      # Column K
    COL_CONTACT_OWNER: int = 11         # Column L
    COL_FIRST_NAME: int = 12            # Column M
    COL_LAST_NAME: int = 13             # Column N
    COL_EMAIL: int = 14                 # Column O
    COL_DATE_OF_BIRTH: int = 15         # Column P
    COL_COMPANY_NAME_ID: int = 16       # Column Q
    COL_COMPANY_NAME: int = 17          # Column R
    COL_MOBILE: int = 18                # Column S
    COL_PHONE: int = 19                 # Column T
    COL_OTHER_PHONE: int = 20           # Column U
    COL_HOME_PHONE: int = 21            # Column V
    COL_EMAIL_OPT_OUT: int = 22         # Column W
    COL_TAG: int = 23                   # Column X
    COL_DESCRIPTION: int = 24           # Column Y
    
    # Metadata fields
    COL_CREATED_BY_ID: int = 25         # Column Z
    COL_CREATED_BY: int = 26            # Column AA
    COL_MODIFIED_BY_ID: int = 27        # Column AB
    COL_MODIFIED_BY: int = 28           # Column AC
    COL_CREATED_TIME: int = 29          # Column AD
    COL_MODIFIED_TIME: int = 30         # Column AE
    COL_CONTACT_NAME: int = 31          # Column AF
    COL_LAST_ACTIVITY_TIME: int = 32    # Column AG
    COL_UNSUBSCRIBED_MODE: int = 33     # Column AH
    COL_UNSUBSCRIBED_TIME: int = 34     # Column AI
    
    # Address fields (Other)
    COL_OTHER_UNIT: int = 35            # Column AJ
    COL_STREET_NUM: int = 36            # Column AK - Other Street Number
    COL_STREET: int = 37                # Column AL - Other Street
    COL_CITY: int = 38                  # Column AM - Other City
    COL_POSTAL_CODE: int = 39           # Column AN - Other Zip
    COL_STATE: int = 40                 # Column AO - Other State
    COL_COUNTRY: int = 41               # Column AP - Other Country
    
    # Mailing address fields
    COL_MAILING_UNIT: int = 42          # Column AQ
    COL_MAILING_STREET_NUM: int = 43    # Column AR
    COL_MAILING_STREET: int = 44        # Column AS
    COL_MAILING_CITY: int = 45          # Column AT
    COL_MAILING_ZIP: int = 46           # Column AU
    COL_MAILING_STATE: int = 47         # Column AV
    COL_MAILING_COUNTRY: int = 48       # Column AW
    
    # Additional fields
    COL_SOURCE_MOTIVATION: int = 49     # Column AX
    COL_EQUITY: int = 50                # Column AY
    COL_MORTGAGE: int = 51              # Column AZ
    COL_ANALYSE_RISQUE: int = 52        # Column BA - Analyse risque
    COL_PICTURE_1: int = 53             # Column BB - Picture 1 *** IMPORTANT ***
    COL_DRIVE_FOLDER: int = 54          # Column BC - Google Drive *** IMPORTANT ***
    COL_DIRECT_MAIL_DATE: int = 55      # Column BD
    COL_DIRECT_MAIL_NUMBER: int = 56    # Column BE
    COL_VISITE: int = 57                # Column BF
    COL_DATE_VISITE: int = 58           # Column BG
    COL_CALL: int = 59                  # Column BH
    COL_DATE_CALL: int = 60             # Column BI
    COL_REPONSE: int = 61               # Column BJ
    
    # Retry Settings
    MAX_RETRIES_PER_ROW: int = int(os.getenv("MAX_RETRIES_PER_ROW", "2"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    VERBOSE_LOGGING: bool = os.getenv("VERBOSE_LOGGING", "False").lower() in ('true', '1', 'yes')
    
    # PDF Optimization
    PDF_TARGET_DPI: int = int(os.getenv("PDF_TARGET_DPI", "150"))
    PDF_JPEG_QUALITY: int = int(os.getenv("PDF_JPEG_QUALITY", "85"))
    
    # Google Sheets API Scopes
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration"""
        errors = []
        warnings = []
        
        if not cls.GOOGLE_CREDENTIALS_FILE.exists():
            errors.append(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_FILE}")
        
        if not Path("token.json").exists():
            errors.append("token.json not found. Please run the scraper once to generate OAuth token.")
        
        if not cls.IMMOCALCUL_EMAIL or not cls.IMMOCALCUL_PASSWORD:
            errors.append("IMMOCALCUL_EMAIL and IMMOCALCUL_PASSWORD must be set")
        
        if not Path(cls.SCRAPER_SCRIPT).exists():
            errors.append(f"Scraper script not found: {cls.SCRAPER_SCRIPT}")
        
        if not cls.USE_EXISTING_DRIVE_URL and not cls.PARENT_DRIVE_FOLDER_ID:
            warnings.append("PARENT_DRIVE_FOLDER_ID not set and USE_EXISTING_DRIVE_URL is False")
        
        if not cls.SPREADSHEET_ID:
            errors.append("SPREADSHEET_ID must be set")
        
        if warnings:
            for warning in warnings:
                logging.warning(warning)
        
        if errors:
            for error in errors:
                logging.error(error)
            return False
        
        return True
    
    @classmethod
    def log_config(cls):
        """Log current configuration (excluding sensitive data)"""
        logging.info("="*60)
        logging.info("ImmoCalcul Sheet Processor - Configuration")
        logging.info("="*60)
        logging.info(f"  Spreadsheet ID: {cls.SPREADSHEET_ID}")
        logging.info(f"  Worksheet GID: {cls.WORKSHEET_GID}")
        logging.info(f"  Email: {cls.IMMOCALCUL_EMAIL}")
        logging.info(f"  Scraper: {cls.SCRAPER_SCRIPT}")
        logging.info(f"  Scraper timeout: {cls.SCRAPER_TIMEOUT}s")
        logging.info(f"  Headless mode: {cls.HEADLESS}")
        logging.info(f"  Max concurrent: {cls.MAX_CONCURRENT_SCRAPERS}")
        logging.info(f"  Delays: {cls.RANDOM_DELAY_MIN}s - {cls.RANDOM_DELAY_MAX}s")
        logging.info(f"  Use existing Drive URL: {cls.USE_EXISTING_DRIVE_URL}")
        if cls.PARENT_DRIVE_FOLDER_ID:
            logging.info(f"  Parent Drive folder: {cls.PARENT_DRIVE_FOLDER_ID[:20]}...")
        else:
            logging.info(f"  Parent Drive folder: Not set")
        logging.info(f"  Column mappings:")
        logging.info(f"    - Lead Source: Column {chr(65 + cls.COL_LEAD_SOURCE)} (index {cls.COL_LEAD_SOURCE})")
        logging.info(f"    - Reference Number: Column {chr(65 + cls.COL_REFERENCE)} (index {cls.COL_REFERENCE})")
        logging.info(f"    - Cadastral Lot: Column {chr(65 + cls.COL_CADASTRAL)} (index {cls.COL_CADASTRAL})")
        logging.info(f"    - Street Number: Column {chr(65 + cls.COL_STREET_NUM)} (index {cls.COL_STREET_NUM})")
        logging.info(f"    - Street: Column {chr(65 + cls.COL_STREET)} (index {cls.COL_STREET})")
        logging.info(f"    - City: Column {chr(65 + cls.COL_CITY)} (index {cls.COL_CITY})")
        logging.info(f"    - Picture 1: Column {cls._col_to_letter(cls.COL_PICTURE_1)} (index {cls.COL_PICTURE_1})")
        logging.info(f"    - Google Drive: Column {cls._col_to_letter(cls.COL_DRIVE_FOLDER)} (index {cls.COL_DRIVE_FOLDER})")
        logging.info(f"  Verbose logging: {cls.VERBOSE_LOGGING}")
        logging.info("="*60)
    
    @staticmethod
    def _col_to_letter(col_idx: int) -> str:
        """Convert column index to Excel-style letter (0 -> A, 25 -> Z, 26 -> AA, etc.)"""
        result = ""
        col_idx += 1  # Convert to 1-based
        while col_idx > 0:
            col_idx -= 1
            result = chr(65 + (col_idx % 26)) + result
            col_idx //= 26
        return result
