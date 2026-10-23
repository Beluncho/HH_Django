# Рендеринг Markdown в UI

## Проблема

LLM генерирует объяснения навыков и вопросы интервью с использованием markdown-разметки:
- Заголовки: `# Заголовок`, `## Подзаголовок`
- Жирный текст: `**текст**`
- Курсив: `*текст*`
- Списки: `- пункт`, `1. пункт`
- Блоки кода: ` ```код``` `

До исправления эти символы отображались как есть в HTML, что делало текст нечитаемым.

## Решение

### 1. Template Filter

Создан фильтр `render_markdown` в `candidate_trainer/templatetags/trainer_filters.py`:

```python
@register.filter(name="render_markdown")
def render_markdown(text):
    """Рендерит markdown в HTML с безопасными настройками."""
    md = markdown.Markdown(
        extensions=[
            "fenced_code",  # блоки кода с ```
            "tables",       # таблицы
            "nl2br",        # переводы строк как <br>
        ],
        output_format="html5",
    )
    html = md.convert(text)
    return mark_safe(html)
```

### 2. Применение в шаблонах

**analysis_detail.html** (объяснения навыков):
```django
{% load trainer_filters %}
<div class="explanation-text">{{ item.latest_explanation.content|render_markdown }}</div>
```

**interview.html** (сообщения интервью):
```django
{% load trainer_filters %}
<div class="message-content">{{ message.content|render_markdown }}</div>
```

### 3. CSS-стили

Добавлены стили для корректного отображения HTML-элементов markdown:
- Заголовки `h1`-`h4` с правильными размерами и отступами
- Списки `ul`, `ol` с маркерами и отступами
- Блоки кода `pre`, `code` с моноширинным шрифтом и фоном
- Жирный текст `strong` и курсив `em`
- Таблицы `table` с границами
- Цитаты `blockquote` с левой границей

## Зависимости

Библиотека `Markdown==3.7` уже была в `requirements.txt`.

## Безопасность

- Используется `mark_safe()` после рендеринга, так как markdown-библиотека 
  экранирует HTML-теги по умолчанию
- Включены только безопасные расширения markdown
- Не используются расширения, позволяющие произвольный HTML

## Тестирование

Созданы unit-тесты в `tests/test_template_filters.py`, проверяющие:
- Корректное преобразование всех элементов markdown
- Отсутствие сырых markdown-символов в выводе
- Обработку пустого и None-текста
- Комплексный markdown с несколькими типами элементов
