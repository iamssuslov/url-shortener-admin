from playwright.sync_api import Page


class AdminLinksPage:
    def __init__(self, page: Page):
        self.page = page

    def row(self, code: str):
        return self.page.locator("tr", has=self.page.locator(f"text={code}"))

    def row_by_code(self, code: str):
        return self.row(code)

    def block(self, code: str):
        self.row(code).locator("button", has_text="Block").click()

    def delete(self, code: str):
        self.row(code).locator("button", has_text="Delete").click()

    def block_link(self, code: str):
        self.block(code)

    def delete_link(self, code: str):
        self.delete(code)

    def open_details(self, code: str):
        self.page.click(f'a[href="/admin/links/{code}"]')

    def body(self) -> str:
        return self.page.locator("body").inner_text()

    def body_text(self) -> str:
        return self.body()

    def set_page_size(self, value: str):
        self.page.select_option('select[name="page_size"]', value)

    def apply(self):
        self.page.click("text=Apply")

    def apply_filters(self):
        self.apply()