"""Template filters for candidate_trainer."""

import re
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="render_markdown")
def render_markdown(text):
    """
    Рендерит markdown в HTML с безопасными настройками.

    Использует расширения:
    - fenced_code: блоки кода с ```
    - tables: таблицы
    - nl2br: переводы строк как <br>
    """
    if not text:
        return ""

    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
        ],
        output_format="html5",
    )
    html = md.convert(text)
    return mark_safe(html)


@register.filter(name="strip_list_marker")
def strip_list_marker(text):
    """
    Удаляет markdown-маркеры списков из начала строки.
    Используется для элементов, которые уже обёрнуты в <li>.
    """
    if not text:
        return ""

    # Удаляем маркеры * - + в начале
    cleaned = re.sub(r'^\s*[\*\-\+]\s+', '', text.strip())
    return mark_safe(cleaned)
