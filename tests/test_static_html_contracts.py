import pytest

from tests.conftest import parse_page, read_page

PUBLIC_ALIAS_EXPECTATIONS = {
    "homepage.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login"),
    "index.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login"),
    "about.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login", "/terms"),
    "contact.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login"),
    "partners.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login"),
    "register.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login", "/terms"),
    "login.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login", "/forgot"),
    "forgot.html": ("/", "/teachers", "/register", "/about", "/contact", "/partners", "/login"),
    "403.html": ("/",),
    "404.html": ("/",),
}

ROLE_OR_SESSION_PAGES_WITH_PUBLIC_NAV = (
    "admin.html",
    "create.html",
    "create_post.html",
    "edit_teacher.html",
    "forum.html",
    "post.html",
    "reset_password.html",
    "teacher.html",
    "update_password.html",
    "validation.html",
)

CLEANED_PUBLIC_LEGACY_TARGETS = (
    "/pages/homepage.html",
    "/pages/index.html",
    "/pages/register.html",
    "/pages/about.html",
    "/pages/contact.html",
    "/pages/partners.html",
    "/pages/login.html",
    "/pages/forgot.html",
    "/pages/terms_conditions.html",
    "/pages/update_password.html",
    "/pages/wishlist_setup.html",
    "/pages/403.html",
    "/pages/404.html",
)

DEFERRED_PRIVATE_OR_SESSION_LINKS = {
    "homepage.html": ("/forum", "/validation", "/pages/teacher.html"),
    "index.html": ("/forum", "/validation"),
    "about.html": ("/forum", "/validation"),
    "contact.html": ("/forum", "/validation"),
    "partners.html": ("/forum", "/validation"),
    "register.html": ("/forum", "/validation"),
    "login.html": ("/forum", "/validation", "/profile/create"),
    "forgot.html": ("/forum", "/validation"),
}

CLEANED_PRIVATE_LEGACY_TARGETS = (
    "/pages/forum.html",
    "/pages/create_post.html",
    "/pages/validation.html",
    "/pages/admin.html",
    "/pages/create.html",
    "/pages/edit_teacher.html",
)

REMOVED_LEGACY_PUBLIC_LINKS = {
    "homepage.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
    ),
    "index.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
    ),
    "about.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
        "/pages/terms_conditions.html",
    ),
    "contact.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
    ),
    "partners.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
    ),
    "register.html": (
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
        "/pages/terms_conditions.html",
    ),
    "login.html": (
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
        "/pages/forgot.html",
    ),
    "forgot.html": (
        "/pages/homepage.html",
        "/pages/index.html",
        "/pages/register.html",
        "/pages/about.html",
        "/pages/contact.html",
        "/pages/partners.html",
        "/pages/login.html",
    ),
    "403.html": ("/pages/homepage.html",),
    "404.html": ("/pages/homepage.html",),
}


def assert_element(document, element_id, message=None):
    element = document.find_by_id(element_id)
    assert element is not None, message or f"Expected element with id={element_id!r}"
    return element


def assert_named_field(document, field_name, field_id=None, tag_names=("input", "select", "textarea")):
    field_id = field_id or field_name
    matches = []
    for tag_name in tag_names:
        matches.extend(
            attrs for attrs in document.find_all(tag_name)
            if attrs.get("name") == field_name and attrs.get("id") == field_id
        )
    assert matches, f"Expected field name={field_name!r} id={field_id!r}"
    assert document.find_all("label", **{"for": field_id}), f"Expected label for {field_id!r}"
    return matches[0]


