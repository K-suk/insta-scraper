import os
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from scraper.login import login, load_context

@pytest.mark.skipif(not os.getenv('INSTA_USER'), reason='No credentials')
def test_login_playwright():
    from playwright.sync_api import sync_playwright
    login()
    with sync_playwright() as p:
        browser, context = load_context(p)
        assert context is not None
        browser.close()
