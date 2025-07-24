import random
import asyncio
import re
from pathlib import Path
from typing import Dict, List

import pandas as pd
from loguru import logger
from playwright.async_api import async_playwright

from .login import load_context, WAIT_SEC
from .csv_utils import build_dataframe


async def verify_login_status(page):
    """Instagramのログイン状態を確認し、必要に応じて再ログインする"""
    try:
        # まず現在のログイン状態を確認
        logger.info("Checking current login status...")
        await page.goto("https://www.instagram.com/", wait_until="networkidle")
        await asyncio.sleep(WAIT_SEC * 2)
        
        # ログイン状態を確認 - プロフィールアイコンやナビゲーションバーがあるかチェック
        login_indicators = [
            'nav[role="navigation"]',
            'a[href*="/accounts/edit/"]',
            'button[aria-label*="プロフィール"]',
            'button[aria-label*="Profile"]',
            'svg[aria-label*="ホーム"]',
            'svg[aria-label*="Home"]'
        ]
        
        is_logged_in = False
        for indicator in login_indicators:
            try:
                element = await page.wait_for_selector(indicator, timeout=3000)
                if element:
                    is_logged_in = True
                    logger.info("Login verification successful - user is logged in")
                    break
            except:
                continue
        
        if not is_logged_in:
            logger.info("User not logged in, redirecting to login page...")
            await perform_login_flow(page)
        
    except Exception as e:
        logger.error("Error verifying login status: {}", str(e))
        # エラーの場合は念のためログインフローを実行
        await perform_login_flow(page)