def test_register_form_contract():
    document = parse_page("register.html")
    source = read_page("register.html")

    form = assert_element(document, "registration-form")
    assert form["method"].lower() == "post"

    for field in ["name", "email", "phone_number", "password", "confirm_password"]:
        field_attrs = assert_named_field(document, field)
        assert "required" in field_attrs

    for field in ["state", "county", "district", "school"]:
        field_attrs = assert_named_field(document, field, tag_names=("select",))
        assert "required" in field_attrs

    assert "populateCountiesDropdown()" in source
    assert "populateDistrictsDropdown()" in source
    assert "populateSchoolsDropdown()" in source
    assert source.count('class="auth-label"') == 9
    assert source.count('class="auth-input"') == 9
    assert 'class="auth-submit"' in source
    assert 'class="auth-link"' in source
    assert "block text-lg font-medium text-gray-700 mb-2" not in source
    assert "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-base bg-gray-50 text-gray-900" not in source
    assert "w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md" not in source
    assert "text-blue-600 hover:text-blue-800 font-medium transition duration-300 ease-in-out" not in source
    assert_element(document, "termsButton")
    assert_element(document, "termsConditionsModal")
    assert_named_field(document, "termsCheckbox", tag_names=("input",))
    assert document.find_all("iframe")[0]["src"] == "/terms"
    assert document.find_all("div", **{"class": "g-recaptcha mt-4"})
    assert_element(document, "submitButton")


def test_login_form_contract():
    document = parse_page("login.html")
    source = read_page("login.html")

    form = assert_element(document, "login-form")
    assert form["method"].lower() == "post"

    email = assert_named_field(document, "email")
    password = assert_named_field(document, "password")
    assert email["type"] == "email"
    assert password["type"] == "password"
    assert "required" in email
    assert "required" in password
    assert_element(document, "submitButton")
    assert_element(document, "forgotPasswordButton")
    assert_element(document, "registerButton")
    assert 'class="auth-card"' in source
    assert 'class="auth-label"' in source
    assert 'class="auth-input"' in source
    assert 'class="auth-submit"' in source
    assert 'class="auth-link mr-4"' in source
    assert 'class="auth-link"' in source
    assert "bg-white p-8 rounded-lg shadow-md text-gray-800 max-w-lg mx-auto" not in source
    assert "block text-lg font-medium text-gray-700 mb-2" not in source
    assert "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-base bg-gray-50 text-gray-900" not in source
    assert "w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md" not in source
    assert "text-blue-600 hover:text-blue-800 font-medium transition duration-300 ease-in-out" not in source
    assert "/profile/login/" in source
    assert "/forgot" in source
    assert "/register" in source


def test_contact_form_contract():
    document = parse_page("contact.html")
    source = read_page("contact.html")

    form = assert_element(document, "contact-form")
    assert form["method"].lower() == "post"
    assert form["enctype"] == "multipart/form-data"

    for field in ["name", "email", "subject"]:
        assert_named_field(document, field)
    message = assert_named_field(document, "message", tag_names=("textarea",))
    assert message["maxlength"] == "250"
    assert_element(document, "charCount")
    assert_element(document, "contact-message")
    assert_element(document, "submitButton")
    assert document.find_all("div", **{"class": "g-recaptcha"})
    assert '<script src="/static/js/contact-form.js"></script>' in source
    assert "function updateCharacterCount(" not in source
    assert "/api/contact_us/" not in source


def test_forgot_password_form_contract():
    document = parse_page("forgot.html")
    source = read_page("forgot.html")

    form = assert_element(document, "forgot-form")
    assert form["method"].lower() == "post"

    email = assert_named_field(document, "email")
    assert email["type"] == "email"
    assert "required" in email
    assert_element(document, "submitButton")
    assert_element(document, "backToLoginButton")
    assert 'class="auth-card"' in source
    assert 'class="auth-label"' in source
    assert 'class="auth-input"' in source
    assert 'class="auth-submit"' in source
    assert 'class="auth-link"' in source
    assert "bg-white p-8 rounded-lg shadow-md text-gray-800 max-w-lg mx-auto" not in source
    assert "block text-lg font-medium text-gray-700 mb-2" not in source
    assert "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-base bg-gray-50 text-gray-900" not in source
    assert "w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md" not in source
    assert "text-blue-600 hover:text-blue-800 font-medium transition duration-300 ease-in-out" not in source
    assert "/profile/forgot_password/" in source
    assert "/login" in source


