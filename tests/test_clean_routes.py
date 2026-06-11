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
    ("/reset-password", "reset_password.html", ("Reset Your Password", "Invalid Reset Link")),
    ("/wishlist-setup", "wishlist_setup.html", ("Steps to Setup Wishlist", "Amazon.com")),
    ("/terms", "terms_conditions.html", ("Terms and Conditions", "Charitable Mission")),
    ("/teachers", "index.html", ("Find a Teacher", "Find Teachers")),
    ("/forum", "forum.html", ("The Teachers' Lounge", "Sort By")),
    ("/forum/new", "create_post.html", ("Start a New Discussion", "Submit New Post")),
    ("/validation", "validation.html", ("How Validation Works", "Validation List")),
    ("/admin", "admin.html", ("Get Teacher Contact Info", "Delete User Account")),
    ("/profile/create", "create.html", ("Create Teacher Profile", "Wishlist")),
    ("/profile/edit", "edit_teacher.html", ("Edit Teacher Profile", "Update URL ID")),
    ("/403", "403.html", ("403", "Forbidden")),
    ("/404", "404.html", ("404", "Page Does Not Exist")),
]

LEGACY_REDIRECT_CASES = [
    ("/pages/homepage.html", "/"),
    ("/pages/index.html", "/teachers"),
    ("/pages/about.html", "/about"),
    ("/pages/contact.html", "/contact"),
    ("/pages/partners.html", "/partners"),
    ("/pages/register.html", "/register"),
    ("/pages/login.html", "/login"),
    ("/pages/forgot.html", "/forgot"),
    ("/pages/terms_conditions.html", "/terms"),
    ("/pages/403.html", "/403"),
    ("/pages/404.html", "/404"),
]

LEGACY_DIRECT_CASES = [
    ("/pages/update_password.html", "update_password.html", "Update Your Password"),
    ("/pages/reset_password.html", "reset_password.html", "Reset Your Password"),
    ("/pages/wishlist_setup.html", "wishlist_setup.html", "Steps to Setup Wishlist"),
    ("/pages/forum.html", "forum.html", "The Teachers' Lounge"),
    ("/pages/create_post.html", "create_post.html", "Start a New Discussion"),
    ("/pages/create.html", "create.html", "Create Teacher Profile"),
    ("/pages/edit_teacher.html", "edit_teacher.html", "Edit Teacher Profile"),
    ("/pages/validation.html", "validation.html", "How Validation Works"),
    ("/pages/admin.html", "admin.html", "Delete User Account (Admin)"),
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


def test_redirect_ready_legacy_public_pages_redirect_to_clean_aliases(app_module):
    client = TestClient(app_module.app)

    for route_path, expected_location in LEGACY_REDIRECT_CASES:
        response = client.get(route_path, follow_redirects=False)

        assert response.status_code == 307, route_path
        assert response.headers["location"] == expected_location


def test_deferred_legacy_and_private_pages_still_serve_directly(app_module):
    client = TestClient(app_module.app)

    for route_path, page_name, expected_text in LEGACY_DIRECT_CASES:
        response = client.get(route_path, follow_redirects=False)

        assert response.status_code == 200, route_path
        assert "text/html" in response.headers["content-type"]
        assert normalize_text(response.text) == normalize_text(read_page(page_name))
        assert expected_text in response.text
