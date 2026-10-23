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

    Предварительно очищает markdown маркеры списков для корректного рендеринга.
    """
    if not text:
        return ""

    # Удаляем markdown маркеры списков ДО рендеринга
    # Паттерн: строки начинающиеся с * - + (с опциональными пробелами)
    # Заменяем на просто текст без маркера
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Удаляем маркеры в начале строки (после опциональных пробелов)
        cleaned = re.sub(r'^(\s*)[\*\-\+]\s+', r'\1', line)
        cleaned_lines.append(cleaned)
    cleaned_text = '\n'.join(cleaned_lines)

    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "nl2br",
        ],
        output_format="html5",
    )
    html = md.convert(cleaned_text)

    return mark_safe(html)


@register.filter(name="strip_list_marker")
def strip_list_marker(text):
    """
    Удаляет markdown-маркеры списков из начала строки.
    Используется для элементов, которые уже обёрнуты в <li>.
    """
    if not text:
        return ""

    # Удаляем маркеры * - + в начале (с опциональным пробелом после)
    cleaned = re.sub(r'^\s*[\*\-\+]\s*', '', str(text).strip())
    return mark_safe(cleaned)
