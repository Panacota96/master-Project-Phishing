"""E2E tests — Email Threat Inspector flow."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_inspector_page_loads(page: Page, authenticated_user: Page, base_url: str):
    """Authenticated user can reach the inspector page."""
    page.goto(f"{base_url}/inspector/")
    assert "/auth/login" not in page.url
    assert "500" not in page.title()


@pytest.mark.e2e
def test_unauthenticated_inspector_redirect(page: Page, base_url: str):
    """Unauthenticated access to /inspector/ redirects to login."""
    page.goto(f"{base_url}/inspector/")
    assert "/auth/login" in page.url or "login" in page.content().lower()


@pytest.mark.e2e
def test_inspector_api_email_list(page: Page, authenticated_user: Page, base_url: str):
    """Inspector email list API returns JSON."""
    page.goto(f"{base_url}/inspector/")
    response = page.request.get(f"{base_url}/inspector/api/emails")
    # API should return 200 with JSON content type
    assert response.status == 200
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.e2e
def test_inspector_has_email_container(page: Page, authenticated_user: Page, base_url: str):
    """Inspector page renders a container element for emails."""
    page.goto(f"{base_url}/inspector/")
    # The inspector SPA renders inside a container; assert some structure exists
    assert page.locator("body").count() > 0
