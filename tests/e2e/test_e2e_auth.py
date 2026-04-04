import re

from playwright.sync_api import Page, expect


def test_local_login_success(page: Page, e2e_base_url: str, e2e_seed_user, e2e_seed_quiz):
    page.goto(f"{e2e_base_url}/auth/login")
    page.fill("input[name='username']", "testuser")
    page.fill("input[name='password']", "password123")
    page.click("button[type='submit']")

    expect(page).to_have_url(re.compile(r"/quiz/?$"))
    expect(page.get_by_role("heading", name="Training Modules")).to_be_visible()


def test_sso_login_button_visible(page: Page, e2e_base_url: str):
    page.goto(f"{e2e_base_url}/auth/login")
    expect(page.locator("a[href*='/auth/sso/login']")).to_be_visible()


def test_login_failure(page: Page, e2e_base_url: str, e2e_seed_user):
    page.goto(f"{e2e_base_url}/auth/login")
    page.fill("input[name='username']", "wronguser")
    page.fill("input[name='password']", "WrongPass!")
    page.click("button[type='submit']")

    expect(page.locator("text=Invalid username or password.")).to_be_visible()
