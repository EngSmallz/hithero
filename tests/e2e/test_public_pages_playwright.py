import os
import socket
import subprocess
import sys
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
    ("/pages/homepage.html", "Support Teachers, Empower Futures"),
    ("/pages/index.html", "Find a Teacher"),
    ("/pages/about.html", "About Us"),
    ("/pages/contact.html", "Contact Information"),
    ("/pages/register.html", "User Registration"),
    ("/pages/login.html", "Log In to Your Account"),
    ("/pages/partners.html", "Thank You to Our Partners"),
]

ROOT_DIR = Path(__file__).resolve().parents[2]


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def base_url():
    port = find_free_port()
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
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 20
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"uvicorn exited before tests started:\n{output}")
            try:
                with urllib.request.urlopen(f"{url}/pages/homepage.html", timeout=0.5) as response:
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


def test_public_page_loads_at_mobile_viewport(page, base_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base_url}/pages/contact.html", wait_until="domcontentloaded")

    expect(page.locator("body")).to_contain_text("Contact Form")
    expect(page.locator("#hamburgerButton")).to_have_count(1)
