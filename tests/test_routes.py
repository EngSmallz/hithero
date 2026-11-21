"""BE1-2: every (method, path) the app serves, compared to a golden file.

The refactor moves all routes out of app.py. This test fails if any route
is dropped, renamed, gains or loses a trailing slash, or changes method.

After an intended route change, regenerate the golden file with:
    UPDATE_GOLDEN=1 pytest tests/test_routes.py
and review the diff of tests/golden/routes.txt.
"""
from pathlib import Path

from fastapi.routing import APIRoute
from starlette.routing import Mount

from tests.conftest import update_golden

GOLDEN = Path(__file__).parent / "golden" / "routes.txt"


def _flatten(routes):
    """Yield routes, descending into included routers.

    FastAPI >= 0.16x keeps an included router as one entry whose
    original_router holds its routes. The app includes routers without a
    prefix, so their paths are the served paths.
    """
    for route in routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from _flatten(included.routes)
        else:
            yield route


def collect_routes() -> list[str]:
    from app.main import app as fastapi_app

    lines = set()
    for route in _flatten(fastapi_app.routes):
        if isinstance(route, APIRoute):
            for method in route.methods:
                lines.add(f"{method} {route.path}")
        elif isinstance(route, Mount):
            lines.add(f"MOUNT {route.path}")
    return sorted(lines)


def test_routes_match_golden():
    actual = collect_routes()
    if update_golden():
        GOLDEN.write_text("\n".join(actual) + "\n")
    expected = GOLDEN.read_text().splitlines()

    missing = sorted(set(expected) - set(actual))
    added = sorted(set(actual) - set(expected))
    assert not missing and not added, (
        "Routes differ from tests/golden/routes.txt.\n"
        f"Missing (in golden, not in app): {missing}\n"
        f"Added (in app, not in golden): {added}\n"
        "If this change is intended, run UPDATE_GOLDEN=1 pytest tests/test_routes.py"
    )
