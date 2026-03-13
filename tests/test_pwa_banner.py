"""
PWA Smart App Banner Testing
Tests mobile user agent detection, localStorage persistence, and banner visibility
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://lost-data-fix.preview.emergentagent.com')
TEST_EMAIL = 'kmklodnicki@gmail.com'
TEST_PASSWORD = 'HoneyGroove2026!'

# User Agents for testing
IOS_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
DESKTOP_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

async def login(page):
    """Helper to log in"""
    await page.goto(f'{BASE_URL}/login')
    await page.wait_for_load_state('networkidle')
    await page.wait_for_timeout(1000)
    
    # Fill credentials
    email_input = await page.query_selector('input[placeholder*="example.com"]')
    if email_input:
        await email_input.fill(TEST_EMAIL)
    
    password_input = await page.query_selector('input[type="password"]')
    if password_input:
        await password_input.fill(TEST_PASSWORD)
    
    # Submit
    sign_in_btn = await page.query_selector('button:has-text("Sign In")')
    if sign_in_btn:
        await sign_in_btn.click()
    
    await page.wait_for_timeout(3000)
    return '/hive' in page.url

async def test_ios_banner():
    """Test banner appears on iOS with 'How?' button and iOS guide"""
    print("\n" + "="*60)
    print("TEST: iOS Mobile Banner")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=IOS_USER_AGENT,
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        try:
            # Clear localStorage and login
            await page.goto(f'{BASE_URL}/login')
            await page.wait_for_load_state('networkidle')
            await page.evaluate("localStorage.removeItem('pwa_installed')")
            
            logged_in = await login(page)
            if not logged_in:
                print("❌ Failed to login")
                return False
            
            print("✅ Logged in successfully")
            await page.wait_for_timeout(1500)
            
            # Check for banner
            banner = await page.query_selector('[data-testid="pwa-install-banner"]')
            if not banner:
                print("❌ Banner NOT found on iOS mobile")
                await page.screenshot(path='/app/.screenshots/ios_no_banner.png')
                return False
            
            is_visible = await banner.is_visible()
            if not is_visible:
                print("❌ Banner exists but NOT visible on iOS")
                return False
            
            print("✅ Banner is visible on iOS mobile")
            
            # Check button text is "How?" on iOS
            install_btn = await page.query_selector('[data-testid="pwa-install-btn"]')
            if install_btn:
                btn_text = await install_btn.text_content()
                if 'How?' in btn_text:
                    print(f"✅ Button shows 'How?' on iOS (got: '{btn_text}')")
                else:
                    print(f"❌ Expected 'How?' button, got: '{btn_text}'")
                    return False
                
                # Click to show iOS guide
                await install_btn.click()
                await page.wait_for_timeout(500)
                
                ios_guide = await page.query_selector('[data-testid="pwa-ios-guide"]')
                if ios_guide:
                    guide_text = await ios_guide.text_content()
                    if 'Share' in guide_text and 'Add to Home Screen' in guide_text:
                        print("✅ iOS guide shows Share and Add to Home Screen instructions")
                    else:
                        print(f"❌ iOS guide missing expected text: {guide_text[:100]}")
                        return False
                    
                    # Check button changed to "Got it"
                    btn_text_after = await install_btn.text_content()
                    if 'Got it' in btn_text_after:
                        print("✅ Button changed to 'Got it' after click")
                    else:
                        print(f"❌ Expected 'Got it', got: '{btn_text_after}'")
                else:
                    print("❌ iOS guide not visible after clicking 'How?'")
                    return False
            
            # Check styling
            styles = await page.evaluate("""() => {
                const banner = document.querySelector('[data-testid="pwa-install-banner"]');
                const inner = banner.querySelector('div');
                const textSpan = banner.querySelector('span');
                const bannerStyle = window.getComputedStyle(banner);
                const innerStyle = window.getComputedStyle(inner);
                const textStyle = textSpan ? window.getComputedStyle(textSpan) : {};
                return {
                    zIndex: bannerStyle.zIndex,
                    position: bannerStyle.position,
                    background: innerStyle.backgroundColor,
                    textColor: textStyle.color
                };
            }""")
            
            print(f"   Styling - z-index: {styles['zIndex']}, position: {styles['position']}")
            print(f"   Background: {styles['background']}, Text: {styles['textColor']}")
            
            if styles['zIndex'] == '9999':
                print("✅ z-index is 9999")
            else:
                print(f"❌ z-index is {styles['zIndex']}, expected 9999")
            
            # Check spacer
            spacer = await page.query_selector('[data-testid="pwa-banner-spacer"]')
            if spacer:
                print("✅ Spacer div is present")
            else:
                print("❌ Spacer div missing")
            
            await page.screenshot(path='/app/.screenshots/ios_banner_test.png')
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await browser.close()

async def test_android_banner():
    """Test banner appears on Android after 2s fallback timer"""
    print("\n" + "="*60)
    print("TEST: Android Mobile Banner (2s fallback)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=ANDROID_USER_AGENT,
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        try:
            # Clear localStorage and login
            await page.goto(f'{BASE_URL}/login')
            await page.wait_for_load_state('networkidle')
            await page.evaluate("localStorage.removeItem('pwa_installed')")
            
            logged_in = await login(page)
            if not logged_in:
                print("❌ Failed to login")
                return False
            
            print("✅ Logged in successfully")
            
            # Wait for fallback timer (2s + buffer)
            print("   Waiting 3s for Android fallback timer...")
            await page.wait_for_timeout(3000)
            
            # Check for banner
            banner = await page.query_selector('[data-testid="pwa-install-banner"]')
            if not banner:
                print("❌ Banner NOT found on Android after fallback")
                await page.screenshot(path='/app/.screenshots/android_no_banner.png')
                return False
            
            is_visible = await banner.is_visible()
            if not is_visible:
                print("❌ Banner exists but NOT visible on Android")
                return False
            
            print("✅ Banner visible on Android after fallback timer")
            
            # Check button text is "Install" on Android
            install_btn = await page.query_selector('[data-testid="pwa-install-btn"]')
            if install_btn:
                btn_text = await install_btn.text_content()
                if 'Install' in btn_text:
                    print(f"✅ Button shows 'Install' on Android (got: '{btn_text}')")
                else:
                    print(f"❌ Expected 'Install' button, got: '{btn_text}'")
            
            await page.screenshot(path='/app/.screenshots/android_banner_test.png')
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await browser.close()

async def test_desktop_no_banner():
    """Test banner does NOT appear on desktop"""
    print("\n" + "="*60)
    print("TEST: Desktop - No Banner")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=DESKTOP_USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Clear localStorage and login
            await page.goto(f'{BASE_URL}/login')
            await page.wait_for_load_state('networkidle')
            await page.evaluate("localStorage.removeItem('pwa_installed')")
            
            logged_in = await login(page)
            if not logged_in:
                print("❌ Failed to login")
                return False
            
            print("✅ Logged in successfully")
            await page.wait_for_timeout(3000)  # Wait longer than any fallback
            
            # Check for banner
            banner = await page.query_selector('[data-testid="pwa-install-banner"]')
            if banner:
                is_visible = await banner.is_visible()
                if is_visible:
                    print("❌ Banner is VISIBLE on desktop (should NOT show)")
                    await page.screenshot(path='/app/.screenshots/desktop_banner_error.png')
                    return False
                else:
                    print("✅ Banner element exists but hidden on desktop")
            else:
                print("✅ Banner NOT in DOM on desktop (correct)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await browser.close()

async def test_localstorage_persistence():
    """Test banner hides when pwa_installed=true in localStorage"""
    print("\n" + "="*60)
    print("TEST: localStorage Persistence")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=IOS_USER_AGENT,
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        try:
            # Login first with cleared storage
            await page.goto(f'{BASE_URL}/login')
            await page.wait_for_load_state('networkidle')
            await page.evaluate("localStorage.removeItem('pwa_installed')")
            
            logged_in = await login(page)
            if not logged_in:
                print("❌ Failed to login")
                return False
            
            print("✅ Logged in successfully")
            
            # Now set pwa_installed and reload
            await page.evaluate("localStorage.setItem('pwa_installed', 'true')")
            print("   Set localStorage pwa_installed=true")
            await page.reload()
            await page.wait_for_timeout(2000)
            
            # Check banner is hidden
            banner = await page.query_selector('[data-testid="pwa-install-banner"]')
            if banner:
                is_visible = await banner.is_visible()
                if is_visible:
                    print("❌ Banner still visible with pwa_installed=true")
                    return False
                else:
                    print("✅ Banner hidden when pwa_installed=true")
            else:
                print("✅ Banner not rendered when pwa_installed=true")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await browser.close()

async def test_dismiss_button():
    """Test dismiss button sets localStorage and hides banner"""
    print("\n" + "="*60)
    print("TEST: Dismiss Button (X)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=IOS_USER_AGENT,
            viewport={'width': 390, 'height': 844}
        )
        page = await context.new_page()
        
        try:
            # Clear and login
            await page.goto(f'{BASE_URL}/login')
            await page.wait_for_load_state('networkidle')
            await page.evaluate("localStorage.removeItem('pwa_installed')")
            
            logged_in = await login(page)
            if not logged_in:
                print("❌ Failed to login")
                return False
            
            print("✅ Logged in successfully")
            await page.wait_for_timeout(1500)
            
            # Check banner is visible
            banner = await page.query_selector('[data-testid="pwa-install-banner"]')
            if not banner or not await banner.is_visible():
                print("❌ Banner not visible to test dismiss")
                return False
            
            # Click dismiss
            dismiss_btn = await page.query_selector('[data-testid="pwa-dismiss-btn"]')
            if dismiss_btn:
                await dismiss_btn.click()
                await page.wait_for_timeout(500)
                
                # Check localStorage was set
                ls_value = await page.evaluate("localStorage.getItem('pwa_installed')")
                if ls_value == 'true':
                    print("✅ localStorage pwa_installed set to 'true' after dismiss")
                else:
                    print(f"❌ localStorage value is: {ls_value}, expected 'true'")
                    return False
                
                # Check banner is hidden
                banner_after = await page.query_selector('[data-testid="pwa-install-banner"]')
                if banner_after:
                    is_visible = await banner_after.is_visible()
                    if is_visible:
                        print("❌ Banner still visible after dismiss")
                        return False
                    else:
                        print("✅ Banner hidden after dismiss click")
                else:
                    print("✅ Banner removed from DOM after dismiss")
                
                return True
            else:
                print("❌ Dismiss button not found")
                return False
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await browser.close()

async def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("PWA SMART APP BANNER TEST SUITE")
    print("#"*60)
    
    # Create screenshots directory
    os.makedirs('/app/.screenshots', exist_ok=True)
    
    results = {}
    
    # Run tests
    results['ios_banner'] = await test_ios_banner()
    results['android_banner'] = await test_android_banner()
    results['desktop_no_banner'] = await test_desktop_no_banner()
    results['localstorage_persistence'] = await test_localstorage_persistence()
    results['dismiss_button'] = await test_dismiss_button()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
