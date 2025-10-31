from passlib.hash import sha256_crypt
from config import settings
import requests
import secrets
import string

def hash_password(password: str) -> str:
    return sha256_crypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return sha256_crypt.verify(password, hashed)

def generate_temp_password(length: int = 10) -> str:
    return ''.join(
        secrets.choice(string.ascii_letters + string.digits) 
        for _ in range(length)
    )

def verify_recaptcha(recaptcha_response: str) -> bool:
        """Verify reCAPTCHA response"""
        url = "https://www.google.com/recaptcha/api/siteverify"
        params = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response
        }
        response = requests.post(url, params=params)
        data = response.json()
        return data.get("success", False)