async def perform_login_flow(page):
    """明確なログインフローを実行"""
    try:
        logger.info("Navigating to Instagram login page: https://www.instagram.com/accounts/login/")
        await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        await asyncio.sleep(WAIT_SEC * 3)
        
        # ログインフォームが表示されるまで待機
        await page.wait_for_selector('form#loginForm, input[name="username"]', timeout=10000)
        
        # login.pyのlogin関数の処理を呼び出し
        from .login import USER, PASS
        
        if not USER or not PASS:
            raise ValueError("Instagram credentials not configured in .env file")
        
        # ユーザー名入力フィールドを特定
        logger.info("Filling username...")
        username_selectors = [
            'input[name="username"]',  # 最も確実なセレクター
            'input[aria-label="電話番号、ユーザーネーム、またはメールアドレス"]',
            'input[aria-label="Phone number, username, or email"]',
            'input[aria-label*="電話番号"]',
            'input[aria-label*="username"]',
            'input[aria-label*="email"]',
            'form#loginForm input[type="text"]',
            'input._aa4b._add6._ac4d._ap35[type="text"]'  # クラス名ベースのセレクター
        ]
        
        username_filled = False
        for selector in username_selectors:
            try:
                logger.info("Trying username selector: {}", selector)
                username_field = await page.wait_for_selector(selector, timeout=3000)
                if username_field:
                    # フィールドが表示されているか確認
                    is_visible = await username_field.is_visible()
                    if is_visible:
                        await username_field.click()
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        
                        # フィールドをクリアして入力
                        await username_field.fill("")  # より確実なクリア方法
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        await username_field.type(USER, delay=50)
                        
                        # 入力内容を確認
                        input_value = await username_field.input_value()
                        if input_value == USER:
                            username_filled = True
                            logger.info("Username filled successfully with selector: {}", selector)
                            break
                        else:
                            logger.warning("Username input verification failed. Expected: {}, Got: {}", USER, input_value)
            except Exception as e:
                logger.debug("Failed with username selector {}: {}", selector, str(e))
                continue
        
        if not username_filled:
            # スクリーンショットを撮ってデバッグ
            await page.screenshot(path="debug_username_field_error.png")
            
            # ページの全てのinput要素を調査
            all_inputs = await page.query_selector_all('input')
            logger.info("Found {} input elements on the page", len(all_inputs))
            
            for i, input_elem in enumerate(all_inputs):
                try:
                    name_attr = await input_elem.get_attribute('name')
                    type_attr = await input_elem.get_attribute('type')
                    aria_label = await input_elem.get_attribute('aria-label')
                    logger.info("Input {}: name={}, type={}, aria-label={}", i, name_attr, type_attr, aria_label)
                except:
                    pass
            
            raise Exception("Could not fill username field")
        
        # パスワード入力フィールドを特定
        logger.info("Filling password...")
        password_selectors = [
            'input[name="password"]',  # 最も確実なセレクター
            'input[aria-label="パスワード"]',
            'input[aria-label="Password"]',
            'input[type="password"]',
            'form#loginForm input[type="password"]',
            'input._aa4b._add6._ac4d._ap35[type="password"]'  # クラス名ベースのセレクター
        ]
        
        password_filled = False
        for selector in password_selectors:
            try:
                logger.info("Trying password selector: {}", selector)
                password_field = await page.wait_for_selector(selector, timeout=3000)
                if password_field:
                    # フィールドが表示されているか確認
                    is_visible = await password_field.is_visible()
                    if is_visible:
                        await password_field.click()
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        
                        # フィールドをクリアして入力
                        await password_field.fill("")  # より確実なクリア方法
                        await asyncio.sleep(WAIT_SEC * 0.5)
                        await password_field.type(PASS, delay=50)
                        
                        # 入力内容を確認（パスワードなので値は確認しない）
                        password_filled = True
                        logger.info("Password filled successfully with selector: {}", selector)
                        break
            except Exception as e:
                logger.debug("Failed with password selector {}: {}", selector, str(e))
                continue
        
        if not password_filled:
            await page.screenshot(path="debug_password_field_error.png")
            raise Exception("Could not fill password field")
        
        # ログインボタンをクリック
        logger.info("Clicking login button...")
        login_button_selectors = [
            'button[type="submit"]',
            'form#loginForm button[type="submit"]',
            'button._aswp._aswr._aswu._asw_._asx2[type="submit"]',  # クラス名ベース
            'button:has-text("ログイン")',
            'button:has-text("Log In")',
            'div:has-text("ログイン") button',
            '[role="button"]:has-text("ログイン")'
        ]
        
        login_clicked = False
        for selector in login_button_selectors:
            try:
                logger.info("Trying login button selector: {}", selector)
                login_button = await page.wait_for_selector(selector, timeout=3000)
                if login_button:
                    is_visible = await login_button.is_visible()
                    is_enabled = await login_button.is_enabled()
                    
                    if is_visible and is_enabled:
                        await login_button.click()
                        login_clicked = True
                        logger.info("Login button clicked successfully with selector: {}", selector)
                        break
                    else:
                        logger.warning("Login button found but not clickable. Visible: {}, Enabled: {}", is_visible, is_enabled)
            except Exception as e:
                logger.debug("Failed with login button selector {}: {}", selector, str(e))
                continue
        
        if not login_clicked:
            # ボタンが無効化されている場合があるので、Enterキーを試す
            try:
                logger.info("Trying Enter key as fallback...")
                await page.keyboard.press('Enter')
                login_clicked = True
                logger.info("Login submitted using Enter key")
            except:
                await page.screenshot(path="debug_login_button_error.png")
                raise Exception("Could not click login button")
        
        # ログイン完了を待つ
        logger.info("Waiting for login to complete...")
        await asyncio.sleep(WAIT_SEC * 5)
        
        # ログイン後の画面処理（通知設定など）
        await handle_post_login_popups(page)
        
        # ログイン成功を確認
        current_url = page.url
        if "instagram.com" in current_url and "login" not in current_url:
            logger.info("Login flow completed successfully! Current URL: {}", current_url)
        else:
            logger.warning("Login may have failed. Current URL: {}", current_url)
            await page.screenshot(path="debug_login_result.png")
        
    except Exception as e:
        logger.error("Error in login flow: {}", str(e))
        await page.screenshot(path="debug_login_flow_error.png")
        raise


