"""Permanent redirects for externally shared pre-SvelteKit page URLs."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse


LEGACY_PAGE_REDIRECTS = {
    "/pages/homepage.html": "/",
    "/pages/index.html": "/teachers",
    "/pages/about.html": "/about",
    "/pages/contact.html": "/contact",
    "/pages/partners.html": "/partners",
    "/pages/register.html": "/register",
    "/pages/login.html": "/login",
    "/pages/forgot.html": "/forgot",
    "/pages/reset_password.html": "/reset-password",
    "/pages/update_password.html": "/update-password",
    "/pages/forum.html": "/forum",
    "/pages/create_post.html": "/forum/new",
    "/pages/post.html": "/forum/post",
    "/pages/teacher.html": "/teacher",
    "/pages/create.html": "/profile/create",
    "/pages/edit_teacher.html": "/profile/edit",
    "/pages/validation.html": "/validation",
    "/pages/admin.html": "/admin",
    "/pages/terms_conditions.html": "/terms",
    "/pages/wishlist_setup.html": "/wishlist-setup",
    "/pages/403.html": "/403",
    "/pages/404.html": "/404",
}


def create_redirect_router():
    """Redirect retired page URLs while the deployment proxy serves SvelteKit."""
    router = APIRouter()

    for legacy_path, clean_path in LEGACY_PAGE_REDIRECTS.items():
        async def redirect_legacy_page(
            request: Request,
            clean_path: str = clean_path,
        ):
            query = request.url.query
            destination = f"{clean_path}?{query}" if query else clean_path
            return RedirectResponse(url=destination, status_code=308)

        router.add_api_route(
            legacy_path,
            redirect_legacy_page,
            methods=["GET", "HEAD"],
            include_in_schema=False,
        )

    return router
