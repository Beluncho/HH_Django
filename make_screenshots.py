"""Создание финальных скриншотов для портфолио."""
import sys
import time
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={'width': 1600, 'height': 900},
        device_scale_factor=1
    )
    page = context.new_page()

    print("=== Авторизация ===")
    page.goto("http://localhost:8000/user/login/")
    page.fill('input[name="username"]', USERNAME)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    print("✓ Авторизован")

    # Screenshot 8: Trainer dashboard
    print("\n=== Screenshot 8: Trainer Dashboard ===")
    page.goto("http://localhost:8000/trainer/")
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    page.screenshot(path="screenshots/django-08-trainer.png")
    print("✓ django-08-trainer.png")

    # Screenshot 9: Analysis detail
    print("\n=== Screenshot 9: Analysis Detail ===")
    analyses = page.locator('a[href*="/trainer/analyses/"]').all()
    if analyses:
        analysis_url = analyses[0].get_attribute('href')
        page.goto(f"http://localhost:8000{analysis_url}")
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Скролл к секции Skills
        page.evaluate("document.querySelector('#skills')?.scrollIntoView({behavior: 'instant', block: 'start'})")
        time.sleep(0.5)

        page.screenshot(path="screenshots/django-09-analysis.png", full_page=False)
        print("✓ django-09-analysis.png")

        # Screenshot 10: Skill explanation (если есть)
        print("\n=== Screenshot 10: Skill Explanation ===")
        explanations = page.locator('[id^="skill-explanation-"]').all()
        if explanations:
            # Скролл к первому объяснению
            first_exp_id = explanations[0].get_attribute('id')
            page.evaluate(f"document.querySelector('#{first_exp_id}')?.scrollIntoView({{behavior: 'instant', block: 'start'}})")
            time.sleep(0.5)

            page.screenshot(path="screenshots/django-10-explanation.png", full_page=False)
            print("✓ django-10-explanation.png")
        else:
            print("⚠ Нет объяснений навыков")
    else:
        print("⚠ Нет анализов")

    # Screenshot 11: Interview
    print("\n=== Screenshot 11: Interview ===")
    page.goto("http://localhost:8000/trainer/")
    interviews = page.locator('a[href*="/interviews/"]').all()
    if interviews:
        interview_url = interviews[0].get_attribute('href')
        page.goto(f"http://localhost:8000{interview_url}")
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Скролл к инсайтам
        insights = page.locator('.insight-item').all()
        if insights:
            page.evaluate("document.querySelector('.insight-item')?.scrollIntoView({behavior: 'instant', block: 'center'})")
            time.sleep(0.5)

        page.screenshot(path="screenshots/django-11-interview.png", full_page=False)
        print("✓ django-11-interview.png")
    else:
        print("⚠ Нет интервью")

    print("\n" + "="*60)
    print("✅ Скриншоты AI-модуля обновлены!")
    print("\nОбновлено:")
    print("  - django-08-trainer.png (Dashboard)")
    print("  - django-09-analysis.png (Analysis с навыками)")
    print("  - django-10-explanation.png (Объяснение навыка)")
    print("  - django-11-interview.png (Интервью с инсайтами)")
    print("="*60)

    input("\nНажмите Enter чтобы закрыть браузер...")
    browser.close()