async def handle_post_login_popups(page):
    """ログイン後のポップアップやダイアログを処理"""
    try:
        # よくある後処理ボタン
        skip_selectors = [
            'button:has-text("今はしない")',
            'button:has-text("Not Now")',
            'button:has-text("後で")',
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
                    logger.info("Handled post-login popup")
            except:
                continue
                
    except Exception as e:
        logger.debug("Error handling post-login popups: {}", str(e))


async def navigate_to_user_reels(page, username: str):
    """指定したユーザーのリールページに遷移"""
    reels_url = f"https://www.instagram.com/{username}/reels/"
    logger.info("Navigating to user reels page: {}", reels_url)
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info("Navigation attempt {}/{} to {}", attempt + 1, max_retries, reels_url)
            
            # より緩い条件でページ読み込みを試行
            try:
                await page.goto(reels_url, wait_until="domcontentloaded", timeout=15000)
                logger.info("Page loaded with domcontentloaded")
            except Exception as domload_error:
                logger.warning("domcontentloaded failed: {}, trying with load", str(domload_error))
                try:
                    await page.goto(reels_url, wait_until="load", timeout=20000)
                    logger.info("Page loaded with load")
                except Exception as load_error:
                    logger.warning("load failed: {}, trying without wait condition", str(load_error))
                    await page.goto(reels_url, timeout=25000)
                    logger.info("Page loaded without wait condition")
            
            # ページ読み込み後の追加待機
            await asyncio.sleep(WAIT_SEC * 2)
            
            # リールが実際に存在するかチェック
            reel_indicators = [
                'a[href*="/reel/"]',
                'article',
                'div[role="main"]',
                'main'
            ]
            
            reel_found = False
            for indicator in reel_indicators:
                try:
                    await page.wait_for_selector(indicator, timeout=5000)
                    reel_found = True
                    logger.info("Found reel indicator: {}", indicator)
                    break
                except:
                    continue
            
            if not reel_found:
                logger.warning("No reel indicators found, but page loaded")
            
            # ページ読み込み完了確認
            current_url = page.url
            if username in current_url:
                logger.info("Successfully navigated to {}'s reels page (attempt {})", username, attempt + 1)
                
                # 追加の安定化待機
                await asyncio.sleep(WAIT_SEC * 2)
                return
            else:
                logger.warning("Navigation may have failed. Current URL: {} (attempt {})", current_url, attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(WAIT_SEC * 2)
                    continue
                    
        except Exception as e:
            logger.error("Navigation attempt {} failed: {}", attempt + 1, str(e))
            if attempt < max_retries - 1:
                logger.info("Retrying navigation after {} seconds...", WAIT_SEC * 3)
                await asyncio.sleep(WAIT_SEC * 3)
                continue
            else:
                logger.error("All navigation attempts failed for user: {}", username)
                raise


async def navigate_to_hashtag_reels(page, hashtag: str):
    """指定したハッシュタグのリールページに遷移"""
    hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
    logger.info("Navigating to hashtag page: {}", hashtag_url)
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            logger.info("Hashtag navigation attempt {}/{} to {}", attempt + 1, max_retries, hashtag_url)
            
            # より緩い条件でページ読み込みを試行
            try:
                await page.goto(hashtag_url, wait_until="domcontentloaded", timeout=15000)
                logger.info("Hashtag page loaded with domcontentloaded")
            except Exception as domload_error:
                logger.warning("domcontentloaded failed for hashtag: {}, trying with load", str(domload_error))
                try:
                    await page.goto(hashtag_url, wait_until="load", timeout=20000)
                    logger.info("Hashtag page loaded with load")
                except Exception as load_error:
                    logger.warning("load failed for hashtag: {}, trying without wait condition", str(load_error))
                    await page.goto(hashtag_url, timeout=25000)
                    logger.info("Hashtag page loaded without wait condition")
            
            # ページ読み込み後の追加待機
            await asyncio.sleep(WAIT_SEC * 2)
            
            # ハッシュタグページの要素確認
            hashtag_indicators = [
                'article',
                'div[role="main"]',
                'main',
                'span:has-text("リール")',
                'span:has-text("Reels")'
            ]
            
            element_found = False
            for indicator in hashtag_indicators:
                try:
                    await page.wait_for_selector(indicator, timeout=5000)
                    element_found = True
                    logger.info("Found hashtag page indicator: {}", indicator)
                    break
                except:
                    continue
            
            if not element_found:
                logger.warning("No hashtag page indicators found, but page loaded")
            
            # リールタブをクリック
            reels_tab_selectors = [
                'a[href*="/reels/"]',
                'span:has-text("リール")',
                'span:has-text("Reels")',
                'a:has-text("リール")',
                'a:has-text("Reels")'
            ]
            
            tab_clicked = False
            for selector in reels_tab_selectors:
                try:
                    reels_tab = await page.wait_for_selector(selector, timeout=5000)
                    if reels_tab:
                        await reels_tab.click()
                        await asyncio.sleep(WAIT_SEC * 2)
                        logger.info("Clicked reels tab for hashtag #{}", hashtag)
                        tab_clicked = True
                        break
                except Exception as tab_error:
                    logger.debug("Failed to click tab with selector {}: {}", selector, str(tab_error))
                    continue
            
            if not tab_clicked:
                logger.warning("Could not find or click reels tab for hashtag #{}", hashtag)
            
            # 成功確認
            current_url = page.url
            if hashtag in current_url:
                logger.info("Successfully navigated to hashtag #{} page (attempt {})", hashtag, attempt + 1)
                await asyncio.sleep(WAIT_SEC * 2)
                return
            else:
                logger.warning("Hashtag navigation may have failed. Current URL: {} (attempt {})", current_url, attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(WAIT_SEC * 2)
                    continue
        
        except Exception as e:
            logger.error("Hashtag navigation attempt {} failed: {}", attempt + 1, str(e))
            if attempt < max_retries - 1:
                logger.info("Retrying hashtag navigation after {} seconds...", WAIT_SEC * 3)
                await asyncio.sleep(WAIT_SEC * 3)
                continue
            else:
                logger.error("All hashtag navigation attempts failed for #{}", hashtag)
                raise


async def scrape_user_reels_from_page(page, username: str, max_items: int, columns: List[str]) -> List[Dict]:
    """現在のページからユーザーのリールをスクレイピング"""
    logger.info("Starting scraping process for user: {}", username)
    results = []
    
    try:
        # 最初のリールをクリック（画像で指示された左上のリール）
        first_reel_selectors = [
            # 提供されたHTMLに基づく最も具体的なセレクター
            'a.x1i10hfl.xjbqb8w.x1ejq31n[href*="/reel/"]:first-of-type',
            'a[class*="x1i10hfl"][href*="/reel/"]:first-of-type',
            'a[class*="_a6hd"][href*="/reel/"]:first-of-type',
            # リールグリッド内の最初の要素
            'div._ac7v a[href*="/reel/"]:first-of-type',
            'div[class*="x1qjc9v5"] a[href*="/reel/"]:first-of-type',
            'div[class*="x1qjc9v5"] div[class*="x2fvf9"] a[href*="/reel/"]:first-of-type',
            # 一般的なリールリンクセレクター
            'a[href*="/reel/"]:first-of-type',
            'article a[href*="/reel/"]:first-of-type',
            # より広範囲な検索：任意のリールリンク
            'a[href*="/reel/"]',
            'div[role="button"] a[href*="/reel/"]'
        ]
        
        first_reel = None
        reel_count = 0
        
        # まずページ上のリール数を確認
        try:
            all_reels = await page.query_selector_all('a[href*="/reel/"]')
            reel_count = len(all_reels)
            logger.info("Found {} reel links on the page", reel_count)
        except Exception as e:
            logger.warning("Could not count reels: {}", str(e))
        
        if reel_count == 0:
            logger.error("No reel links found on the page for user: {}", username)
            return results
        
        # 最初のリールを特定してクリック
        for i, selector in enumerate(first_reel_selectors):
            try:
                logger.info("Trying selector {}: {}", i + 1, selector)
                first_reel = await page.wait_for_selector(selector, timeout=5000)
                if first_reel:
                    # 要素が表示されているか確認
                    is_visible = await first_reel.is_visible()
                    is_enabled = await first_reel.is_enabled()
                    
                    if is_visible and is_enabled:
                        # リールのhrefを取得してログ出力
                        href = await first_reel.get_attribute('href')
                        logger.info("Found first reel with selector: {} (href: {})", selector, href)
                        break
                    else:
                        logger.warning("Reel element found but not clickable (visible: {}, enabled: {})", is_visible, is_enabled)
                        first_reel = None
            except Exception as e:
                logger.debug("Selector {} failed: {}", selector, str(e))
                continue
        
        if not first_reel:
            logger.error("Could not find clickable first reel for user: {}", username)
            # デバッグ用：スクリーンショットを保存
            try:
                screenshot_path = f"debug_reel_list_{username}.png"
                await page.screenshot(path=screenshot_path)
                logger.info("Saved debug screenshot: {}", screenshot_path)
            except:
                pass
            return results
        
        # リールをクリック
        try:
            logger.info("Clicking first reel...")
            
            # 通常のクリックを試行
            try:
                await first_reel.click()
                await asyncio.sleep(WAIT_SEC * 2)
                
                # クリック後のURL確認
                current_url = page.url
                if "/reel/" in current_url:
                    logger.info("Successfully navigated to reel detail page via normal click: {}", current_url)
                else:
                    raise Exception("Normal click did not navigate to reel page")
                    
            except Exception as normal_click_error:
                logger.warning("Normal click failed: {}, trying JavaScript click", str(normal_click_error))
                
                # JavaScriptによる強制クリック
                try:
                    href = await first_reel.get_attribute('href')
                    if href:
                        # JavaScriptで直接要素をクリック
                        await page.evaluate('(element) => element.click()', first_reel)
                        await asyncio.sleep(WAIT_SEC * 2)
                        
                        current_url = page.url
                        if "/reel/" in current_url:
                            logger.info("Successfully navigated to reel detail page via JavaScript click: {}", current_url)
                        else:
                            # 最後の手段：直接URLに遷移
                            full_url = f"https://www.instagram.com{href}" if href.startswith('/') else href
                            logger.info("Trying direct navigation to: {}", full_url)
                            await page.goto(full_url, wait_until="networkidle")
                            await asyncio.sleep(WAIT_SEC * 3)
                            
                            current_url = page.url
                            if "/reel/" in current_url:
                                logger.info("Successfully navigated to reel detail page via direct URL: {}", current_url)
                            else:
                                raise Exception("All click methods failed")
                    else:
                        raise Exception("Could not get href attribute")
                        
                except Exception as js_click_error:
                    logger.error("JavaScript click also failed: {}", str(js_click_error))
                    raise js_click_error
            
            await asyncio.sleep(WAIT_SEC * 2)  # 追加の待機時間
                
        except Exception as e:
            logger.error("All click methods failed for first reel: {}", str(e))
            # デバッグ用スクリーンショット
            try:
                screenshot_path = f"debug_click_failed_{username}.png"
                await page.screenshot(path=screenshot_path)
                logger.info("Saved debug screenshot after click failure: {}", screenshot_path)
            except:
                pass
            return results
        
        # 各リールから情報を取得
        for i in range(max_items):
            logger.info("Scraping reel {}/{} for user {}", i + 1, max_items, username)
            
            reel_data = await scrape_reel_details(page, username, columns)
            if reel_data:
                results.append(reel_data)
                logger.info("Successfully scraped reel {} data", i + 1)
            
            # 最後のリールでない場合は次に移動
            if i < max_items - 1:
                if not await navigate_to_next_reel(page):
                    logger.warning("Could not navigate to next reel, stopping at reel {}", i + 1)
                    break
            
            await asyncio.sleep(random.uniform(WAIT_SEC, WAIT_SEC * 2))
        
        logger.info("Completed scraping user {}: {} reels collected", username, len(results))
        
    except Exception as e:
        logger.error("Error scraping user reels: {}", str(e))
    
    return results


async def scrape_hashtag_reels_from_page(page, hashtag: str, max_items: int, columns: List[str]) -> List[Dict]:
    """現在のページからハッシュタグのリールをスクレイピング"""
    logger.info("Starting scraping process for hashtag: #{}", hashtag)
    results = []
    
    try:
        # ハッシュタグページでの処理は基本的にユーザーページと同じ
        return await scrape_user_reels_from_page(page, f"#{hashtag}", max_items, columns)
        
    except Exception as e:
        logger.error("Error scraping hashtag reels: {}", str(e))
        return results


async def navigate_to_next_reel(page) -> bool:
    """次のリールに移動する"""
    try:
        # 複数の次へボタンセレクターを試す
        next_selectors = [
            'button[aria-label="Next"], button[aria-label="次へ"]',
            'svg[aria-label="Next"], svg[aria-label="次へ"]',
            'button:has(svg[aria-label="Next"]), button:has(svg[aria-label="次へ"])',
            'div[role="button"]:has(svg[aria-label="Next"])',
            'div[role="button"]:has(svg[aria-label="次へ"])',
            # 右矢印のアイコンを探す
            'button svg[viewBox*="24"][d*="m15.5"]',
            'div[role="button"] svg[viewBox*="24"][d*="m15.5"]'
        ]
        
        for selector in next_selectors:
            try:
                next_button = await page.wait_for_selector(selector, timeout=3000)
                if next_button:
                    await next_button.click()
                    await asyncio.sleep(WAIT_SEC * 2)
                    return True
            except:
                continue
        
        # キーボードショートカットも試す
        try:
            await page.keyboard.press('ArrowRight')
            await asyncio.sleep(WAIT_SEC * 2)
            return True
        except:
            pass
            
        return False
        
    except Exception as e:
        logger.debug("Error navigating to next reel: {}", str(e))
        return False


async def scrape_reel_details(page, source: str, columns: List[str]) -> Dict:
    """現在表示されているリールの詳細情報を取得"""
    try:
        # ページが完全に読み込まれるまで待機
        await asyncio.sleep(WAIT_SEC * 2)
        
        # 現在のURLを取得
        current_url = page.url
        
        # キャプションを取得
        caption = ""
        try:
            # より具体的なキャプションセレクター
            caption_selectors = [
                'div[data-testid="post-caption"] span',
                'article div[role="button"] span',
                'div[dir="auto"] span',
                'h1 + div span',
                'span[style*="word-wrap"]'
            ]
            
            for selector in caption_selectors:
                try:
                    caption_elements = await page.query_selector_all(selector)
                    for element in caption_elements:
                        text = await element.text_content()
                        if text and len(text.strip()) > 20:  # 十分な長さのテキスト
                            caption = text.strip()
                            break
                    if caption:
                        break
                except:
                    continue
        except Exception as e:
            logger.debug("Could not find caption: {}", str(e))
        
        # いいね数を取得
        likes = ""
        if "likes" in columns:
            try:
                # いいねボタンやテキストを探す
                likes_selectors = [
                    'button[aria-label*="いいね"] span',
                    'button[aria-label*="like"] span', 
                    'section[role="tablist"] + div button span',
                    'svg[aria-label*="いいね"] + span',
                    'svg[aria-label*="like"] + span'
                ]
                
                for selector in likes_selectors:
                    try:
                        likes_elements = await page.query_selector_all(selector)
                        for element in likes_elements:
                            text = await element.text_content()
                            if text:
                                # 数字を抽出（K、M表記も考慮）
                                likes_match = re.search(r'([\d,]+(?:\.\d+)?[KkMm]?)', text)
                                if likes_match:
                                    likes = likes_match.group(1)
                                    break
                        if likes:
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug("Could not find likes: {}", str(e))
        
        # 動画再生回数を取得
        video_view_count = ""
        if "video_view_count" in columns:
            try:
                view_selectors = [
                    'span:has-text("回再生")',
                    'span:has-text("views")',
                    'div:has-text("回再生")',
                    'div:has-text("views")',
                    'div[role="button"] span:has-text("回")',
                    'div[role="button"] span:has-text("view")'
                ]
                
                for selector in view_selectors:
                    try:
                        view_elements = await page.query_selector_all(selector)
                        for element in view_elements:
                            text = await element.text_content()
                            if text and ("再生" in text or "view" in text):
                                # 数字を抽出（K、M表記も考慮）
                                view_match = re.search(r'([\d,]+(?:\.\d+)?[KkMm]?)', text)
                                if view_match:
                                    video_view_count = view_match.group(1)
                                    break
                        if video_view_count:
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug("Could not find video view count: {}", str(e))
        
        # コメント数を取得
        comments = ""
        if "comments" in columns:
            try:
                comment_selectors = [
                    'button[aria-label*="コメント"] span',
                    'button[aria-label*="comment"] span',
                    'svg[aria-label*="コメント"] + span',
                    'svg[aria-label*="comment"] + span',
                    'section[role="tablist"] + div button:nth-child(2) span'
                ]
                
                for selector in comment_selectors:
                    try:
                        comment_elements = await page.query_selector_all(selector)
                        for element in comment_elements:
                            text = await element.text_content()
                            if text:
                                # 数字を抽出（K、M表記も考慮）
                                comment_match = re.search(r'([\d,]+(?:\.\d+)?[KkMm]?)', text)
                                if comment_match:
                                    comments = comment_match.group(1)
                                    break
                        if comments:
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug("Could not find comments: {}", str(e))
        
        # 投稿時間を取得
        posted_at = ""
        try:
            time_elements = await page.query_selector_all('time')
            for element in time_elements:
                datetime_attr = await element.get_attribute('datetime')
                title_attr = await element.get_attribute('title')
                if datetime_attr:
                    posted_at = datetime_attr
                    break
                elif title_attr:
                    posted_at = title_attr
                    break
        except Exception as e:
            logger.debug("Could not find posted time: {}", str(e))
        
        reel_data = {
            "url": current_url,
            "title": source,
            "caption": caption,
            "posted_at": posted_at
        }
        
        # 選択されたカラムのみ追加
        if "likes" in columns:
            reel_data["likes"] = likes
        if "comments" in columns:
            reel_data["comments"] = comments
        if "video_view_count" in columns:
            reel_data["video_view_count"] = video_view_count
        
        logger.info("Scraped reel data: URL={}, Likes={}, Views={}, Comments={}, Caption preview={}", 
                   current_url, likes, video_view_count, comments, caption[:50] + "..." if len(caption) > 50 else caption)
        
        return reel_data
        
    except Exception as e:
        logger.error("Error scraping reel details: {}", str(e))
        return None


async def scrape_job(job_id: str, usernames: List[str], hashtags: List[str], max_items: int, columns: List[str], progress: Dict[str, Dict]):
    """Instagram リールスクレイピングジョブ - 明確なプロセスで実行"""
    logger.info("Starting scrape job {}", job_id)
    progress[job_id] = {"progress": 0, "status": "running"}

    results = []
    total_tasks = len(usernames) + len(hashtags)
    completed_tasks = 0

    async with async_playwright() as p:
        browser, context = await load_context(p)
        page = await context.new_page()
        
        try:
            # Step 1: Instagramログインの確認・実行
            logger.info("Step 1: Verifying Instagram login status...")
            await verify_login_status(page)
            
            # Step 2: ユーザーのリールを取得
            for username in usernames:
                logger.info("Step 2: Starting to scrape user: {}", username)
                
                # 明確にユーザーのリールページに遷移
                await navigate_to_user_reels(page, username)
                
                # スクレイピング開始
                user_results = await scrape_user_reels_from_page(page, username, max_items, columns)
                results.extend(user_results)
                
                completed_tasks += 1
                progress[job_id]["progress"] = int(100 * completed_tasks / total_tasks)
                logger.info("Completed user {}, progress: {}%", username, progress[job_id]["progress"])

            # Step 3: ハッシュタグのリールを取得
            for hashtag in hashtags:
                logger.info("Step 3: Starting to scrape hashtag: #{}", hashtag)
                
                # ハッシュタグページに遷移
                await navigate_to_hashtag_reels(page, hashtag)
                
                # スクレイピング開始
                hashtag_results = await scrape_hashtag_reels_from_page(page, hashtag, max_items, columns)
                results.extend(hashtag_results)
                
                completed_tasks += 1
                progress[job_id]["progress"] = int(100 * completed_tasks / total_tasks)
                logger.info("Completed hashtag #{}, progress: {}%", hashtag, progress[job_id]["progress"])
                
        except Exception as e:
            logger.error("Error during scraping: {}", str(e))
        finally:
            await browser.close()

    # 結果をCSVに保存
    if results:
        df = build_dataframe(results, columns)
        # 現在のファイルの親ディレクトリを基準にしたパスを使用
        current_file = Path(__file__).resolve()
        backend_root = current_file.parent.parent  # scraper/ から backend/ へ
        out_dir = backend_root / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = out_dir / f"{job_id}.csv"
        df.to_csv(csv_path, index=False)
        progress[job_id].update({"status": "done", "path": str(csv_path)})
        logger.info("Job {} complete. CSV saved to: {} with {} results", job_id, csv_path, len(results))
    else:
        progress[job_id].update({"status": "error", "message": "No results found"})
        logger.warning("Job {} completed but no results found", job_id) 