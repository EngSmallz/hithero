import html
import importlib
import os
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret")

ROOT_DIR = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT_DIR / "pages"


def isolate_xdist_sqlite_database():
    worker = os.getenv("PYTEST_XDIST_WORKER")
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not worker or not test_database_url or os.getenv("DATABASE_URL"):
        return

    if test_database_url == "sqlite:///:memory:" or not test_database_url.startswith("sqlite:///"):
        return

    database_name = test_database_url.removeprefix("sqlite:///")
    if not database_name or database_name == ":memory:":
        return

    database_path = Path(database_name)
    if not database_path.is_absolute():
        database_path = ROOT_DIR / database_path

    worker_path = database_path.with_name(f"{database_path.stem}-{worker}{database_path.suffix}")
    worker_path.parent.mkdir(parents=True, exist_ok=True)

    os.environ["TEST_DATABASE_URL"] = f"sqlite:///{worker_path}"


isolate_xdist_sqlite_database()


class HtmlDocument(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.elements = []
        self.text_chunks = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag.lower(), dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.text_chunks.append(data)

    @property
    def text(self):
        return normalize_text(" ".join(self.text_chunks))

    def find_all(self, tag=None, **attrs):
        matches = []
        for element_tag, element_attrs in self.elements:
            if tag and element_tag != tag:
                continue
            if all(element_attrs.get(key) == value for key, value in attrs.items()):
                matches.append(element_attrs)
        return matches

    def find_by_id(self, element_id):
        matches = self.find_all(id=element_id)
        return matches[0] if matches else None


def normalize_text(value):
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def read_page(page_name):
    return (PAGES_DIR / page_name).read_text(encoding="utf-8")


def parse_page(page_name):
    return HtmlDocument(read_page(page_name))


@pytest.fixture(scope="session")
def app_module():
    return importlib.import_module("app")
