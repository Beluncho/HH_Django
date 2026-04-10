# HH_Django
# HH Django Project - Job Search Platform

[![Django Version](https://img.shields.io/badge/Django-5.1.6-green)](https://www.djangoproject.com/)
[![DRF Version](https://img.shields.io/badge/DRF-3.15.2-blue)](https://www.django-rest-framework.org/)
[![Python Version](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)

## 📖 О проекте

Веб-платформа для поиска работы и сотрудников (аналог HeadHunter), построенная на Django и Django REST Framework. Проект включает как классические шаблонные страницы, так и REST API.

### Основной функционал:
- ✅ **Пользователи и роли** (соискатели, работодатели, администраторы)
- ✅ **Управление вакансиями** (создание, редактирование, поиск)
- ✅ **Резюме соискателей** с загрузкой фото/документов
- ✅ **REST API** с пагинацией, фильтрацией и аутентификацией
- ✅ **Админ-панель** для управления контентом
- ✅ **Отправка email-уведомлений** (консольный backend для разработки)
- ✅ **Валюты** (интеграция с ЦБ РФ через pycbrf)
- ✅ **DBF-файлы** (импорт данных из старых форматов)

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/Beluncho/HH_Django.git
cd HH_Django
git checkout nu31-api  # Переключитесь на ветку с API
