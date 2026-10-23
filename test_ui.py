"""UI тесты для проверки markdown рендеринга."""
import re
import sys
from playwright.sync_api import sync_playwright

# Устанавливаем UTF-8 для вывода в консоль Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_interview_page():
    """Проверяет что markdown маркеры не видны в списках на странице интервью."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()

        print("Откройте браузер и авторизуйтесь, затем перейдите на страницу интервью")
        print("После этого нажмите Enter в консоли...")

        page.goto("http://localhost:8000/trainer/")
        input("Нажмите Enter когда будете готовы проверить страницу интервью...")

        # Проверяем текущий URL
        current_url = page.url
        print(f"Текущий URL: {current_url}")

        if "/interviews/" not in current_url:
            print("⚠ Пожалуйста, перейдите на страницу интервью")
            input("Нажмите Enter когда перейдёте...")

        # Ждём загрузки инсайтов
        try:
            page.wait_for_selector('.insight-item', timeout=5000)
        except:
            print("❌ Не найдены элементы .insight-item на странице")
            browser.close()
            return False

        # Проверяем списки в инсайтах
        insights = page.locator('.insight-item')
        insights_count = insights.count()
        print(f"✓ Найдено инсайтов: {insights_count}")

        issues = []

        for i in range(insights_count):
            insight = insights.nth(i)

            # Проверяем пробелы (gaps)
            gaps = insight.locator('.insight-list:has-text("Пробелы") li')
            gaps_count = gaps.count()

            for j in range(gaps_count):
                gap_text = gaps.nth(j).inner_text()
                if re.match(r'^\s*[\*\-\+]\s', gap_text):
                    issues.append(f"Инсайт {i+1}, Пробел {j+1}: '{gap_text[:50]}...'")

            # Проверяем рекомендации
            recs = insight.locator('.insight-list:has-text("Рекомендации") li')
            recs_count = recs.count()

            for j in range(recs_count):
                rec_text = recs.nth(j).inner_text()
                if re.match(r'^\s*[\*\-\+]\s', rec_text):
                    issues.append(f"Инсайт {i+1}, Рекомендация {j+1}: '{rec_text[:50]}...'")

        if issues:
            print("\n❌ Найдены markdown маркеры в списках:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Все списки корректны - маркеры удалены")

        # Делаем скриншот
        page.screenshot(path="interview_page.png", full_page=True)
        print("✓ Скриншот сохранён: interview_page.png")

        input("Нажмите Enter для закрытия браузера...")
        browser.close()

        return len(issues) == 0


if __name__ == "__main__":
    success = test_interview_page()
    exit(0 if success else 1)
