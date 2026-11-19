"""Application entry point: creates the app, adds middleware, mounts static files,
registers the error pages, and plugs in every router."""
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# config must be imported first: it runs load_dotenv() before SECRET_KEY is read below
from app import config
from app.limiter import limiter
from app import models  # makes sure every table is defined (and created) at startup
from app.routers import site, internal, auth, validation, teachers, locations, forum, admin, promo

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"), https_only=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.helpteachers.net", "https://helpteachers.net"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Disable documentation routes
app.openapi_url = None
app.redoc_url = None

# Determine the path to the directory
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Custom 404 error handler
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "404.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=404)

# Custom 403 error handler
@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "403.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=403)

# Router order matters: promo holds the catch-all /{token} route, so it MUST stay last.
# (site holds /ads.txt and /sitemap.xml, which the catch-all would otherwise swallow.)
app.include_router(site.router)
app.include_router(internal.router)
app.include_router(auth.router)
app.include_router(validation.router)
app.include_router(teachers.router)
app.include_router(locations.router)
app.include_router(forum.router)
app.include_router(admin.router)
app.include_router(promo.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)