import base64
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy import String, cast, select


PUBLIC_PAGE_ALIASES = {
    "/": "homepage.html",
    "/home": "homepage.html",
    "/about": "about.html",
    "/contact": "contact.html",
    "/partners": "partners.html",
    "/register": "register.html",
    "/login": "login.html",
    "/forgot": "forgot.html",
    "/update-password": "update_password.html",
    "/reset-password": "reset_password.html",
    "/wishlist-setup": "wishlist_setup.html",
    "/terms": "terms_conditions.html",
    "/teachers": "index.html",
    "/403": "403.html",
    "/404": "404.html",
}

PRIVATE_PAGE_ALIASES = {
    "/forum": "forum.html",
    "/forum/new": "create_post.html",
    "/forum/post": "post.html",
    "/teacher": "teacher.html",
    "/validation": "validation.html",
    "/admin": "admin.html",
    "/profile/create": "create.html",
    "/profile/edit": "edit_teacher.html",
}

LEGACY_PUBLIC_PAGE_REDIRECTS = {
    "/pages/homepage.html": "/",
    "/pages/index.html": "/teachers",
    "/pages/about.html": "/about",
    "/pages/contact.html": "/contact",
    "/pages/partners.html": "/partners",
    "/pages/register.html": "/register",
    "/pages/login.html": "/login",
    "/pages/forgot.html": "/forgot",
    "/pages/terms_conditions.html": "/terms",
    "/pages/wishlist_setup.html": "/wishlist-setup",
    "/pages/403.html": "/403",
    "/pages/404.html": "/404",
}

PROMO_IMAGE_MAPPING = {
    "seattlewolf": "images/partners/1007TheWolf.png",
    "livefree": "images/partners/965CountryColor.png",
    "basecamp": "images/partners/BaseCamp.png",
    "coastal": "images/partners/Coastal.png",
}

PAGE_ROUTE_METHODS = ["GET", "HEAD"]


def serve_page(pages_dir, page_name: str, status_code: int = 200):
    return FileResponse(
        os.path.join(pages_dir, page_name),
        status_code=status_code,
    )


def create_legacy_router(
    *,
    session_factory,
    teacher_model,
    spotlight_model,
    set_teacher_session,
    logger,
    pages_dir="pages",
    static_dir="static",
):
    router = APIRouter()

    @router.get("/ads.txt", include_in_schema=False)
    async def get_ads_txt():
        return FileResponse(
            os.path.join(static_dir, "ads.txt"),
            media_type="text/plain",
        )

    @router.get("/sitemap.xml", include_in_schema=False)
    async def get_sitemap_xml():
        return FileResponse(
            os.path.join(static_dir, "sitemap.xml"),
            media_type="application/xml",
        )

    for route_path, page_name in PUBLIC_PAGE_ALIASES.items():
        async def public_page_alias(
            _request: Request,
            page_name: str = page_name,
        ):
            return serve_page(pages_dir, page_name)

        router.add_api_route(
            route_path,
            public_page_alias,
            methods=PAGE_ROUTE_METHODS,
            include_in_schema=False,
        )

    for route_path, page_name in PRIVATE_PAGE_ALIASES.items():
        async def private_page_alias(
            _request: Request,
            page_name: str = page_name,
        ):
            return serve_page(pages_dir, page_name)

        router.add_api_route(
            route_path,
            private_page_alias,
            methods=PAGE_ROUTE_METHODS,
            include_in_schema=False,
        )

    for legacy_path, clean_path in LEGACY_PUBLIC_PAGE_REDIRECTS.items():
        async def legacy_public_page_redirect(
            request: Request,
            clean_path: str = clean_path,
        ):
            query = request.url.query
            destination = f"{clean_path}?{query}" if query else clean_path
            return RedirectResponse(url=destination, status_code=307)

        router.add_api_route(
            legacy_path,
            legacy_public_page_redirect,
            methods=PAGE_ROUTE_METHODS,
            include_in_schema=False,
        )

    @router.get("/spotlight/{token}")
    async def get_spotlight_info(request: Request, token: str):
        db = session_factory()
        try:
            spotlight_info = db.execute(
                select(spotlight_model).where(
                    cast(spotlight_model.token, String)
                    == cast(token, String)
                )
            ).fetchone()
            if not spotlight_info:
                raise HTTPException(
                    status_code=404,
                    detail="Spotlight info not found for the given token",
                )

            data = spotlight_info[0]
            image_data = (
                base64.b64encode(data.image_data).decode("utf-8")
                if data.image_data
                else None
            )
            request.session["state"] = data.state
            request.session["county"] = data.county
            if data.district:
                request.session["district"] = data.district
            if data.school:
                request.session["school"] = data.school
                request.session["teacher"] = data.name
            return {
                "state": data.state,
                "county": data.county,
                "district": data.district,
                "school": data.school,
                "name": data.name,
                "image_data": image_data,
            }
        except Exception as exc:
            logger.error(f"Internal Server Error: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )
        finally:
            db.close()

    @router.get("/teacher/{url_id}")
    async def get_teacher_info(url_id: str, request: Request):
        db = session_factory()
        try:
            teacher_info = db.execute(
                select(teacher_model).where(
                    cast(teacher_model.url_id, String) == url_id
                )
            ).fetchone()
            if not teacher_info:
                return RedirectResponse(url="/404")
            set_teacher_session(request, teacher_info[0])
            return RedirectResponse(url="/teacher")
        except Exception:
            return RedirectResponse(url="/404")
        finally:
            db.close()

    @router.get("/promo/get_promo_info/")
    async def get_promo_info(request: Request):
        return JSONResponse(
            content={
                "promo_image_url": request.session.pop(
                    "promo_image_url",
                    None,
                ),
                "promo_title": request.session.pop("promo_title", None),
            }
        )

    @router.get("/{token}")
    async def get_promotional_page_with_hero(
        request: Request,
        token: str,
    ):
        relative_image_path = PROMO_IMAGE_MAPPING.get(token.lower())
        if not relative_image_path:
            relative_image_path = PROMO_IMAGE_MAPPING.get("default")
            if not relative_image_path:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Promotional image not found and no default image "
                        "available in mapping."
                    ),
                )

        full_filesystem_path = os.path.join(static_dir, relative_image_path)
        if not os.path.exists(full_filesystem_path):
            if token != "default":
                default_relative_path = PROMO_IMAGE_MAPPING.get("default")
                if default_relative_path and os.path.exists(
                    os.path.join(static_dir, default_relative_path)
                ):
                    relative_image_path = default_relative_path
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Image for token '{token}' not found and default "
                            "image file is also missing."
                        ),
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Default promotional image file not found.",
                )

        request.session["promo_image_url"] = (
            f"/static/{relative_image_path}"
        )
        request.session["promo_title"] = (
            "Working together to serve our communities!"
        )
        return RedirectResponse(url="/")

    return router


def register_legacy_error_handlers(app, *, pages_dir="pages"):
    async def not_found(_request: Request, _exc: HTTPException):
        return serve_page(pages_dir, "404.html", status_code=404)

    async def forbidden(_request: Request, _exc: HTTPException):
        return serve_page(pages_dir, "403.html", status_code=403)

    app.add_exception_handler(404, not_found)
    app.add_exception_handler(403, forbidden)
