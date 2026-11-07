"""Drives a real Chromium: types the Nepali date in the search box, presses 'खोज्नु होस्', returns the HTML."""
import time

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from . import bsdate
from .config import DATE_INPUT_SELECTOR, NAV_TIMEOUT_MS, SITE_URL, SUBMIT_SELECTOR


class Site:
    def __enter__(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=True)
        self.ctx = self.browser.new_context(
            locale="ne-NP", timezone_id="Asia/Kathmandu", viewport={"width": 1400, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"))
        self.ctx.set_default_timeout(NAV_TIMEOUT_MS)
        self.page = self.ctx.new_page()
        self.open()
        return self

    def __exit__(self, *a):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    def open(self):
        self.page.goto(SITE_URL, wait_until="load", timeout=NAV_TIMEOUT_MS)

    # -- helpers ---------------------------------------------------------------------------
    def _date_input(self):
        sel = DATE_INPUT_SELECTOR or "input[type='text']:visible, input:not([type]):visible"
        loc = self.page.locator(sel).first
        loc.wait_for(state="visible", timeout=30000)
        return loc

    def _submit(self):
        if SUBMIT_SELECTOR:
            return self.page.locator(SUBMIT_SELECTOR).first
        for sel in ("input[type=submit]:visible", "button[type=submit]:visible",
                    "input[value*='खोज्न']:visible", "button:has-text('खोज्न'):visible",
                    "text=खोज्नु होस्"):
            loc = self.page.locator(sel).first
            if loc.count():
                return loc
        raise RuntimeError("search button not found")

    def _set_date(self, value: str):
        inp = self._date_input()
        try:
            inp.fill(value)
        except Exception:
            inp.evaluate("(el, v) => { el.removeAttribute('readonly'); el.value = v; }", value)
        if inp.input_value().strip() != value:
            inp.evaluate("""(el, v) => { el.value = v;
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true})); }""", value)
        return inp

    # -- public ---------------------------------------------------------------------------
    def search(self, iso: str) -> str:
        """Search one BS date (YYYY-MM-DD). Always starts from a freshly loaded page so no state
        (date-picker memory, earlier results) can leak from the previous search."""
        self.open()
        value = bsdate.to_dev(iso)             # the site shows Nepali digits in the box
        inp = self._set_date(value)
        self.typed = inp.input_value().strip()
        # JS click: works even if a pop-up calendar covers the button
        self._submit().evaluate("el => el.click()")
        try:
            self.page.wait_for_load_state("load", timeout=NAV_TIMEOUT_MS)
            self.page.wait_for_load_state("networkidle", timeout=30000)
        except PWTimeout:
            pass
        time.sleep(0.5)
        try:
            self.after = self._date_input().input_value().strip()
        except Exception:
            self.after = ""
        return self.page.content()

    def screenshot(self, path: str):
        self.page.screenshot(path=path, full_page=True)
