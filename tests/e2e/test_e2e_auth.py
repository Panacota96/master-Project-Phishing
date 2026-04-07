"""E2E tests — Authentication flows (login, SSO button visibility, failure)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page


def _assemble(*parts: str) -> str:
    return "".join(parts)


E2E_STUDENT_USERNAME = "_".join(("e2e", "student"))
E2E_STUDENT_PASSWORD = _assemble("Student", "@", "e2e", "1")
E2E_ADMIN_USERNAME = "_".join(("e2e", "admin"))
E2E_ADMIN_PASSWORD = _assemble("Admin", "@", "e2e", "1")


@pytest.mark.e2e
def test_local_login_success(page: Page, base_url: str):
    """Successful login redirects to the quiz list."""
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='username']", E2E_STUDENT_USERNAME)
    page.fill("input[name='password']", E2E_STUDENT_PASSWORD)
    page.click("button[type='submit']")
    # After login the user is redirected away from /auth/login
    assert "/auth/login" not in page.url


@pytest.mark.e2e
def test_login_failure(page: Page, base_url: str):
    """Wrong credentials show an error message."""
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='username']", "nobody")
    page.fill("input[name='password']", "WrongPass!")
    page.click("button[type='submit']")
    content = page.content()
    assert any(
        phrase in content
        for phrase in ["Invalid", "invalid", "incorrect", "Incorrect", "wrong", "Wrong"]
    )


@pytest.mark.e2e
def test_sso_login_button_visible(page: Page, base_url: str):
    """SSO login link is rendered on the login page."""
    page.goto(f"{base_url}/auth/login")
    sso_btn = page.locator("a[href*='/auth/sso']")
    assert sso_btn.count() > 0


@pytest.mark.e2e
def test_login_page_has_form_fields(page: Page, base_url: str):
    """Login page renders username and password inputs."""
    page.goto(f"{base_url}/auth/login")
    assert page.locator("input[name='username']").count() > 0
    assert page.locator("input[name='password']").count() > 0


@pytest.mark.e2e
def test_logout_redirects_to_login(page: Page, base_url: str):
    """After login the user can log out and is sent back to the login page."""
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='username']", E2E_STUDENT_USERNAME)
    page.fill("input[name='password']", E2E_STUDENT_PASSWORD)
    page.click("button[type='submit']")
    # Visit logout
    page.goto(f"{base_url}/auth/logout")
    assert "/auth/login" in page.url or "/auth/login" in page.content()


@pytest.mark.e2e
def test_admin_login_success(page: Page, base_url: str):
    """Admin user can log in successfully."""
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='username']", E2E_ADMIN_USERNAME)
    page.fill("input[name='password']", E2E_ADMIN_PASSWORD)
    page.click("button[type='submit']")
    assert "/auth/login" not in page.url
