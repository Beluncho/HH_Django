"""Тест markdown рендеринга."""
import markdown
import re

text = """2. Где применяется
На основе ваших задач Python используется в трех ключевых направлениях:
* Data Engineering (Data Pipeline): Сбор данных из внешних источников
* AI/ML Разработка: Проектирование архитектуры интеллектуальных агентов
* Backend и Автоматизация: Создание внутренней бизнес-логики"""

print("=== Исходный текст ===")
print(text)

md = markdown.Markdown(
    extensions=["fenced_code", "tables", "nl2br"],
    output_format="html5"
)
html = md.convert(text)

print("\n=== HTML после markdown ===")
print(html)

# Применяем regex
cleaned = re.sub(r'(<li[^>]*>)\s*[\*\-\+]\s+', r'\1', html)

print("\n=== HTML после regex ===")
print(cleaned)
