from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


ARTIFACTS_DIR = Path("test-artifacts")


@pytest.fixture(scope="session")
def browser():
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def context(browser, request):
    test_name = request.node.name
    context = browser.new_context()

    context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True,
    )

    yield context

    trace_path = ARTIFACTS_DIR / f"{test_name}-trace.zip"
    context.tracing.stop(path=str(trace_path))
    context.close()


@pytest.fixture
def page(context):
    page = context.new_page()
    yield page
    page.close()