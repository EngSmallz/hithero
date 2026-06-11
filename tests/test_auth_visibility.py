import re

import pytest

from tests.conftest import parse_page, read_page


PUBLIC_PAGES = [
    "homepage.html",
    "index.html",
    "about.html",
    "contact.html",
    "register.html",
    "login.html",
    "partners.html",
    "terms_conditions.html",
    "forgot.html",
    "wishlist_setup.html",
    "403.html",
    "404.html",
]

PRIVATE_TARGETS = {
    "/admin",
    "/validation",
    "/profile/create",
}

EXPECTED_PRIVATE_REFERENCES = {
    "homepage.html": {"/validation"},
    "index.html": {"/validation"},
    "about.html": {"/validation"},
    "contact.html": {"/validation"},
    "register.html": {"/validation"},
    "login.html": {"/validation", "/profile/create"},
    "partners.html": {"/validation"},
    "forgot.html": {"/validation"},
}


def private_refs_in_source(source):
    return {target for target in PRIVATE_TARGETS if target in source}


def target_from_onclick(onclick):
    match = re.search(r"['\"](/(?:admin|validation|profile/create))['\"]", onclick or "")
    return match.group(1) if match else None


@pytest.mark.parametrize("page_name", PUBLIC_PAGES)
def test_public_pages_do_not_render_visible_private_navigation(page_name):
    document = parse_page(page_name)

    for anchor in document.find_all("a"):
        assert anchor.get("href") not in PRIVATE_TARGETS

    for button in document.find_all("button"):
        target = target_from_onclick(button.get("onclick"))
        if target in PRIVATE_TARGETS:
            classes = set((button.get("class") or "").split())
            assert "hidden" in classes, f"{page_name} exposes visible button to {target}"


def test_private_page_references_in_public_html_are_known_and_documented():
    actual = {
        page_name: private_refs_in_source(read_page(page_name))
        for page_name in PUBLIC_PAGES
    }
    actual = {page_name: refs for page_name, refs in actual.items() if refs}

    assert actual == EXPECTED_PRIVATE_REFERENCES