def test_update_password_form_contract():
    document = parse_page("update_password.html")
    source = read_page("update_password.html")

    form = assert_element(document, "update-form")
    assert form["method"].lower() == "post"
    assert form["enctype"] == "multipart/form-data"

    for field in ["old_password", "new_password", "new_password_confirmed"]:
        field_attrs = assert_named_field(document, field)
        assert field_attrs["type"] == "password"
        assert "required" in field_attrs

    assert_element(document, "submitButton")
    assert 'class="auth-card-md"' in source
    assert source.count('class="auth-label"') == 3
    assert source.count('class="auth-input-lg"') == 3
    assert 'class="auth-submit-lg"' in source
    assert "bg-white p-8 rounded-lg shadow-md text-gray-800 w-full max-w-md" not in source
    assert "block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-lg" not in source
    assert "w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md text-xl" not in source
    assert "/profile/update_password/" in source


def test_reset_password_form_contract():
    document = parse_page("reset_password.html")
    source = read_page("reset_password.html")

    assert_element(document, "invalid-token-section")
    assert_element(document, "reset-form-section")
    assert_element(document, "success-section")
    assert_element(document, "reset-form")
    assert_element(document, "error-message")
    token_field = assert_element(document, "token")
    assert token_field["name"] == "token"
    assert token_field["type"] == "hidden"
    assert 'class="auth-card-md hidden"' in source
    assert source.count('class="auth-card-md hidden"') == 3

    for field in ["new_password", "confirm_password"]:
        field_attrs = assert_named_field(document, field)
        assert field_attrs["type"] == "password"
        assert "required" in field_attrs

    assert_element(document, "submitButton")
    assert source.count('class="auth-label"') == 2
    assert source.count('class="auth-input-lg"') == 2
    assert 'class="auth-submit-lg"' in source
    assert "bg-white p-8 rounded-lg shadow-md text-gray-800 w-full max-w-md" not in source
    assert "block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500 sm:text-lg" not in source
    assert "w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-md text-xl" not in source
    assert "/profile/reset_password/" in source


@pytest.mark.parametrize("page_name", ["register.html", "login.html", "contact.html", "forgot.html", "update_password.html"])
def test_auth_header_javascript_contracts_exist_on_form_pages(page_name):
    source = read_page(page_name)
    document = parse_page(page_name)

    assert_element(document, "hamburgerButton")
    assert_element(document, "menuItems")
    for button_id in ["loginButton", "logoutButton", "mypageButton", "forumButton", "validationButton"]:
        assert_element(document, button_id)

    assert '/static/js/auth.js' in source


@pytest.mark.parametrize(
    "page_name",
    [
        "homepage.html",
        "index.html",
        "about.html",
        "contact.html",
        "register.html",
        "login.html",
        "partners.html",
        "forgot.html",
        "update_password.html",
        "reset_password.html",
    ],
)
def test_shared_auth_script_is_used_without_inline_shared_function_defs(page_name):
    source = read_page(page_name)

    assert '<script src="/static/js/auth.js"></script>' in source
    assert "function redirectTo(" not in source
    assert "function toggleMenu(" not in source
    assert "async function checkAuthentication(" not in source
    assert "async function logout(" not in source
    assert "async function mypage(" not in source


@pytest.mark.parametrize("page_name", ["validation.html", "teacher.html"])
def test_shared_auth_script_is_used_without_inline_shared_function_defs_on_role_pages(page_name):
    source = read_page(page_name)

    assert '<script src="/static/js/auth.js"></script>' in source
    assert "function redirectTo(" not in source
    assert "function toggleMenu(" not in source
    assert "async function checkAuthentication(" not in source
    assert "async function logout(" not in source
    assert "async function mypage(" not in source


