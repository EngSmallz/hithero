import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pytest

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    expect = None
    sync_playwright = None

pytestmark = pytest.mark.skipif(sync_playwright is None, reason="playwright is not installed")


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TEST_HOST = "127.0.0.1"


def find_free_port(host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, 0))
        except PermissionError as exc:
            pytest.skip(f"OS does not allow e2e test server binding on {host}: {exc}")
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    bind_host = os.getenv("E2E_BIND_HOST", DEFAULT_TEST_HOST)
    client_host = os.getenv("E2E_CLIENT_HOST", DEFAULT_TEST_HOST)
    port = int(os.getenv("E2E_PORT") or find_free_port(bind_host))
    env = {
        **os.environ,
        "APP_ENV": "test",
        "SECRET_KEY": "test-secret",
        "PYTHONUNBUFFERED": "1",
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            bind_host,
            "--port",
            str(port),
        ],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url = f"http://{client_host}:{port}"
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"uvicorn exited before tests started:\n{output}")
            try:
                with urllib.request.urlopen(f"{url}/", timeout=0.5) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.2)
        else:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"Timed out waiting for uvicorn:\n{output}")

        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


def install_routes(page, base_url, stubs):
    def route_request(route):
        url = route.request.url
        parsed_url = urlparse(url)
        path = parsed_url.path
        path_with_query = path
        if parsed_url.query:
            path_with_query = f"{path}?{parsed_url.query}"

        if url.startswith(base_url):
            for matcher, response in stubs.items():
                if path == matcher or path_with_query == matcher:
                    status, payload = response
                    route.fulfill(
                        status=status,
                        content_type="application/json",
                        body=json.dumps(payload),
                    )
                    return
            route.continue_()
            return

        if url.startswith("data:") or url.startswith("about:"):
            route.continue_()
            return

        route.abort()

    page.route("**/*", route_request)


def json_stub(payload, status=200):
    return status, payload


def assert_has_class(page, selector, class_name):
    assert page.locator(selector).evaluate(
        "(element, className) => element.classList.contains(className)",
        class_name,
    )


def assert_lacks_class(page, selector, class_name):
    assert not page.locator(selector).evaluate(
        "(element, className) => element.classList.contains(className)",
        class_name,
    )


def profile_stub(role, user_id=7):
    if role is None:
        return json_stub({"detail": "Not authenticated"}, status=401)
    return json_stub({"user_role": role, "user_id": user_id})


def teacher_info_stub():
    return json_stub(
        {
            "state": "Washington",
            "county": "King",
            "district": "Seattle Public Schools",
            "school": "Evergreen Elementary",
            "name": "Test Teacher",
            "wishlist_url": "https://example.com/wishlist",
            "about_me": "I help students build durable skills.",
            "image_data": None,
        }
    )


def forum_post():
    return {
        "id": 101,
        "title": "Browser covered post",
        "content": "This discussion was rendered from a mocked forum API response.",
        "created_at": "2026-06-10T12:00:00",
        "user_id": 7,
        "upvote_count": 3,
        "comment_count": 0,
    }


@pytest.mark.parametrize(
    ("role", "visible_buttons", "hidden_buttons"),
    [
        (None, ("loginButton",), ("logoutButton", "mypageButton", "forumButton", "validationButton")),
        ("teacher", ("logoutButton", "mypageButton", "forumButton", "validationButton"), ("loginButton",)),
        ("admin", ("logoutButton", "forumButton", "validationButton"), ("loginButton", "mypageButton")),
    ],
)
def test_public_header_auth_buttons_reflect_profile_role(page, base_url, role, visible_buttons, hidden_buttons):
    install_routes(page, base_url, {"/api/profile/": profile_stub(role)})

    page.goto(f"{base_url}/", wait_until="domcontentloaded")
    page.locator("#hamburgerButton").click()

    for button_id in visible_buttons:
        assert_lacks_class(page, f"#{button_id}", "hidden")
    for button_id in hidden_buttons:
        assert_has_class(page, f"#{button_id}", "hidden")


