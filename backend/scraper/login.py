import json
import os
from pathlib import Path
import asyncio

from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright

STATE_PATH = Path("state/insta_state.json")

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

USER = os.getenv("INSTA_USER")
PASS = os.getenv("INSTA_PASS")
WAIT_SEC = float(os.getenv("WAIT_SEC", "1.0"))


async def login() -> None:
    """Log into Instagram and save authenticated state."""
    if not USER or not PASS:
        logger.error("Instagram credentials not found in .env file. Please set INSTA_USER and INSTA_PASS")
        raise ValueError("Instagram credentials not configured")
    
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = await browser.new_context(
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US"},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            logger.info("Navigating to Instagram login page")
            await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
            await asyncio.sleep(WAIT_SEC * 3)
            
            # Cookieバナーを閉じる（存在する場合）
            try:
                cookie_accept = await page.wait_for_selector('button:has-text("Accept"), button:has-text("すべて許可"), button:has-text("Allow")', timeout=3000)
                if cookie_accept:
                    await cookie_accept.click()
                    await asyncio.sleep(WAIT_SEC)
            except:
                pass
            
            # ユーザー名入力フィールドを探して入力
            logger.info("Filling username field")
            username_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[aria-label="電話番号、ユーザーネーム、またはメール"]',
                'input[placeholder*="username"]',
                'input[placeholder*="ユーザーネーム"]',
                'input[autocomplete="username"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    username_field = await page.wait_for_selector(selector, timeout=5000)
                    if username_field:
                        await username_field.click()
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        await username_field.clear()
                        await username_field.type(USER, delay=50)
                        username_filled = True
                        logger.info("Username filled successfully with selector: {}", selector)
                        break
                except:
                    continue
            
            if not username_filled:
                logger.error("Could not find username field")
                await page.screenshot(path="debug_username_error.png")
                raise Exception("Username field not found")
            
            # パスワード入力フィールドを探して入力
            logger.info("Filling password field")
            password_selectors = [
                'input[name="password"]',
                'input[aria-label="Password"]',
                'input[aria-label="パスワード"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_field = await page.wait_for_selector(selector, timeout=5000)
                    if password_field:
                        await password_field.click()
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        await password_field.clear()
                        await password_field.type(PASS, delay=50)
                        password_filled = True
                        logger.info("Password filled successfully with selector: {}", selector)
                        break
                except:
                    continue
            
            if not password_filled:
                logger.error("Could not find password field")
                await page.screenshot(path="debug_password_error.png")
                raise Exception("Password field not found")
            
            await asyncio.sleep(WAIT_SEC)
            
            # ログインボタンを探してクリック
            logger.info("Clicking login button")
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Log In")',
                'button:has-text("ログイン")',
                'div[role="button"]:has-text("Log In")',
                'div[role="button"]:has-text("ログイン")',
                'button[data-testid="loginForm-submit"]'
            ]
            
            login_clicked = False
            for selector in login_button_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        await login_button.click()
                        login_clicked = True
                        logger.info("Login button clicked successfully with selector: {}", selector)
                        break
                except:
                    continue
            
            if not login_clicked:
                logger.error("Could not find login button")
                await page.screenshot(path="debug_login_button_error.png")
                raise Exception("Login button not found")
            
            # ログイン処理の完了を待つ
            logger.info("Waiting for login to complete...")
            await asyncio.sleep(WAIT_SEC * 5)
            
            # 二段階認証やセキュリティチェックをスキップ（存在する場合）
            try:
                skip_selectors = [
                    'button:has-text("今はしない")',
                    'button:has-text("Not Now")',
                    'button:has-text("Skip")',
                    'div[role="button"]:has-text("今はしない")',
                    'div[role="button"]:has-text("Not Now")'
                ]
                
                for selector in skip_selectors:
                    try:
                        skip_button = await page.wait_for_selector(selector, timeout=3000)
                        if skip_button:
                            await skip_button.click()
                            await asyncio.sleep(WAIT_SEC * 2)
                            logger.info("Skipped additional step with selector: {}", selector)
                    except:
                        continue
            except:
                pass
            
            # ログイン成功を確認
            current_url = page.url
            if "instagram.com" in current_url and "login" not in current_url:
                logger.info("Login successful! Current URL: {}", current_url)
                await context.storage_state(path=STATE_PATH)
                logger.info("Saved login state to {}", STATE_PATH)
            else:
                logger.error("Login may have failed. Current URL: {}", current_url)
                await page.screenshot(path="debug_login_failed.png")
                
        except Exception as e:
            logger.error("Error during login: {}", str(e))
            await page.screenshot(path="debug_login_error.png")
            raise
        finally:
            await browser.close()


async def load_context(playwright):
    if not STATE_PATH.exists():
        logger.info("No saved login state found, performing login...")
        await login()
    else:
        logger.info("Using saved login state from {}", STATE_PATH)
    
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-blink-features=AutomationControlled'
        ]
    )
    context = await browser.new_context(
        locale="en-US",
        extra_http_headers={"Accept-Language": "en-US"},
        storage_state=STATE_PATH,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    return browser, context
