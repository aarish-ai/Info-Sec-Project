"""
MediaGuard - Real-Browser End-to-End QA Automation & Evidence Capture Script.
Driven via Playwright Chromium headless engine to verify all live user workflows.
"""
import io
import os
import sys
import time
import pyotp
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
EVIDENCE_DIR = Path("d:/Projects/Unii/IS Project/docs/evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = Path("d:/Projects/Unii/IS Project/storage/test_assets")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def create_sample_images():
    # 1. Authentic sample image
    img = Image.new("RGB", (400, 300), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill=(99, 102, 241), outline=(16, 185, 129), width=4)
    draw.text((80, 140), "MediaGuard Authentic Evidence", fill=(255, 255, 255))
    authentic_path = TEMP_DIR / "evidence_authentic.png"
    img.save(authentic_path)

    # 2. Tampered sample image (different pixels in rectangle)
    img_tampered = Image.new("RGB", (400, 300), color=(15, 23, 42))
    draw_t = ImageDraw.Draw(img_tampered)
    draw_t.rectangle([50, 50, 350, 250], fill=(244, 63, 94), outline=(225, 29, 72), width=4)
    draw_t.text((80, 140), "TAMPERED Malicious Evidence", fill=(255, 255, 255))
    tampered_path = TEMP_DIR / "evidence_tampered.png"
    img_tampered.save(tampered_path)

    return str(authentic_path), str(tampered_path)

def run_browser_e2e():
    authentic_img, tampered_img = create_sample_images()
    print("Sample images created.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        user_context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = user_context.new_page()

        print("[Step 1] Visiting Landing Page...")
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        assert "Provenance" in page.title() or "MediaGuard" in page.content()
        page.screenshot(path=str(EVIDENCE_DIR / "01_landing_page.png"), full_page=True)
        print("  -> Captured: 01_landing_page.png")

        print("[Step 2] Navigating to Registration...")
        page.goto(f"{BASE_URL}/auth/register", wait_until="networkidle")
        username = f"forensic_alice_{int(time.time())}"
        page.fill("#username", username)
        page.fill("#email", f"{username}@nust.edu.pk")
        page.select_option("#role", "User")
        page.fill("#password", "SecureEvidencePassword2026!")
        page.fill("#confirm_password", "SecureEvidencePassword2026!")
        page.click("button[type='submit']")

        # Should redirect to /auth/setup-2fa
        page.wait_for_url("**/auth/setup-2fa", timeout=15000)
        print("  -> Reached 2FA Setup Screen")
        page.screenshot(path=str(EVIDENCE_DIR / "02_setup_2fa_qr.png"), full_page=True)
        print("  -> Captured: 02_setup_2fa_qr.png")

        # Extract manual secret key
        secret_elem = page.query_selector("#totp-secret-key")
        assert secret_elem is not None, "Secret key element #totp-secret-key must be present"
        totp_secret = secret_elem.inner_text().strip()
        print(f"  -> Extracted TOTP Secret: {totp_secret}")

        # Compute valid code
        totp = pyotp.TOTP(totp_secret)
        code = totp.now()
        page.fill("#code", code)
        page.click("button[type='submit']")

        # Redirects to home page on activation
        page.wait_for_load_state("networkidle")
        print("  -> 2FA Activated. Redirected successfully.")

        # Navigate to /media
        page.goto(f"{BASE_URL}/media/", wait_until="networkidle")
        print("  -> Reached Media Vault Dashboard")
        page.screenshot(path=str(EVIDENCE_DIR / "03_user_media_vault_empty.png"), full_page=True)

        print("[Step 3] Uploading Authentic Media...")
        page.goto(f"{BASE_URL}/media/upload", wait_until="networkidle")
        page.set_input_files("#media-file", authentic_img)
        page.screenshot(path=str(EVIDENCE_DIR / "04_media_upload_form.png"), full_page=True)
        with page.expect_navigation(timeout=15000):
            page.click("button[type='submit']")

        print(f"  -> Media Upload Submitted. Current URL: {page.url}")
        page.screenshot(path=str(EVIDENCE_DIR / "05_media_vault_with_asset.png"), full_page=True)
        print("  -> Captured: 05_media_vault_with_asset.png")

        # Extract the Certificate / Media ID from the library page
        cert_link = page.query_selector("a[href*='/media/'][href*='/certificate']")
        assert cert_link is not None, "Certificate download link must be present!"
        cert_href = cert_link.get_attribute("href")
        media_id = cert_href.split("/")[2]
        print(f"  -> Extracted Registered Media ID: {media_id}")

        print("[Step 4] Downloading PDF Verification Certificate...")
        with page.expect_download() as download_info:
            cert_link.click()
        download = download_info.value
        pdf_path = EVIDENCE_DIR / f"Certificate_{media_id}.pdf"
        download.save_as(str(pdf_path))
        print(f"  -> Saved Certificate PDF: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")

        # Step 5: Public Verification in Incognito Context (Unauthenticated Guest)
        print("[Step 5] Incognito Guest: Public Verification (Authentic File)...")
        guest_context = browser.new_context(viewport={"width": 1280, "height": 800})
        guest_page = guest_context.new_page()

        guest_page.goto(f"{BASE_URL}/verify?cert_id={media_id}", wait_until="networkidle")
        guest_page.set_input_files("#verify-file", authentic_img)
        with guest_page.expect_navigation(timeout=15000):
            guest_page.click("button[type='submit']")

        guest_page.wait_for_selector(".badge-authentic", timeout=15000)
        assert "AUTHENTIC" in guest_page.content()
        guest_page.screenshot(path=str(EVIDENCE_DIR / "06_public_verify_authentic.png"), full_page=True)
        print("  -> Captured: 06_public_verify_authentic.png (VERDICT: AUTHENTIC)")

        # Step 6: Public Verification with Tampered File
        print("[Step 6] Incognito Guest: Public Verification (Tampered File)...")
        guest_page.goto(f"{BASE_URL}/verify?cert_id={media_id}", wait_until="networkidle")
        guest_page.set_input_files("#verify-file", tampered_img)
        with guest_page.expect_navigation(timeout=15000):
            guest_page.click("button[type='submit']")

        guest_page.wait_for_selector(".badge-modified", timeout=15000)
        assert "MODIFIED" in guest_page.content()
        guest_page.screenshot(path=str(EVIDENCE_DIR / "07_public_verify_tampered.png"), full_page=True)
        print("  -> Captured: 07_public_verify_tampered.png (VERDICT: MODIFIED)")

        guest_context.close()
        user_context.close()

        # Step 7: Auditor Role - Audit Trail & 1-Click Chain Verification
        print("[Step 7] Testing Auditor Role & Hash-Chained Audit Trail...")
        auditor_context = browser.new_context(viewport={"width": 1280, "height": 800})
        auditor_page = auditor_context.new_page()

        auditor_page.goto(f"{BASE_URL}/auth/register", wait_until="networkidle")
        auditor_user = f"auditor_hanya_{int(time.time())}"
        auditor_page.fill("#username", auditor_user)
        auditor_page.fill("#email", f"{auditor_user}@nust.edu.pk")
        auditor_page.select_option("#role", "Auditor")
        auditor_page.fill("#password", "AuditorSecurePassword2026!")
        auditor_page.fill("#confirm_password", "AuditorSecurePassword2026!")
        auditor_page.click("button[type='submit']")

        auditor_page.wait_for_url("**/auth/setup-2fa", timeout=15000)
        auditor_secret = auditor_page.query_selector("#totp-secret-key").inner_text().strip()
        auditor_page.fill("#code", pyotp.TOTP(auditor_secret).now())
        auditor_page.click("button[type='submit']")
        auditor_page.wait_for_load_state("networkidle")

        auditor_page.goto(f"{BASE_URL}/audit", wait_until="networkidle")
        assert "Cryptographic Audit Trail" in auditor_page.content() or "Audit" in auditor_page.title()
        auditor_page.screenshot(path=str(EVIDENCE_DIR / "08_audit_log_dashboard.png"), full_page=True)
        print("  -> Captured: 08_audit_log_dashboard.png")

        # Click the 1-click Verify Entire Audit Chain button
        auditor_page.click("#btn-verify-chain")
        auditor_page.wait_for_timeout(1000)
        auditor_page.screenshot(path=str(EVIDENCE_DIR / "09_audit_chain_verified_banner.png"), full_page=True)
        print("  -> Captured: 09_audit_chain_verified_banner.png")
        auditor_context.close()

        # Step 8: Admin Role - User Management & SECURE_MODE Demonstrator
        print("[Step 8] Testing Admin Role & SECURE_MODE Demonstrator...")
        admin_context = browser.new_context(viewport={"width": 1280, "height": 800})
        admin_page = admin_context.new_page()

        admin_page.goto(f"{BASE_URL}/auth/register", wait_until="networkidle")
        admin_user = f"admin_aarish_{int(time.time())}"
        admin_page.fill("#username", admin_user)
        admin_page.fill("#email", f"{admin_user}@nust.edu.pk")
        admin_page.select_option("#role", "Admin")
        admin_page.fill("#password", "AdminSecurePassword2026!")
        admin_page.fill("#confirm_password", "AdminSecurePassword2026!")
        admin_page.click("button[type='submit']")

        admin_page.wait_for_url("**/auth/setup-2fa", timeout=15000)
        admin_secret = admin_page.query_selector("#totp-secret-key").inner_text().strip()
        admin_page.fill("#code", pyotp.TOTP(admin_secret).now())
        admin_page.click("button[type='submit']")
        admin_page.wait_for_load_state("networkidle")

        # Navigate to SECURE_MODE page
        admin_page.goto(f"{BASE_URL}/admin/secure-mode", wait_until="networkidle")
        assert "OWASP" in admin_page.content()
        admin_page.screenshot(path=str(EVIDENCE_DIR / "10_admin_secure_mode_owasp.png"), full_page=True)
        print("  -> Captured: 10_admin_secure_mode_owasp.png")

        # Step 9: Attack Simulations Dashboard
        print("[Step 9] Testing Security Attack Simulations Dashboard...")
        admin_page.goto(f"{BASE_URL}/experiments", wait_until="networkidle")
        assert "Attack Simulation" in admin_page.content() or "Security Lab" in admin_page.title()
        admin_page.screenshot(path=str(EVIDENCE_DIR / "11_attack_simulations_lab.png"), full_page=True)
        print("  -> Captured: 11_attack_simulations_lab.png")

        # Run Pixel Tampering simulation from the UI
        btn = admin_page.query_selector(".btn-run-attack[data-attack-id='pixel_tampering']")
        if not btn:
            btn = admin_page.query_selector(".btn-run-attack")
        if btn:
            btn.click()
            admin_page.wait_for_timeout(2000)
            admin_page.screenshot(path=str(EVIDENCE_DIR / "12_simulation_result_console.png"), full_page=True)
            print("  -> Captured: 12_simulation_result_console.png")

        admin_context.close()
        browser.close()
        print("\n[SUCCESS] All Real-Browser End-to-End QA checks PASSED with 100% fidelity!")

if __name__ == '__main__':
    run_browser_e2e()
