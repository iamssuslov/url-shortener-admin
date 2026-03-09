from datetime import datetime, timedelta, UTC

import allure
import pytest

from tests.builders.link_builder import LinkBuilder


@allure.epic("URL Shortener")
@allure.feature("Links Lifecycle")
@allure.story("Redirect increments click counter")
@pytest.mark.api
@pytest.mark.smoke
def test_redirect_increments_clicks(client, api_headers):
    payload = LinkBuilder.create_payload()

    create_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert create_response.status_code == 201
    code = create_response.json()["code"]

    redirect_response = client.get(f"/r/{code}", follow_redirects=False)
    assert redirect_response.status_code == 302

    get_response = client.get(f"/api/v1/links/{code}", headers=api_headers)
    assert get_response.status_code == 200
    assert get_response.json()["clicks"] == 1
    assert get_response.json()["is_expired"] is False


@allure.epic("URL Shortener")
@allure.feature("Links Lifecycle")
@allure.story("Link expires by datetime")
@pytest.mark.api
@pytest.mark.regression
def test_redirect_returns_404_for_expired_link_by_datetime(client, api_headers):
    expires_at = (datetime.now(UTC) - timedelta(minutes=5)).isoformat()
    payload = LinkBuilder.with_expiration("expired1", expires_at)

    create_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert create_response.status_code == 201

    get_response = client.get("/api/v1/links/expired1", headers=api_headers)
    assert get_response.status_code == 200
    assert get_response.json()["is_expired"] is True

    redirect_response = client.get("/r/expired1", follow_redirects=False)
    assert redirect_response.status_code == 404


@allure.epic("URL Shortener")
@allure.feature("Links Lifecycle")
@allure.story("Link expires after max clicks")
@pytest.mark.api
@pytest.mark.regression
def test_redirect_returns_404_after_max_clicks_exhausted(client, api_headers):
    payload = LinkBuilder.with_max_clicks("onceonly", 1)

    create_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert create_response.status_code == 201

    first_redirect = client.get("/r/onceonly", follow_redirects=False)
    second_redirect = client.get("/r/onceonly", follow_redirects=False)

    assert first_redirect.status_code == 302
    assert second_redirect.status_code == 404

    get_response = client.get("/api/v1/links/onceonly", headers=api_headers)
    assert get_response.status_code == 200
    assert get_response.json()["clicks"] == 1
    assert get_response.json()["is_expired"] is True


@allure.epic("URL Shortener")
@allure.feature("Links Lifecycle")
@allure.story("Soft delete hides link from API and redirect")
@pytest.mark.api
@pytest.mark.regression
def test_soft_delete_hides_link_from_api_and_redirect(client, api_headers):
    payload = LinkBuilder.with_custom_code("del001")

    create_response = client.post(
        "/api/v1/links",
        json=payload,
        headers=api_headers,
    )
    assert create_response.status_code == 201

    delete_response = client.delete("/api/v1/links/del001", headers=api_headers)
    assert delete_response.status_code == 204

    get_response = client.get("/api/v1/links/del001", headers=api_headers)
    assert get_response.status_code == 404

    redirect_response = client.get("/r/del001", follow_redirects=False)
    assert redirect_response.status_code == 404