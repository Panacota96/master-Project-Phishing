from playwright.sync_api import Page, expect


def test_quiz_complete_flow(page: Page, e2e_base_url: str, e2e_seed_quiz, login_user):
    login_user()

    page.goto(f"{e2e_base_url}/quiz/")
    page.get_by_role("link", name="Start Module").click()
    expect(page).to_have_url(f"{e2e_base_url}/quiz/quiz-test/video")

    # Mark video as watched to unlock the quiz.
    page.evaluate("() => fetch('/quiz/quiz-test/video-watched', {method: 'POST'})")
    page.goto(f"{e2e_base_url}/quiz/quiz-test/start")

    # Two questions in the seeded quiz
    for _ in range(2):
        expect(page.locator("input[name='answer']")).to_be_visible()
        page.locator("input[name='answer']").first.check()
        page.get_by_role("button", name="Submit").click()
        if page.get_by_role("link", name="Next Question").is_visible():
            page.get_by_role("link", name="Next Question").click()

    expect(page.get_by_text("Quiz Complete!")).to_be_visible()
