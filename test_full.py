"""Полный автотест с авторизацией и проверкой markdown."""
import sys
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Логин
        page.goto("http://localhost:8000/user/login/")
        print("✓ Страница логина")

        page.fill('#id_username', 'admin')
        page.fill('#id_password', 'admin')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        print("✓ Авторизация")

        # Переход в trainer
        page.goto("http://localhost:8000/trainer/")
        print(f"✓ Trainer URL: {page.url}")

        # Скриншот главной
        page.screenshot(path="trainer_home.png", full_page=True)
        print("✓ Скриншот: trainer_home.png")

        # Ищем интервью
        links = page.locator('a').all()
        interview_link = None
        for link in links:
            href = link.get_attribute('href') or ''
            if '/interviews/' in href:
                interview_link = href
                break

        if not interview_link:
            print("❌ Нет ссылок на интервью")
            # Пробуем создать данные
            print("Пробуем создать тестовые данные...")
            page.goto("http://localhost:8000/admin/")

            browser.close()
            exit(2)

        print(f"✓ Найдено интервью: {interview_link}")

        # Открываем интервью
        page.goto(f"http://localhost:8000{interview_link}")
        page.wait_for_load_state('networkidle')
        print("✓ Страница интервью загружена")

        # Скриншот интервью
        page.screenshot(path="interview_full.png", full_page=True)
        print("✓ Скриншот: interview_full.png")

        # Проверяем инсайты
        insights = page.locator('.insight-item').all()
        print(f"✓ Найдено инсайтов: {len(insights)}")

        if not insights:
            print("❌ Нет инсайтов")
            browser.close()
            exit(2)

        # Проверяем маркеры
        issues = 0
        for i, insight in enumerate(insights):
            # Пробелы
            gaps = insight.locator('.insight-list:has-text("Пробелы") li').all()
            for j, gap in enumerate(gaps):
                text = gap.inner_text()
                print(f"  Gap {i+1}.{j+1}: {text[:60]}")
                if text.strip().startswith(('*', '-', '+')):
                    print(f"    ❌ Есть маркер!")
                    issues += 1

            # Рекомендации
            recs = insight.locator('.insight-list:has-text("Рекомендации") li').all()
            for j, rec in enumerate(recs):
                text = rec.inner_text()
                print(f"  Rec {i+1}.{j+1}: {text[:60]}")
                if text.strip().startswith(('*', '-', '+')):
                    print(f"    ❌ Есть маркер!")
                    issues += 1

        if issues > 0:
            print(f"\n❌ Найдено проблем: {issues}")
            exit(1)
        else:
            print("\n✅ Все списки корректны!")
            exit(0)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        page.screenshot(path="error_full.png", full_page=True)
        browser.close()
        exit(1)
