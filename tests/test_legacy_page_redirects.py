from fastapi.testclient import TestClient

from backend.routers.redirects import LEGACY_PAGE_REDIRECTS


def test_retired_page_urls_redirect_to_clean_urls(app_module):
    client = TestClient(app_module.app)

    for legacy_path, clean_path in LEGACY_PAGE_REDIRECTS.items():
        response = client.get(legacy_path, follow_redirects=False)

        assert response.status_code == 308, legacy_path
        assert response.headers["location"] == clean_path


def test_retired_page_redirects_preserve_query_strings(app_module):
    client = TestClient(app_module.app)

    response = client.get(
        "/pages/reset_password.html?token=reset-token-123&campaign=summer",
        follow_redirects=False,
    )

    assert response.status_code == 308
    assert response.headers["location"] == (
        "/reset-password?token=reset-token-123&campaign=summer"
    )
