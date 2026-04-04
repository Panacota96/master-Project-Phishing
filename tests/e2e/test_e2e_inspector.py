from playwright.sync_api import Page, expect


def test_inspector_submit_phishing(page: Page, e2e_base_url: str, login_user, seed_inspector_samples):
    login_user()

    page.goto(f"{e2e_base_url}/inspector/")
    expect(page.locator(".email-item").first).to_be_visible()
    page.locator(".email-item").first.click()

    form = page.locator("form.classification-form")
    expect(form).to_be_visible()

    form.locator("input[name='classification'][value='Phishing']").check()
    expect(form.locator(".signal-section")).to_be_visible()

    for label in ["Fake Invoice", "Sense of Urgency", "Spoofing"]:
        form.locator(f"label:has-text('{label}') input[type='checkbox']").check()

    form.locator("button.classification-submit").click()
    expect(form.locator(".classification-status.success")).to_be_visible()
