from passlib.hash import sha256_crypt
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