import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    expect = None
    sync_playwright = None

pytestmark = pytest.mark.skipif(sync_playwright is None, reason="playwright is not installed")


PUBLIC_PAGE_CASES = [
    ("/", "Support Teachers, Empower Futures"),
    ("/teachers", "Find a Teacher"),
    ("/about", "About Us"),
    ("/contact", "Contact Information"),
    ("/register", "User Registration"),
    ("/login", "Log In to Your Account"),
    ("/partners", "Thank You to Our Partners"),
]

LEGACY_REDIRECT_CASES = [
    ("/pages/homepage.html", "/", "Support Teachers, Empower Futures"),
    ("/pages/index.html", "/teachers", "Find a Teacher"),
    ("/pages/about.html", "/about", "About Us"),
    ("/pages/contact.html", "/contact", "Contact Information"),
    ("/pages/register.html", "/register", "User Registration"),
    ("/pages/login.html", "/login", "Log In to Your Account"),
    ("/pages/partners.html", "/partners", "Thank You to Our Partners"),
    ("/pages/forgot.html", "/forgot", "Forgot Your Password"),
    ("/pages/terms_conditions.html", "/terms", "Terms and Conditions"),
    ("/pages/wishlist_setup.html", "/wishlist-setup", "Steps to Setup Wishlist"),
    ("/pages/403.html", "/403", "Forbidden"),
    ("/pages/404.html", "/404", "Page Does Not Exist"),
]

HOME_NAV_CASES = [
    ("/teachers", "Find a Teacher"),
    ("/register", "User Registration"),
    ("/about", "About Us"),
    ("/contact", "Contact Information"),
    ("/partners", "Thank You to Our Partners"),
]

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
    server_log = tempfile.NamedTemporaryFile(
        mode="w+",
        prefix="hithero-public-e2e-",
        suffix=".log",
        delete=False,
    )
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
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url = f"http://{client_host}:{port}"
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                server_log.seek(0)
                output = server_log.read()
                raise RuntimeError(f"uvicorn exited before tests started:\n{output}")
            try:
                with urllib.request.urlopen(f"{url}/", timeout=0.5) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.2)
        else:
            server_log.seek(0)
            output = server_log.read()
            raise RuntimeError(f"Timed out waiting for uvicorn:\n{output}")

        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        server_log.close()
        os.unlink(server_log.name)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def page(browser, base_url):
    context = browser.new_context()
    page = context.new_page()

    def route_request(route):
        url = route.request.url
        if url.startswith(base_url) or url.startswith("data:") or url.startswith("about:"):
            route.continue_()
        else:
            route.abort()

    page.route("**/*", route_request)
    yield page
    context.close()


@pytest.mark.parametrize(("path", "expected_text"), PUBLIC_PAGE_CASES)
def test_public_pages_load_in_browser(page, base_url, path, expected_text):
    page.goto(f"{base_url}{path}", wait_until="domcontentloaded")

    expect(page.locator("body")).to_contain_text(expected_text)


@pytest.mark.parametrize(("legacy_path", "clean_path", "expected_text"), LEGACY_REDIRECT_CASES)
def test_legacy_public_pages_redirect_to_clean_urls(page, base_url, legacy_path, clean_path, expected_text):
    page.goto(f"{base_url}{legacy_path}", wait_until="domcontentloaded")

    assert page.url == f"{base_url}{clean_path}"
    expect(page.locator("body")).to_contain_text(expected_text)


@pytest.mark.parametrize(("target_path", "expected_text"), HOME_NAV_CASES)
def test_homepage_public_navigation_links_work(page, base_url, target_path, expected_text):
    page.goto(f"{base_url}/", wait_until="domcontentloaded")

    page.locator(f"a[href='{target_path}']").first.click()

    assert page.url == f"{base_url}{target_path}"
    expect(page.locator("body")).to_contain_text(expected_text)


def test_account_recovery_navigation_and_form_controls_work(page, base_url):
    page.goto(f"{base_url}/login", wait_until="domcontentloaded")

    page.locator("#forgotPasswordButton").click()
    assert page.url == f"{base_url}/forgot"
    expect(page.locator("input[name='email']")).to_have_attribute("type", "email")

    page.locator("#backToLoginButton").click()
    assert page.url == f"{base_url}/login"
    expect(page.locator("input[name='email']")).to_have_attribute("type", "email")
    expect(page.locator("input[name='password']")).to_have_attribute("type", "password")


def test_public_page_loads_at_mobile_viewport(page, base_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/contact", wait_until="domcontentloaded")

    expect(page.locator("body")).to_contain_text("Contact Form")
    expect(page.locator("#hamburgerButton")).to_have_count(1)