@pytest.mark.parametrize(
    ("role", "expect_owner_controls"),
    [
        (None, False),
        ("teacher", True),
        ("admin", True),
    ],
)
def test_teacher_page_renders_mocked_profile_data_and_role_controls(
    page, base_url, role, expect_owner_controls
):
    install_routes(
        page,
        base_url,
        {
            "/api/profile/": profile_stub(role),
            "/api/check_access_teacher/": json_stub({"message": "allowed"}),
            "/api/get_teacher_info/": teacher_info_stub(),
        },
    )

    page.goto(f"{base_url}/pages/teacher.html", wait_until="domcontentloaded")

    assert_lacks_class(page, "#main-container", "hidden")
    expect(page.locator("#teacher-name")).to_contain_text("Test Teacher")
    expect(page.locator("#school-name")).to_contain_text("Evergreen Elementary")
    expect(page.locator("#about-me")).to_contain_text("durable skills")

    if expect_owner_controls:
        assert_lacks_class(page, "#editButton", "hidden")
        assert_lacks_class(page, "#updateButton", "hidden")
    else:
        assert_has_class(page, "#editButton", "hidden")
        assert_has_class(page, "#updateButton", "hidden")


@pytest.mark.parametrize(
    "path",
    [
        "/profile/create",
        "/forum/new",
        "/validation",
        "/admin",
    ],
)
def test_private_pages_redirect_unauthenticated_visitors_to_forbidden(page, base_url, path):
    install_routes(page, base_url, {"/api/profile/": profile_stub(None)})

    page.goto(f"{base_url}{path}", wait_until="domcontentloaded")

    page.wait_for_timeout(500)
    assert page.url == f"{base_url}/403"
    expect(page.locator("body")).to_contain_text("Forbidden")


def test_validation_page_renders_mocked_teacher_signup_list_for_admin(page, base_url):
    install_routes(
        page,
        base_url,
        {
            "/api/profile/": profile_stub("admin"),
            "/api/validation_list/": json_stub(
                {
                    "new_users": [
                        {
                            "name": "New Teacher",
                            "email": "new.teacher@example.com",
                            "state": "WA",
                            "district": "Seattle",
                            "school": "Evergreen Elementary",
                            "phone_number": "555-0100",
                            "emailed": 0,
                            "report": 1,
                        }
                    ]
                }
            ),
        },
    )

    page.goto(f"{base_url}/validation", wait_until="domcontentloaded")

    expect(page.locator("#validationList")).to_contain_text("New Teacher")
    expect(page.locator("#validationList")).to_contain_text("new.teacher@example.com")
    expect(page.locator("#validationList")).to_contain_text("Validate")
    expect(page.locator("#validationList")).to_contain_text("Delete")
    expect(page.locator("#validationList")).to_contain_text("REPORTED")


def test_forum_list_and_post_detail_render_from_mocked_api_responses(page, base_url):
    post = forum_post()
    install_routes(
        page,
        base_url,
        {
            "/api/profile/": profile_stub("teacher"),
            "/forum/get_posts": json_stub([post]),
            "/forum/get_post?post_id=101": json_stub(post),
            "/forum/comments/101/": json_stub([]),
        },
    )

    page.goto(f"{base_url}/forum", wait_until="domcontentloaded")

    expect(page.locator("#posts-container")).to_contain_text("Browser covered post")
    expect(page.locator("#posts-container")).to_contain_text("mocked forum API")

    page.locator("a[href='/pages/post.html?id=101']").click()

    page.wait_for_url(f"{base_url}/pages/post.html?id=101")
    expect(page.locator("#post-detail-card")).to_contain_text("Browser covered post")
    expect(page.locator("#post-detail-card")).to_contain_text("mocked forum API")
    expect(page.locator("#comment-count-display")).to_contain_text("0")
