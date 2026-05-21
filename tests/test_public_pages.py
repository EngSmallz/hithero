import pytest

from tests.conftest import PAGES_DIR, parse_page, read_page


PUBLIC_PAGE_CASES = [
    ("homepage.html", ["Support Teachers, Empower Futures", "Teacher of the Day", "Find Teachers to Support"]),
    ("index.html", ["Find a Teacher", "Search Results", "Find Teachers"]),
    ("about.html", ["About Us", "Our Mission", "Website Terms and Conditions"]),
    ("contact.html", ["Contact Information", "Contact Form", "Homeroom Heroes"]),
    ("register.html", ["User Registration", "Phone Number", "Terms and Conditions"]),
    ("login.html", ["Log In to Your Account", "Forgot Password", "Register"]),
    ("partners.html", ["Thank You to Our Partners", "Radio Partners", "Become a Partner"]),
    ("terms_conditions.html", ["Terms and Conditions", "Charitable Mission", "User Registration"]),
    ("forgot.html", ["Forgot Your Password", "reset your password", "Email"]),
    ("wishlist_setup.html", ["Steps to Setup Wishlist", "Amazon.com", "Copy Link"]),
    ("403.html", ["403", "Forbidden", "permission"]),
    ("404.html", ["404", "Page Does Not Exist", "Go to Homepage"]),
]


@pytest.mark.parametrize(("page_name", "expected_strings"), PUBLIC_PAGE_CASES)
def test_public_html_pages_exist_and_have_page_specific_content(page_name, expected_strings):
    path = PAGES_DIR / page_name

    assert path.exists(), f"{page_name} should exist"
    source = read_page(page_name)
    document = parse_page(page_name)

    assert source.strip(), f"{page_name} should not be empty"
    assert source.lstrip().lower().startswith("<!doctype html>")
    assert document.find_all("html")
    assert document.find_all("head")
    assert document.find_all("body")
    assert document.find_all("title")

    for expected in expected_strings:
        assert expected in document.text or expected in source


def test_fastapi_app_imports_in_test_mode_without_production_db_url(app_module):
    assert app_module.APP_ENV == "test"
    assert app_module.SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    assert callable(app_module.init_db)


def test_init_db_uses_explicit_create_all_call(app_module, monkeypatch):
    calls = []

    def fake_create_all(bind):
        calls.append(bind)

    monkeypatch.setattr(app_module.Base.metadata, "create_all", fake_create_all)

    app_module.init_db()

    assert calls == [app_module.engine]
