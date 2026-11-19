"""Promo routes. Includes the catch-all /{token} route, so this router must be registered LAST."""
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config import BASE_STATIC_DIR, PROMO_IMAGE_MAPPING

router = APIRouter()

# --- Modified API Endpoint for Promotional Items ---
@router.get("/{token}", response_class=HTMLResponse)
async def get_promotional_page_with_hero(request: Request, token: str):
    """
    Sets a session variable with the promo token and redirects to the homepage.
    The homepage's JavaScript will then pick up this token and display the promo hero.
    """
    lookup_token = token.lower()
    relative_image_path = PROMO_IMAGE_MAPPING.get(lookup_token)

    if not relative_image_path:
        relative_image_path = PROMO_IMAGE_MAPPING.get("default")
        if not relative_image_path:
            raise HTTPException(status_code=404, detail="Promotional image not found and no default image available in mapping.")

    full_filesystem_path = os.path.join(BASE_STATIC_DIR, relative_image_path)
    if not os.path.exists(full_filesystem_path):
        if token != "default":
            default_relative_path = PROMO_IMAGE_MAPPING.get("default")
            if default_relative_path and os.path.exists(os.path.join(BASE_STATIC_DIR, default_relative_path)):
                relative_image_path = default_relative_path
            else:
                raise HTTPException(status_code=404, detail=f"Image for token '{token}' not found and default image file is also missing.")
        else:
            raise HTTPException(status_code=404, detail="Default promotional image file not found.")

    # Store the actual static URL of the image in the session
    promo_image_url = f"/static/{relative_image_path}"
    request.session["promo_image_url"] = promo_image_url
    request.session["promo_title"] = f"Working together to serve our communities!" # Example title

    # Redirect to the homepage
    return RedirectResponse(url="/pages/homepage.html")

# --- API to get promo info (called by JavaScript) ---
@router.get("/promo/get_promo_info/")
async def get_promo_info(request: Request):
    promo_info = {
        "promo_image_url": request.session.pop("promo_image_url", None), # Pop to clear after use
        "promo_title": request.session.pop("promo_title", None),
    }
    # Clear the session variables after they are fetched
    return JSONResponse(content=promo_info)