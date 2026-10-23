"""Тесты template filters."""

from django.test import SimpleTestCase

from candidate_trainer.templatetags.trainer_filters import render_markdown


class RenderMarkdownFilterTestCase(SimpleTestCase):
    """Тесты фильтра render_markdown."""

    def test_empty_text(self):
        """Пустой текст возвращает пустую строку."""
        self.assertEqual(render_markdown(""), "")
        self.assertEqual(render_markdown(None), "")

    def test_plain_text(self):
        """Обычный текст оборачивается в параграф."""
        result = render_markdown("Простой текст")
        self.assertIn("Простой текст", result)

    def test_bold_text(self):
        """Жирный текст рендерится в <strong>."""
        result = render_markdown("Это **жирный** текст")
        self.assertIn("<strong>жирный</strong>", result)
        self.assertNotIn("**", result)

    def test_italic_text(self):
        """Курсив рендерится в <em>."""
        result = render_markdown("Это *курсив* текст")
        self.assertIn("<em>курсив</em>", result)
        self.assertNotIn("*курсив*", result)

    def test_headers(self):
        """Заголовки рендерятся в <h1>, <h2> и т.д."""
        result = render_markdown("# Заголовок 1\n## Заголовок 2")
        self.assertIn("<h1>Заголовок 1</h1>", result)
        self.assertIn("<h2>Заголовок 2</h2>", result)
        self.assertNotIn("# Заголовок", result)
        self.assertNotIn("## Заголовок", result)

    def test_unordered_list(self):
        """Маркированный список рендерится в <ul><li>."""
        result = render_markdown("- Пункт 1\n- Пункт 2\n- Пункт 3")
        self.assertIn("<ul>", result)
        self.assertIn("<li>Пункт 1</li>", result)
        self.assertIn("<li>Пункт 2</li>", result)
        self.assertNotIn("- Пункт", result)

    def test_ordered_list(self):
        """Нумерованный список рендерится в <ol><li>."""
        result = render_markdown("1. Первый\n2. Второй\n3. Третий")
        self.assertIn("<ol>", result)
        self.assertIn("<li>Первый</li>", result)
        self.assertIn("<li>Второй</li>", result)

    def test_code_block(self):
        """Блок кода рендерится в <code> и <pre>."""
        result = render_markdown("```python\nprint('hello')\n```")
        self.assertIn("<code>", result)
        self.assertIn("print('hello')", result)
        self.assertNotIn("```", result)

    def test_line_breaks(self):
        """Переводы строк сохраняются благодаря nl2br."""
        result = render_markdown("Строка 1\nСтрока 2")
        self.assertIn("Строка 1", result)
        self.assertIn("Строка 2", result)
        # nl2br должен добавить <br>
        self.assertIn("<br", result)

    def test_complex_markdown(self):
        """Комплексный markdown с разными элементами."""
        markdown_text = """
# Навык: Python

Python — это **высокоуровневый** язык программирования.

## Основные особенности:

- Простой синтаксис
- Динамическая типизация
- Большая стандартная библиотека

## Применение:

1. Web-разработка
2. Data Science
3. Автоматизация

Пример кода:
```python
def hello():
    print("Hello, World!")
```
"""
        result = render_markdown(markdown_text)

        # Проверяем, что markdown-символы удалены
        self.assertNotIn("**", result)
        self.assertNotIn("# Навык", result)
        self.assertNotIn("## Основные", result)
        self.assertNotIn("```", result)
        self.assertNotIn("- Простой", result)
        self.assertNotIn("1. Web", result)

        # Проверяем, что HTML создан
        self.assertIn("<h1>Навык: Python</h1>", result)
        self.assertIn("<h2>Основные особенности:</h2>", result)
        self.assertIn("<strong>высокоуровневый</strong>", result)
        self.assertIn("<ul>", result)
        self.assertIn("<li>Простой синтаксис</li>", result)
        self.assertIn("<ol>", result)
        self.assertIn("<li>Web-разработка</li>", result)
        self.assertIn("<code>", result)
        self.assertIn("def hello():", result)
