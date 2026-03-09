import allure
import pytest

from tests.builders.link_builder import LinkBuilder


@allure.epic("URL Shortener")
@allure.feature("Links API Filters")
@allure.story("List links with sorting and pagination")
@pytest.mark.api
@pytest.mark.regression
def test_list_links_with_filters_sort_and_pagination(client, api_headers):
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("bbb01"), headers=api_headers)
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("aaa01"), headers=api_headers)
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("ccc01"), headers=api_headers)

    client.get("/r/bbb01", follow_redirects=False)
    client.get("/r/bbb01", follow_redirects=False)
    client.get("/r/aaa01", follow_redirects=False)

    response = client.get(
        "/api/v1/links",
        params={"sort": "clicks_desc", "page": 1, "page_size": 2},
        headers=api_headers,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["code"] == "bbb01"
    assert body["items"][1]["code"] == "aaa01"


@allure.epic("URL Shortener")
@allure.feature("Links API Filters")
@allure.story("Filter links by query")
@pytest.mark.api
@pytest.mark.regression
def test_list_links_filter_by_query(client, api_headers):
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("findme"), headers=api_headers)
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("other1"), headers=api_headers)

    response = client.get(
        "/api/v1/links",
        params={"query": "findme"},
        headers=api_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "findme"


@allure.epic("URL Shortener")
@allure.feature("Links API Filters")
@allure.story("Filter links by blocked flag")
@pytest.mark.api
@pytest.mark.regression
def test_list_links_filter_by_blocked(client, api_headers):
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("block1"), headers=api_headers)
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("block2"), headers=api_headers)

    login_response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert login_response.status_code == 303

    toggle_response = client.post(
        "/admin/links/block1/toggle",
        follow_redirects=False,
    )
    assert toggle_response.status_code == 303

    response = client.get(
        "/api/v1/links",
        params={"blocked": True},
        headers=api_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["code"] == "block1"


@allure.epic("URL Shortener")
@allure.feature("Links API Filters")
@allure.story("Export links to CSV")
@pytest.mark.api
@pytest.mark.regression
def test_export_links_csv(client, api_headers):
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("csv01"), headers=api_headers)
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("csv02"), headers=api_headers)

    response = client.get("/api/v1/links/export", headers=api_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == "attachment; filename=links.csv"

    body = response.text
    assert "code,target_url,clicks,is_blocked,expires_at,max_clicks,is_expired" in body
    assert "csv01" in body
    assert "csv02" in body


@allure.epic("URL Shortener")
@allure.feature("Links API Filters")
@allure.story("Include deleted links in list")
@pytest.mark.api
@pytest.mark.regression
def test_list_links_can_include_deleted(client, api_headers):
    client.post("/api/v1/links", json=LinkBuilder.with_custom_code("del002"), headers=api_headers)
    client.delete("/api/v1/links/del002", headers=api_headers)

    hidden_response = client.get("/api/v1/links", headers=api_headers)
    assert hidden_response.status_code == 200
    assert all(item["code"] != "del002" for item in hidden_response.json()["items"])

    shown_response = client.get(
        "/api/v1/links",
        params={"include_deleted": True},
        headers=api_headers,
    )
    assert shown_response.status_code == 200
    assert any(
        item["code"] == "del002" and item["is_deleted"] is True
        for item in shown_response.json()["items"]
    )