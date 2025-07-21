import json
import os
from pathlib import Path
from time import sleep

from dotenv import load_dotenv
from loguru import logger
from playwright.sync_api import sync_playwright

STATE_PATH = Path("state/insta_state.json")

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

USER = os.getenv("INSTA_USER")
PASS = os.getenv("INSTA_PASS")
WAIT_SEC = float(os.getenv("WAIT_SEC", "0.5"))


def login() -> None:
    """Log into Instagram and save authenticated state."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US"},
        )
        page = context.new_page()
        logger.info("Logging into Instagram")
        page.goto("https://www.instagram.com/accounts/login/")
        page.fill("input[name=username]", USER)
        page.fill("input[name=password]", PASS)
        page.click("button[type=submit]")
        sleep(WAIT_SEC * 5)
        context.storage_state(path=STATE_PATH)
        logger.info("Saved login state to {}", STATE_PATH)
        browser.close()


def load_context(playwright):
    if not STATE_PATH.exists():
        login()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        locale="en-US",
        extra_http_headers={"Accept-Language": "en-US"},
        storage_state=STATE_PATH,
    )
    return browser, context
