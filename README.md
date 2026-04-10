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
2. Создание и активация виртуального окружения
bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
3. Установка зависимостей
bash
pip install -r requirements.txt
4. Настройка переменных окружения
Создайте файл .env в корне проекта:

env
SECRET_KEY=ваш-секретный-ключ-сгенерируйте-новый
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
⚠️ Важно: Никогда не коммитьте .env файл в репозиторий! Добавьте его в .gitignore.

5. Применение миграций и создание суперпользователя
bash
python manage.py migrate
python manage.py createsuperuser
6. Запуск сервера разработки
bash
python manage.py runserver
Сайт будет доступен: http://127.0.0.1:8000
Админ-панель: http://127.0.0.1:8000/admin

📁 Структура проекта
text
HH_Django/
├── HH/                      # Корневая папка проекта
│   ├── HH/                  # Основная конфигурация Django
│   │   ├── settings.py      # Настройки проекта
│   │   ├── urls.py          # Головные URL-маршруты
│   │   └── wsgi.py
│   ├── hhapp/               # Основное приложение (вакансии, резюме)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── management/      # Кастомные команды manage.py
│   │   ├── migrations/
│   │   └── templates/hhapp/
│   ├── userapp/             # Приложение пользователей (кастомная модель)
│   │   ├── models.py        # WebSiteUser (замена стандартного User)
│   │   ├── views.py
│   │   ├── migrations/
│   │   └── templates/userapp/
│   ├── static/              # Статические файлы (CSS, JS, изображения)
│   │   ├── assets/
│   │   ├── css/
│   │   ├── jquery/
│   │   └── js/
│   ├── media/               # Пользовательские файлы (аватарки, резюме)
│   │   └── users/
│   ├── templates/           # Глобальные шаблоны
│   │   └── startbootstrap-creative-gh-pages/
├── nginx/                   # Конфигурация для продакшена
├── venv/                    # Виртуальное окружение (не коммитится)
└── requirements.txt
🔌 API Endpoints (REST API)
Метод	URL	Описание
GET	/api/vacancies/	Список вакансий (пагинация 20 элементов)
POST	/api/vacancies/	Создание новой вакансии (требуется аутентификация)
GET	/api/resumes/	Список резюме
GET	/api/vacancies/{id}/	Детальная информация о вакансии
POST	/api/auth/login/	Вход через BasicAuth или SessionAuth
Пример запроса к API:

bash
curl -H 'Accept: application/json' http://127.0.0.1:8000/api/vacancies/
🛠️ Управление проектом
Запуск тестов
bash
python manage.py test
Проверка покрытия кода тестами
bash
coverage run manage.py test
coverage report
Сбор статических файлов (для продакшена)
bash
python manage.py collectstatic
⚠️ Важные замечания по безопасности
Перед деплоем в продакшен необходимо:

Секретный ключ — вынести в переменные окружения:

python
import os
SECRET_KEY = os.getenv('SECRET_KEY')
Отключить DEBUG:

python
DEBUG = False
Заполнить ALLOWED_HOSTS:

python
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
Сменить базу данных с SQLite на PostgreSQL:

python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
    }
}
Настроить реальный Email backend (SMTP) вместо консольного

📦 Используемые технологии
Backend: Django 5.1, Django REST Framework 3.15

База данных: SQLite (dev) / PostgreSQL (рекомендуется для prod)

Отладка: django-debug-toolbar

Тестирование: coverage, mixer, Faker

Работа с файлами: Pillow, django-cleanup

Внешние API: requests, pycbrf (курсы валют)

Фронтенд: Bootstrap (стартовый шаблон Creative), jQuery