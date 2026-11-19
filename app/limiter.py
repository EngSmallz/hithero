"""Shared rate limiter. Routers import this same instance; main.py attaches it to the app."""
from slowapi import Limiter
from slowapi.util import get_remote_address

##limiter
limiter = Limiter(key_func=get_remote_address)