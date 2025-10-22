from playwright.sync_api import sync_playwright
from dotenv import dotenv_values
import os


config = dotenv_values(".env")


username = config.get('ESHARE_USERNAME')
password = config.get("ESHARE_PASSWORD")

print(f"Username loaded: {username is not None}")
print(f"Password loaded: {password is not None}")

def inspect_aspnet_form(page):
    print("Inspecting ASP.NET form values..")

    



with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://a816-health.nyc.gov/eshare/")
    page.wait_for_load_state("networkidle") # Wait until page is fully ready

    # Check if login form appears
    if page.locator('#gigya-loginID').is_visible():
        print("✅ Login form visible - stealth working!")
        
        # Try login
        page.fill('#gigya-loginID', username)
        page.fill('#gigya-password', password)
        page.get_by_role("button", name="Login").click()
        
        # Wait and check result
        page.wait_for_timeout(5000)
        print(f"Final URL: {page.url}")
        
    else:
        print("❌ Login form blocked - bot detection active")

    try:
        page.wait_for_selector("div[content-table]", timeout=5000)
        print("Test Passed: Login successfull!")
    except:
        print("Test Failed: Login unsuccesfull or timeout occured")

    browser.close()