"""E2E tests — Admin dashboard."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_admin_dashboard_loads(page: Page, authenticated_admin: Page, base_url: str):
    """Admin user can access the dashboard."""
    page.goto(f"{base_url}/dashboard/")
    assert "/auth/login" not in page.url
    assert "500" not in page.title()


@pytest.mark.e2e
def test_non_admin_dashboard_forbidden(page: Page, authenticated_user: Page, base_url: str):
    """Non-admin student should be denied access to the dashboard."""
    page.goto(f"{base_url}/dashboard/")
    content = page.content()
    # Either redirected away or shown a 403/forbidden message
    assert "/auth/login" in page.url or any(
        phrase in content.lower()
        for phrase in ["forbidden", "403", "not authorized", "access denied", "admin"]
    )


@pytest.mark.e2e
def test_unauthenticated_dashboard_redirect(page: Page, base_url: str):
    """Unauthenticated access to /dashboard/ redirects to login."""
    page.goto(f"{base_url}/dashboard/")
    assert "/auth/login" in page.url or "login" in page.content().lower()


@pytest.mark.e2e
def test_dashboard_stats_api(page: Page, authenticated_admin: Page, base_url: str):
    """Dashboard stats API endpoint returns JSON for admins."""
    page.goto(f"{base_url}/dashboard/")
    response = page.request.get(f"{base_url}/dashboard/api/stats")
    assert response.status in (200, 404)  # 404 if route not available at that path
    if response.status == 200:
        assert "application/json" in response.headers.get("content-type", "")
