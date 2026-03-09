import allure
import pytest

from tests.builders.link_builder import LinkBuilder
from tests.ui.pages.admin_links_page import AdminLinksPage
from tests.ui.pages.login_page import LoginPage

BASE_URL = "http://127.0.0.1:8005"
API_HEADERS = {"X-API-Key": "test-api-key"}


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Successful admin login")
@pytest.mark.ui
@pytest.mark.smoke
def test_admin_login(page):
    login = LoginPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")

    page.wait_for_url(f"{BASE_URL}/admin/links")
    assert "Links" in page.locator("body").inner_text()


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Block link from admin panel")
@pytest.mark.ui
@pytest.mark.smoke
def test_admin_can_block_link(page):
    payload = LinkBuilder.create_payload()

    resp = page.request.post(
        f"{BASE_URL}/api/v1/links",
        data=payload,
        headers=API_HEADERS,
    )
    assert resp.status == 201
    code = resp.json()["code"]

    login = LoginPage(page)
    admin = AdminLinksPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")
    page.wait_for_url(f"{BASE_URL}/admin/links")

    admin.block(code)
    page.wait_for_url(f"{BASE_URL}/admin/links")

    assert "yes" in admin.row(code).inner_text()

    redirect_resp = page.request.get(f"{BASE_URL}/r/{code}", max_redirects=0)
    assert redirect_resp.status == 404


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Open link details and view click events")
@pytest.mark.ui
@pytest.mark.regression
def test_admin_can_open_link_details(page):
    payload = LinkBuilder.with_custom_code("detail-ui-01")

    resp = page.request.post(
        f"{BASE_URL}/api/v1/links",
        data=payload,
        headers=API_HEADERS,
    )
    assert resp.status == 201
    code = resp.json()["code"]

    click_resp = page.request.get(
        f"{BASE_URL}/r/{code}",
        headers={"referer": "https://google.com"},
        max_redirects=0,
    )
    assert click_resp.status == 302

    login = LoginPage(page)
    admin = AdminLinksPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")
    page.wait_for_url(f"{BASE_URL}/admin/links")

    admin.open_details(code)
    page.wait_for_url(f"{BASE_URL}/admin/links/{code}")

    body = admin.body()
    assert "Link details" in body
    assert code in body
    assert "Click events" in body
    assert "google.com" in body or "https://google.com" in body


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Soft delete link from admin panel")
@pytest.mark.ui
@pytest.mark.regression
def test_admin_can_soft_delete_link(page):
    payload = LinkBuilder.with_custom_code("delete-ui-01")

    resp = page.request.post(
        f"{BASE_URL}/api/v1/links",
        data=payload,
        headers=API_HEADERS,
    )
    assert resp.status == 201

    login = LoginPage(page)
    admin = AdminLinksPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")
    page.wait_for_url(f"{BASE_URL}/admin/links")

    admin.delete("delete-ui-01")
    page.wait_for_url(lambda url: "include_deleted=yes" in url)

    assert "delete-ui-01" in admin.body()
    assert "yes" in admin.row("delete-ui-01").inner_text()

    redirect_resp = page.request.get(f"{BASE_URL}/r/delete-ui-01", max_redirects=0)
    assert redirect_resp.status == 404


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Search link by code")
@pytest.mark.ui
@pytest.mark.regression
def test_admin_can_search_link(page):
    payload = LinkBuilder.with_custom_code("search-ui-01")

    resp = page.request.post(
        f"{BASE_URL}/api/v1/links",
        data=payload,
        headers=API_HEADERS,
    )
    assert resp.status == 201

    login = LoginPage(page)
    admin = AdminLinksPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")
    page.wait_for_url(f"{BASE_URL}/admin/links")

    page.goto(f"{BASE_URL}/admin/links?q=search-ui-01")

    body = admin.body()
    assert "search-ui-01" in body


@allure.epic("URL Shortener")
@allure.feature("Admin UI")
@allure.story("Pagination works in admin links table")
@pytest.mark.ui
@pytest.mark.regression
def test_admin_pagination_works(page):
    for i in range(1, 7):
        payload = LinkBuilder.with_custom_code(f"page-ui-{i:02d}")
        resp = page.request.post(
            f"{BASE_URL}/api/v1/links",
            data=payload,
            headers=API_HEADERS,
        )
        assert resp.status == 201

    login = LoginPage(page)
    admin = AdminLinksPage(page)

    login.open(BASE_URL)
    login.login("admin", "admin123")
    page.wait_for_url(f"{BASE_URL}/admin/links")

    admin.set_page_size("5")
    admin.apply()
    page.wait_for_url(lambda url: "/admin/links" in url)

    assert "Page: 1 /" in admin.body()

    if page.locator('a:text("Next")').count() > 0:
        page.click('a:text("Next")')
        page.wait_for_url(lambda url: "page=2" in url)
        assert "Page: 2 /" in admin.body()