from playwright.sync_api import Page, expect


def test_admin_dashboard_loads(page: Page, e2e_base_url: str, login_admin):
    login_admin()
    page.goto(f"{e2e_base_url}/dashboard/")
    expect(page.locator(".stat-card").first).to_be_visible()


def test_threat_feed_renders(page: Page, e2e_base_url: str, login_admin):
    login_admin()
    page.goto(f"{e2e_base_url}/dashboard/")
    expect(page.locator("li.threat-feed-item").first).to_be_visible(timeout=5000)
