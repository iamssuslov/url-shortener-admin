import allure
import pytest

from tests.builders.link_builder import LinkBuilder


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Healthcheck")
@pytest.mark.api
@pytest.mark.smoke
def test_healthcheck_returns_ok(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "x-request-id" in response.headers


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Create short link")
@pytest.mark.api
@pytest.mark.smoke
def test_create_link(client, api_headers):
    payload = LinkBuilder.create_payload()

    response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )

    assert response.status_code == 201
    body = response.json()

    assert "code" in body
    assert body["target_url"] == payload["target_url"]
    assert body["is_expired"] is False
    assert body["is_deleted"] is False
    assert "x-request-id" in response.headers


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Get short link by code")
@pytest.mark.api
@pytest.mark.regression
def test_get_link_by_code(client, api_headers):
    payload = LinkBuilder.with_custom_code("getlink01")

    create_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert create_response.status_code == 201

    response = client.get("/api/v1/links/getlink01", headers=api_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "getlink01"
    assert body["target_url"] == payload["target_url"]


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Create custom code")
@pytest.mark.api
@pytest.mark.regression
def test_create_link_with_custom_code(client, api_headers):
    payload = LinkBuilder.with_custom_code("my_code_1")

    response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )

    assert response.status_code == 201
    assert response.json()["code"] == "my_code_1"


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Reject duplicate custom code")
@pytest.mark.api
@pytest.mark.regression
def test_create_link_with_duplicate_custom_code_returns_409(client, api_headers):
    payload = LinkBuilder.with_custom_code("samecode")

    first_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Custom code already exists"


@allure.epic("URL Shortener")
@allure.feature("Links API")
@allure.story("Reject invalid custom code")
@pytest.mark.api
@pytest.mark.regression
def test_create_link_with_invalid_custom_code_returns_422(client, api_headers):
    payload = {
        "target_url": "https://example.com",
        "custom_code": "bad code !",
    }

    response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )

    assert response.status_code == 422