from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from config import settings, Base, engine
from controllers import auth_controller, teacher_controller, location_controller
# Import other controllers as needed

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Add middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Disable documentation routes
app.openapi_url = None
app.redoc_url = None

# Mount static files
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_controller.router)
app.include_router(teacher_controller.router)
app.include_router(location_controller.router)
# Include other routers here

# Homepage
@app.get("/")
def read_root():
    return RedirectResponse("/pages/homepage.html")

# Error handlers
@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "404.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=404)

@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    with open(os.path.join("pages/", "403.html"), "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content, status_code=403)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)