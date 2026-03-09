from pathlib import Path

import pytest

ARTIFACTS_DIR = Path("test-artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when != "call" or rep.passed:
        return

    page = item.funcargs.get("page")
    if page is None:
        return

    screenshot_path = ARTIFACTS_DIR / f"{item.name}-failed.png"
    page.screenshot(path=str(screenshot_path), full_page=True)