from playwright.sync_api import sync_playwright

def verify_dashboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to dashboard
        page.goto("http://127.0.0.1:5000")

        # Check that 'sites' is NOT present
        # We look for project-name 'sites'
        sites_visible = page.locator(".project-name", has_text="sites").count() > 0
        if sites_visible:
            print("FAILURE: 'sites' project is visible!")
        else:
            print("SUCCESS: 'sites' project is hidden.")

        # Check that 'test_verify' IS present
        test_visible = page.locator(".project-name", has_text="test_verify").count() > 0
        if test_visible:
            print("SUCCESS: 'test_verify' project is visible.")
        else:
            print("FAILURE: 'test_verify' project is NOT visible!")

        # Check for Delete button
        # Find the project card for test_verify
        card = page.locator(".project-card").filter(has=page.locator(".project-name", has_text="test_verify"))
        delete_btn = card.locator("button.btn-danger", has_text="Delete")

        if delete_btn.count() > 0:
            print("SUCCESS: Delete button found for 'test_verify'.")
        else:
            print("FAILURE: Delete button NOT found for 'test_verify'.")

        # Take screenshot
        page.screenshot(path="verification.png")
        print("Screenshot saved to verification.png")

        browser.close()

if __name__ == "__main__":
    verify_dashboard()
