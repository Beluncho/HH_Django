"""Playwright тест с сохранением скриншотов."""
import sys
import re
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Читаем credentials
def load_credentials():
    try:
        with open('.env.test', 'r') as f:
            creds = {}
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, val = line.strip().split('=', 1)
                    creds[key] = val
            return creds.get('USERNAME', 'admin'), creds.get('PASSWORD', 'admin')
    except:
        return 'admin', 'admin'

USERNAME, PASSWORD = load_credentials()
print(f"Using credentials: {USERNAME} / {'*' * len(PASSWORD)}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()

    try:
        print("=== Авторизация ===")
        page.goto("http://localhost:8000/user/login/")
        page.screenshot(path="screenshots/01_login.png")

        # Пробуем разные селекторы для формы логина
        page.fill('input[name="username"]', USERNAME)
        page.fill('input[name="password"]', PASSWORD)
        page.screenshot(path="screenshots/02_login_filled.png")

        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        print(f"После логина: {page.url}")
        page.screenshot(path="screenshots/03_after_login.png")

        # Переход в trainer
        print("\n=== Переход в Trainer ===")
        page.goto("http://localhost:8000/trainer/")
        page.wait_for_load_state('networkidle')
        print(f"Trainer URL: {page.url}")
        page.screenshot(path="screenshots/04_trainer_home.png", full_page=True)

        # Ищем анализы
        analyses = page.locator('a[href*="/trainer/analyses/"]').all()
        print(f"Найдено анализов: {len(analyses)}")

        if analyses:
            # Открываем первый анализ
            analysis_url = analyses[0].get_attribute('href')
            print(f"\n=== Анализ: {analysis_url} ===")
            page.goto(f"http://localhost:8000{analysis_url}")
            page.wait_for_load_state('networkidle')
            page.screenshot(path="screenshots/05_analysis.png", full_page=True)
            print("✓ Скриншот анализа сохранён")

        # Ищем интервью
        interviews = page.locator('a[href*="/interviews/"]').all()
        print(f"\nНайдено интервью: {len(interviews)}")

        if not interviews:
            print("⚠ Нет интервью - создаём тестовые данные")
            page.goto("http://localhost:8000/admin/")
            page.screenshot(path="screenshots/06_no_interviews.png")
            browser.close()
            sys.exit(2)

        # Открываем первое интервью
        interview_url = interviews[0].get_attribute('href')
        print(f"\n=== Интервью: {interview_url} ===")
        page.goto(f"http://localhost:8000{interview_url}")
        page.wait_for_load_state('networkidle')
        page.screenshot(path="screenshots/07_interview_full.png", full_page=True)
        print("✓ Скриншот интервью сохранён")

        # Проверяем инсайты
        insights = page.locator('.insight-item').all()
        print(f"\nНайдено инсайтов: {len(insights)}")

        issues = []
        for i, insight in enumerate(insights):
            print(f"\n--- Инсайт {i+1} ---")

            # Скриншот инсайта
            insight.screenshot(path=f"screenshots/08_insight_{i+1}.png")

            # Проверяем пробелы
            gaps = insight.locator('.insight-list:has-text("Пробелы") li').all()
            print(f"Пробелов: {len(gaps)}")
            for j, gap in enumerate(gaps):
                text = gap.inner_text()
                html = gap.inner_html()
                print(f"  [{j+1}] Text: {text[:60]}")
                print(f"      HTML: {html[:80]}")

                # Проверяем маркеры
                if re.match(r'^\s*[\*\-\+]', text):
                    print(f"      ❌ МАРКЕР НАЙДЕН!")
                    issues.append(f"Инсайт {i+1}, Пробел {j+1}")

            # Проверяем рекомендации
            recs = insight.locator('.insight-list:has-text("Рекомендации") li').all()
            print(f"Рекомендаций: {len(recs)}")
            for j, rec in enumerate(recs):
                text = rec.inner_text()
                html = rec.inner_html()
                print(f"  [{j+1}] Text: {text[:60]}")
                print(f"      HTML: {html[:80]}")

                if re.match(r'^\s*[\*\-\+]', text):
                    print(f"      ❌ МАРКЕР НАЙДЕН!")
                    issues.append(f"Инсайт {i+1}, Рекомендация {j+1}")

        print("\n" + "="*60)
        if issues:
            print(f"❌ FAIL: Найдено маркеров в {len(issues)} местах:")
            for issue in issues:
                print(f"   - {issue}")
            sys.exit(1)
        else:
            print("✅ PASS: Все маркеры удалены корректно!")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        page.screenshot(path="screenshots/99_error.png", full_page=True)
        sys.exit(1)
    finally:
        input("\nНажмите Enter для закрытия браузера...")
        browser.close()
