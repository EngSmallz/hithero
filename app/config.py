"""Central configuration: environment variables and constants shared across the app."""
import os
from dotenv import load_dotenv

# Must run before any os.getenv() call below
load_dotenv()

RECAPTCHA_SECRET_KEY=os.getenv("SERVER_KEY_CAPTCHA")

###content cleanup and formatting for forum
ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p", "br"]
ALLOWED_ATTRS = {"a": ["href"]}

BASE_STATIC_DIR = "static"

ADS_TXT_PATH = f"{BASE_STATIC_DIR}/ads.txt"
SITEMAP_XML_PATH = f"{BASE_STATIC_DIR}/sitemap.xml"

# --- Configuration for Promotional Images Mapping ---
PROMO_IMAGE_MAPPING = {
    "seattlewolf": "images/partners/1007TheWolf.png",
    "livefree": "images/partners/965CountryColor.png",
    "basecamp": "images/partners/BaseCamp.png",
    "coastal": "images/partners/Coastal.png"
}

###cronjob ip white list
CRONJOB_ALLOWED_IPS = {
    "116.203.129.16",
    "116.203.134.67",
    "23.88.105.37",
    "128.140.8.200",
    "91.99.23.109",
}

# Load environment variables
DATABASE_SERVER = os.getenv("DATABASE_SERVER")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_UID = os.getenv("DATABASE_UID")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

# Construct SQLAlchemy database URL
SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc://{DATABASE_UID}:{DATABASE_PASSWORD}@{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_NAME}?driver=ODBC+Driver+18+for+SQL+Server"

# Maximum allowed file size in bytes (e.g., 1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024