@pytest.mark.parametrize("page_name", ["index.html", "register.html"])
def test_shared_school_dropdown_script_is_used_without_inline_dropdown_function_defs(page_name):
    source = read_page(page_name)

    assert '<script src="/static/js/school-dropdowns.js"></script>' in source
    assert "configureSchoolDropdowns(" in source
    assert "async function populateStatesDropdown(" not in source
    assert "async function populateCountiesDropdown(" not in source
    assert "async function populateDistrictsDropdown(" not in source
    assert "async function populateSchoolsDropdown(" not in source


@pytest.mark.parametrize("page_name", ["login.html", "forgot.html", "update_password.html", "reset_password.html", "register.html"])
def test_shared_forms_helpers_script_is_used_on_account_pages(page_name):
    source = read_page(page_name)

    assert '<script src="/static/js/forms.js"></script>' in source
    assert "function postForm(" not in source
    assert "function postFormData(" not in source
    assert "function parseJsonSafe(" not in source


@pytest.mark.parametrize(
    ("page_name", "preserved_css"),
    [
        ("403.html", ()),
        ("404.html", ()),
        ("terms_conditions.html", ()),
        ("wishlist_setup.html", ("li::marker", "list-style-type: decimal")),
    ],
)
def test_static_pages_use_shared_body_theme_without_inline_body_rule(page_name, preserved_css):
    source = read_page(page_name)

    assert '<link rel="stylesheet" href="/static/style.css">' in source
    assert "font-family: 'Inter', sans-serif;" not in source
    assert "background-color: #1f2937;" not in source
    assert "color: #f9fafb;" not in source

    for css_snippet in preserved_css:
        assert css_snippet in source


@pytest.mark.parametrize(("page_name", "expected_targets"), PUBLIC_ALIAS_EXPECTATIONS.items())
def test_public_navigation_and_cta_links_use_clean_aliases(page_name, expected_targets):
    source = read_page(page_name)

    for target in expected_targets:
        assert target in source, f"Expected {target!r} in {page_name}"


@pytest.mark.parametrize(("page_name", "deferred_targets"), DEFERRED_PRIVATE_OR_SESSION_LINKS.items())
def test_deferred_private_or_session_dependent_links_may_remain_legacy(page_name, deferred_targets):
    source = read_page(page_name)

    for target in deferred_targets:
        assert target in source, f"Expected deferred legacy target {target!r} in {page_name}"


@pytest.mark.parametrize(("page_name", "legacy_targets"), REMOVED_LEGACY_PUBLIC_LINKS.items())
def test_migrated_public_links_no_longer_use_legacy_page_urls(page_name, legacy_targets):
    source = read_page(page_name)

    for target in legacy_targets:
        assert target not in source, f"Did not expect legacy public target {target!r} in {page_name}"


@pytest.mark.parametrize("page_name", ROLE_OR_SESSION_PAGES_WITH_PUBLIC_NAV)
def test_role_and_session_pages_no_longer_use_legacy_public_urls(page_name):
    source = read_page(page_name)

    for target in CLEANED_PUBLIC_LEGACY_TARGETS:
        assert target not in source, f"Did not expect legacy public target {target!r} in {page_name}"


@pytest.mark.parametrize(
    "page_name",
    (
        "homepage.html",
        "index.html",
        "about.html",
        "contact.html",
        "partners.html",
        "register.html",
        "login.html",
        "forgot.html",
        "admin.html",
        "create.html",
        "create_post.html",
        "edit_teacher.html",
        "forum.html",
        "post.html",
        "reset_password.html",
        "teacher.html",
        "update_password.html",
        "validation.html",
    ),
)
def test_pages_no_longer_use_migrated_private_legacy_urls(page_name):
    source = read_page(page_name)

    for target in CLEANED_PRIVATE_LEGACY_TARGETS:
        assert target not in source, f"Did not expect migrated private target {target!r} in {page_name}"
