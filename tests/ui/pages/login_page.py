from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page

    def open(self, base_url: str):
        self.page.goto(f"{base_url}/admin/login")

    def login(self, username: str, password: str):
        self.page.fill('input[name="username"]', username)
        self.page.fill('input[name="password"]', password)
        self.page.click('button[type="submit"]')

    def body(self) -> str:
        return self.page.locator("body").inner_text()