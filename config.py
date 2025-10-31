import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

class Settings:
    # Database
    DATABASE_SERVER = os.getenv("DATABASE_SERVER")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_UID = os.getenv("DATABASE_UID")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    
    SQLALCHEMY_DATABASE_URL = (
        f"mssql+pyodbc://{DATABASE_UID}:{DATABASE_PASSWORD}@"
        f"{DATABASE_SERVER}:{DATABASE_PORT}/{DATABASE_NAME}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
    )
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    RECAPTCHA_SECRET_KEY = os.getenv("SERVER_KEY_CAPTCHA")

    #Twitter API
    TWITTER_API_KEY = os.getenv("X_API_KEY")
    TWITTER_API_SECRET = os.getenv("X_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
    
    # Email
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    EMAIL_SENDER_NAME = "Homeroom Heroes"
    EMAIL_SENDER_ADDRESS = "homeroom.heroes.contact@gmail.com"
    
    # File Upload
    MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
    
    # Paths
    BASE_STATIC_DIR = "static"
    EMAIL_TEMPLATE_PATH = "static/email_template.html"
    
    # Promo
    PROMO_IMAGE_MAPPING = {
        "SeattleWolf": "images/1007TheWolf.png"
    }

settings = Settings()

# Database setup
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
