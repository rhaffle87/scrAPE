# -*- coding: utf-8 -*-
"""
Playwright E2E verification of segment content and footer translations across languages.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

html_path = Path("docs/site/index.html").resolve()
file_url = f"file:///{html_path.as_posix()}"

print(f"Testing URL: {file_url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    
    # 1. Load German (lang=de)
    page.goto(f"{file_url}?lang=de")
    page.wait_for_load_state("domcontentloaded")
    
    # Check language indicator
    current_code = page.locator("#current-lang-code").inner_text()
    assert current_code == "DE", f"Expected 'DE', got '{current_code}'"
    print("[OK] [DE] Lang code verified: DE")
    
    # Check German section card title
    card_title = page.locator("#sec-install-steps .card-title").inner_text()
    assert card_title == "2.2 Installationsablauf & Einrichtung", f"Unexpected card title: '{card_title}'"
    print(f"[OK] [DE] Card title verified: '{card_title}'")
    
    # Check German code header
    code_header = page.locator("#sec-install-steps .code-header span").first.inner_text()
    assert code_header == "BASH // INSTALLATIONSBEFEHLE", f"Unexpected code header: '{code_header}'"
    print(f"[OK] [DE] Code header verified: '{code_header}'")
    
    # Check German alert title
    alert_title = page.locator("#sec-install-steps .alert-title").inner_text()
    assert alert_title == "[i] FLARESOLVERR-EINRICHTUNG", f"Unexpected alert title: '{alert_title}'"
    print(f"[OK] [DE] Alert title verified: '{alert_title}'")
    
    # Check German snippet comments
    snippet_text = page.locator("#sec-install-steps pre").inner_text()
    assert "# 1. Repository klonen" in snippet_text, "Missing German comment in snippet!"
    print("[OK] [DE] Snippet comments localized successfully.")
    
    # Check German footer
    footer_logo = page.locator(".footer-logo").inner_text()
    assert footer_logo == "scrAPE // KERN-SYSTEM", f"Unexpected footer logo: '{footer_logo}'"
    
    footer_badge = page.locator(".footer-badges .badge-tag").nth(1).inner_text()
    assert "MIT-LIZENZIERT" in footer_badge, f"Unexpected footer badge: '{footer_badge}'"
    
    footer_heading_docs = page.locator(".footer-nav-col .footer-heading").nth(1).inner_text()
    assert footer_heading_docs == "DOKUMENTATION", f"Unexpected heading: '{footer_heading_docs}'"
    
    footer_link_source = page.locator(".footer-link-list a").first.inner_text()
    assert footer_link_source == "Quellcode", f"Unexpected link: '{footer_link_source}'"
    
    footer_link_changelog = page.locator(".footer-link-list a").nth(6).inner_text()
    assert footer_link_changelog == "Änderungsprotokoll", f"Unexpected link: '{footer_link_changelog}'"
    
    footer_copy = page.locator(".footer-copy").inner_text()
    assert "Open Source unter der MIT-Lizenz" in footer_copy, f"Unexpected copy: '{footer_copy}'"
    
    footer_sysinfo = page.locator(".footer-sysinfo").inner_text()
    assert footer_sysinfo == "STATUS: EINSATZBEREIT // ENGINE: v0.30.1", f"Unexpected sysinfo: '{footer_sysinfo}'"
    print("[OK] [DE] All footer elements (logo, badges, headings, links, copy, sysinfo) verified.")
    
    # 2. Dynamically Switch to Indonesian (ID) via Dropdown
    page.locator("#lang-picker-btn").click()
    page.locator(".lang-choice[data-lang='id']").click()
    
    id_card_title = page.locator("#sec-install-steps .card-title").inner_text()
    assert id_card_title == "2.2 Prosedur Instalasi & Pengaturan", f"Unexpected ID title: '{id_card_title}'"
    
    id_code_header = page.locator("#sec-install-steps .code-header span").first.inner_text()
    assert id_code_header == "BASH // PERINTAH INSTALASI", f"Unexpected ID header: '{id_code_header}'"
    
    id_alert_title = page.locator("#sec-install-steps .alert-title").inner_text()
    assert id_alert_title == "[i] PENGATURAN FLARESOLVERR", f"Unexpected ID alert title: '{id_alert_title}'"
    
    id_footer_logo = page.locator(".footer-logo").inner_text()
    assert id_footer_logo == "scrAPE // SISTEM INTI", f"Unexpected ID footer logo: '{id_footer_logo}'"
    
    id_footer_badge = page.locator(".footer-badges .badge-tag").nth(1).inner_text()
    assert "LISENSI MIT" in id_footer_badge, f"Unexpected ID badge: '{id_footer_badge}'"
    print("[OK] [ID] Dynamic switch to Indonesian verified.")
    
    # 3. Dynamically Switch to Chinese (ZH) via Dropdown
    page.locator("#lang-picker-btn").click()
    page.locator(".lang-choice[data-lang='zh']").click()
    
    zh_card_title = page.locator("#sec-install-steps .card-title").inner_text()
    assert zh_card_title == "2.2 安装步骤与部署流程", f"Unexpected ZH title: '{zh_card_title}'"
    
    zh_footer_logo = page.locator(".footer-logo").inner_text()
    assert zh_footer_logo == "scrAPE // 核心系统", f"Unexpected ZH footer logo: '{zh_footer_logo}'"
    
    zh_footer_link = page.locator(".footer-link-list a").first.inner_text()
    assert zh_footer_link == "源代码", f"Unexpected ZH link: '{zh_footer_link}'"
    print("[OK] [ZH] Dynamic switch to Chinese verified.")
    
    # 4. Dynamically Switch back to English (EN)
    page.locator("#lang-picker-btn").click()
    page.locator(".lang-choice[data-lang='en']").click()
    
    en_card_title = page.locator("#sec-install-steps .card-title").inner_text()
    assert en_card_title == "2.2 Setup Procedure", f"Unexpected EN title: '{en_card_title}'"
    
    # Switch to German mode for final screenshot
    page.locator("#lang-picker-btn").click()
    page.locator(".lang-choice[data-lang='de']").click()
    
    # Activate section directly by clicking the link via JS
    page.evaluate("document.querySelector('.nav-sub-item a[href=\"#sec-install-steps\"]').click()")
    page.wait_for_timeout(500)
    page.screenshot(path="docs/site/test_de_install_steps.png")
    
    # Scroll to footer and take screenshot
    page.locator(".doc-footer").scroll_into_view_if_needed()
    page.screenshot(path="docs/site/test_de_footer.png")
    
    browser.close()

print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")
