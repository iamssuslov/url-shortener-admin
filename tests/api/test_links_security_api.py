import allure
import pytest

from tests.builders.link_builder import LinkBuilder


@allure.epic("URL Shortener")
@allure.feature("Links API Security")
@allure.story("API key is required")
@pytest.mark.api
@pytest.mark.smoke
def test_api_requires_key(client):
    payload = LinkBuilder.create_payload()

    response = client.post("/api/v1/links", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"


@allure.epic("URL Shortener")
@allure.feature("Links API Security")
@allure.story("Inactive API key is forbidden")
@pytest.mark.api
@pytest.mark.regression
def test_inactive_api_key_returns_403(client, inactive_api_headers):
    payload = LinkBuilder.create_payload()

    response = client.post(
        "/api/v1/links",
        json=payload,
        headers=inactive_api_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is inactive"


@allure.epic("URL Shortener")
@allure.feature("Links API Security")
@allure.story("Rate limit protects link creation")
@pytest.mark.api
@pytest.mark.regression
def test_rate_limit_returns_429_after_too_many_creates(client, api_headers):
    statuses = []

    for i in range(11):
        payload = LinkBuilder.with_custom_code(f"rlim{i:02d}")
        payload["target_url"] = f"https://example{i}.com"

        response = client.post(
            "/api/v1/links",
            json=payload,
            headers=api_headers,
        )
        statuses.append(response.status_code)

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429