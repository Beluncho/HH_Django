"""Автоматический UI тест для проверки markdown рендеринга."""
import re
import sys
import time
from playwright.sync_api import sync_playwright

# Устанавливаем UTF-8 для вывода в консоль Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_interview_markdown():
    """Автоматически проверяет markdown маркеры на странице интервью."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Переход на главную
            page.goto("http://localhost:8000/trainer/")
            print("✓ Открыта главная страница")
            time.sleep(2)

            # Ищем ссылки на интервью
            interviews = page.locator('a[href*="/interviews/"]').all()

            if not interviews:
                print("⚠ Нет интервью для проверки")
                browser.close()
                return None

            interview_url = interviews[0].get_attribute('href')
            print(f"✓ Найдено интервью: {interview_url}")

            # Открываем интервью
            page.goto(f"http://localhost:8000{interview_url}")
            print("✓ Страница интервью загружена")
            time.sleep(2)

            # Ждём инсайты
            try:
                page.wait_for_selector('.insight-item', timeout=5000)
            except:
                print("❌ Нет элементов .insight-item")
                # Делаем скриншот для отладки
                page.screenshot(path="error_no_insights.png", full_page=True)
                browser.close()
                return None

            # Проверяем списки
            insights = page.locator('.insight-item')
            count = insights.count()
            print(f"✓ Найдено инсайтов: {count}")

            issues = []

            for i in range(count):
                insight = insights.nth(i)

                # Проверяем пробелы
                gaps = insight.locator('.insight-list:has-text("Пробелы") li').all()
                for j, gap in enumerate(gaps):
                    text = gap.inner_text()
                    if re.match(r'^\s*[\*\-\+]\s', text):
                        issues.append({
                            'type': 'gap',
                            'insight': i + 1,
                            'index': j + 1,
                            'text': text[:60]
                        })

                # Проверяем рекомендации
                recs = insight.locator('.insight-list:has-text("Рекомендации") li').all()
                for j, rec in enumerate(recs):
                    text = rec.inner_text()
                    if re.match(r'^\s*[\*\-\+]\s', text):
                        issues.append({
                            'type': 'recommendation',
                            'insight': i + 1,
                            'index': j + 1,
                            'text': text[:60]
                        })

            # Результаты
            if issues:
                print("\n❌ Найдены markdown маркеры:")
                for issue in issues:
                    print(f"  - Инсайт {issue['insight']}, "
                          f"{issue['type']} {issue['index']}: '{issue['text']}'")
                page.screenshot(path="markdown_issues.png", full_page=True)
                print("✓ Скриншот: markdown_issues.png")
            else:
                print("\n✅ Все списки корректны - маркеры удалены")
                page.screenshot(path="interview_success.png", full_page=True)
                print("✓ Скриншот: interview_success.png")

            time.sleep(2)
            browser.close()

            return len(issues) == 0

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            page.screenshot(path="error.png", full_page=True)
            browser.close()
            return False


if __name__ == "__main__":
    result = test_interview_markdown()
    if result is None:
        print("\n⚠ Тест не выполнен - нет данных")
        exit(2)
    elif result:
        print("\n✅ PASS")
        exit(0)
    else:
        print("\n❌ FAIL")
        exit(1)
