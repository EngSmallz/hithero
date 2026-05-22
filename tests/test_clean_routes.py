from fastapi.testclient import TestClient

from tests.conftest import normalize_text, read_page


CLEAN_ROUTE_CASES = [
    ("/", "homepage.html", ("Support Teachers, Empower Futures", "Teacher of the Day")),
    ("/home", "homepage.html", ("Support Teachers, Empower Futures", "Teacher of the Day")),
    ("/about", "about.html", ("About Us", "Our Mission")),
    ("/contact", "contact.html", ("Contact Information", "Contact Form")),
    ("/partners", "partners.html", ("Thank You to Our Partners", "Radio Partners")),
    ("/register", "register.html", ("User Registration", "Phone Number")),
    ("/login", "login.html", ("Log In to Your Account", "Forgot Password")),
    ("/forgot", "forgot.html", ("Forgot Your Password", "reset your password")),
    ("/update-password", "update_password.html", ("Update Your Password", "New Password")),
    ("/wishlist-setup", "wishlist_setup.html", ("Steps to Setup Wishlist", "Amazon.com")),
    ("/terms", "terms_conditions.html", ("Terms and Conditions", "Charitable Mission")),
    ("/teachers", "index.html", ("Find a Teacher", "Find Teachers")),
    ("/teachers/example-teacher", "teacher.html", ("Teacher Profile", "Share Page")),
    ("/403", "403.html", ("403", "Forbidden")),
    ("/404", "404.html", ("404", "Page Does Not Exist")),
]

LEGACY_ROUTE_CASES = [
    ("/pages/homepage.html", "homepage.html", "Support Teachers, Empower Futures"),
    ("/pages/index.html", "index.html", "Find a Teacher"),
    ("/pages/about.html", "about.html", "About Us"),
    ("/pages/contact.html", "contact.html", "Contact Information"),
    ("/pages/login.html", "login.html", "Log In to Your Account"),
]


def test_clean_route_aliases_serve_expected_pages(app_module):
    client = TestClient(app_module.app)

    for route_path, page_name, expected_strings in CLEAN_ROUTE_CASES:
        response = client.get(route_path)

        assert response.status_code == 200, route_path
        assert "text/html" in response.headers["content-type"]

        source = normalize_text(response.text)
        expected_page = normalize_text(read_page(page_name))
        assert source == expected_page

        for expected in expected_strings:
            assert expected in response.text, route_path


def test_legacy_page_urls_still_serve_existing_static_pages(app_module):
    client = TestClient(app_module.app)

    for route_path, page_name, expected_text in LEGACY_ROUTE_CASES:
        response = client.get(route_path)

        assert response.status_code == 200, route_path
        assert "text/html" in response.headers["content-type"]
        assert normalize_text(response.text) == normalize_text(read_page(page_name))
        assert expected_text in response.text
