"""
Кастомные теги для рендеринга форм с Bootstrap 5
Использование:
    {% load form_tags %}
    {% render_form form %}
    или
    {% render_field field %}
"""

from django import template
from django.forms import BoundField
from django.forms.widgets import CheckboxInput, RadioSelect, FileInput

register = template.Library()


@register.inclusion_tag('components/form_field.html')
def render_field(field, show_label=True):
    """
    Рендерит одно поле формы с Bootstrap классами

    Args:
        field: BoundField объект
        show_label: показывать ли label (по умолчанию True)

    Returns:
        dict: контекст для шаблона form_field.html
    """
    widget_type = field.field.widget.__class__.__name__

    # Определяем тип поля для специфичных стилей
    is_checkbox = isinstance(field.field.widget, CheckboxInput)
    is_radio = isinstance(field.field.widget, RadioSelect)
    is_file = isinstance(field.field.widget, FileInput)

    # Базовые классы для input
    css_classes = field.field.widget.attrs.get('class', '')

    if is_checkbox:
        css_classes += ' form-check-input'
    elif is_radio:
        css_classes += ' form-check-input'
    else:
        css_classes += ' form-control'

    # Добавляем класс is-invalid если есть ошибки
    if field.errors:
        css_classes += ' is-invalid'

    field.field.widget.attrs['class'] = css_classes.strip()

    # Добавляем aria-describedby для связи с help_text и ошибками
    described_by = []
    if field.help_text:
        described_by.append(f'{field.id_for_label}_help')
    if field.errors:
        described_by.append(f'{field.id_for_label}_errors')

    if described_by:
        field.field.widget.attrs['aria-describedby'] = ' '.join(described_by)

    return {
        'field': field,
        'show_label': show_label,
        'is_checkbox': is_checkbox,
        'is_radio': is_radio,
        'is_file': is_file,
    }


@register.inclusion_tag('components/form_render.html')
def render_form(form, submit_text='Отправить', submit_class='btn btn-primary'):
    """
    Рендерит всю форму с Bootstrap стилями

    Args:
        form: Django Form объект
        submit_text: текст кнопки отправки
        submit_class: CSS классы для кнопки отправки

    Returns:
        dict: контекст для шаблона form_render.html
    """
    return {
        'form': form,
        'submit_text': submit_text,
        'submit_class': submit_class,
    }
