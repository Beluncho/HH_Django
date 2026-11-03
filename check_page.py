"""Проверка структуры страницы."""
import sys
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("http://localhost:8000/trainer/")
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Проверяем все ссылки
    all_links = page.locator('a').all()
    print(f"\nВсего ссылок: {len(all_links)}")

    for link in all_links[:20]:  # Первые 20
        href = link.get_attribute('href')
        text = link.inner_text()[:50] if link.inner_text() else '[no text]'
        print(f"  - {href}: {text}")

    # Делаем скриншот
    page.screenshot(path="homepage.png", full_page=True)
    print("\n✓ Скриншот: homepage.png")

    input("Press Enter...")
    browser.close()
