# План улучшения разметки и стилизации проекта HH_Django

## Дата создания: 2025-01-20
## Последнее обновление: 2025-01-20

---

## Анализ текущего состояния

### Обнаруженные проблемы

#### 1. **Несогласованность стилей между приложениями**
- **candidate_trainer**: современный CSS с переменными, семантическая вёрстка, accessibility-first подход
- **hhapp, userapp**: Bootstrap 5 с минимальной кастомизацией, устаревшие паттерны

#### 2. **Базовый шаблон (base.html)**
- ❌ Навигация: кнопка Log Out без Bootstrap-классов (голый `<button>` на строке 42)
- ❌ Отсутствует `.navbar-toggler` — мобильное меню не работает
- ❌ Структура навигации нелогична: элементы добавляются и внутри, и вне блока `{% block navigation %}`
- ❌ Жёстко захардкоженная галерея Portfolio (6 заглушечных изображений, строки 56-98)
- ❌ Изображения portfolio имеют пустой alt: `alt="..."`
- ⚠️ Смешивание контента и layout: портфолио, footer — часть base, а не опциональные блоки
- ⚠️ SimpleLightbox подключен, но используется только для portfolio

#### 3. **Формы (все приложения)**
- ❌ `{{ form.as_p }}` повсеместно — Django рендерит без Bootstrap-стилей
- ❌ Отсутствие единого паттерна рендеринга форм
- ❌ Нет валидации на клиенте, слабая обратная связь об ошибках
- ❌ Placeholders в виджетах дублируют labels (hhapp/forms.py)
- ❌ Формы в `login.html` (строка 12: `.text-white`) — белый текст на тёмном фоне, ошибки валидации не видны

#### 4. **index.html (hhapp)**
- ❌ Пагинация: голые ссылки без стилей Bootstrap (`<span class="step-links">`)
- ❌ Смешивание внутренних вакансий и HH.ru без визуального разделения
- ❌ Форма поиска работает, но результаты для HH отображаются иначе, чем для внутренних
- ℹ️ Anchor-навигация (#about, #services, #contact) — допустимо для одностраничного layout, но смешивается с многостраничной навигацией (профиль, тренажёр)

#### 5. **profile.html (userapp)**
- ❌ Токен в голом `<div>`, без карточки и стилей
- ❌ Кнопки разных стилей: `btn-primary`, `btn-info`, без единообразия
- ❌ Проверка прав (`{% if user.id == object.id %}`) в шаблоне, а не во view
- ⚠️ Атрибут `foto` в модели WebSiteUser (строка 8 userapp/models.py) — английская база кода, русское слово

#### 6. **vacancy.html, vacancy_create.html (hhapp)**
- ❌ `vacancy_create.html`: форма в узком контейнере `col-lg-3` — слишком мало места
- ❌ `vacancy.html`: избыточная сетка из 4 колонок для 4 полей — можно компактнее
- ⚠️ Дублирование заголовка "URL vacancies on HH.ru" в двух местах

#### 7. **login.html, registration.html (userapp)**
- ❌ Формы с белым текстом на тёмном фоне (`.text-white` на строке 12 login.html) — ошибки валидации не видны
- ❌ `{{ form.as_p }}` — нет стилей Bootstrap для полей
- ⚠️ Размер контейнера разный: login — `col-lg-6`, registration — `col-xs-12`

#### 8. **Отсутствующие элементы**
- ❌ Кастомные страницы ошибок 404.html, 500.html
- ❌ Единый компонент для вывода сообщений (Django messages framework)
- ❌ Breadcrumbs навигация (есть только в candidate_trainer)
- ❌ Мобильная навигация (hamburger menu) не работает — `.navbar-toggler` отсутствует в base.html

#### 9. **Accessibility и семантика**
- ✅ candidate_trainer: aria-labels, role, semantic HTML
- ❌ hhapp, userapp: нет aria-атрибутов, heading hierarchy нарушен
- ❌ Изображения без alt (portfolio в base.html: `alt="..."`)
- ❌ Формы без связи label-input (через `{{ form.as_p }}`)

---

## План работ

### Этап 0: Критические исправления (hotfix)
**Цель**: Исправить то, что ломает UX прямо сейчас  
**Время**: 1-2 часа  
**Зависимости**: Нет  
**Стратегия отката**: `git revert` отдельных коммитов

- [ ] **0.1** Исправить кнопку Log Out в base.html
  - Добавить классы: `btn btn-outline-light btn-sm`
  - Убрать из `<form>`, обернуть в `<li class="nav-item">`
  - **До**: `<button type="submit">Log Out</button>`
  - **После**: `<button type="submit" class="btn btn-outline-light btn-sm">Log Out</button>`
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **0.2** Добавить navbar-toggler в base.html (строка 27, после открывающего тега `<nav>`)
  ```html
  <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
          data-bs-target="#navbarResponsive" aria-controls="navbarResponsive" 
          aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
  </button>
  ```
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **0.3** Исправить белый текст в login.html
  - Убрать класс `.text-white` из `<div>` на строке 12
  - Обернуть форму в карточку: `<div class="card shadow-sm"><div class="card-body">...</div></div>`
  - Фон masthead оставить, но форму сделать контрастной
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **0.4** Исправить пагинацию в index.html
  - Заменить `<span class="step-links">` на Bootstrap pagination:
  ```html
  <nav aria-label="Навигация по страницам">
    <ul class="pagination justify-content-center">
      <!-- prev, current, next -->
    </ul>
  </nav>
  ```
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **0.5** Проверить работоспособность после hotfix
  - Запустить `docker compose up -d`
  - Проверить навигацию на мобильном (DevTools, 375px)
  - Проверить форму логина (отправить с ошибками)
  - Проверить кнопку Log Out
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Навигация работает на мобильном, формы читаемы, пагинация стилизована.

---

### Этап 1: Базовая инфраструктура
**Цель**: Создать единую систему компонентов и стилей  
**Время**: 4-6 часов  
**Зависимости**: Этап 0 завершён  
**Стратегия отката**: Git branch `feature/markup-stage-1`, отдельный PR

- [ ] **1.1** Создать `HH/static/css/common.css` — общие переменные и утилиты
  - Цветовая схема (базироваться на Bootstrap 5 defaults, добавить акценты из candidate_trainer)
  - Типографика (использовать существующие шрифты Merriweather)
  - Spacing утилиты (дополнение к Bootstrap, если нужно)
  - Состояния (success, error, warning, info) — Bootstrap уже предоставляет
  - **Подключить в base.html после styles.css**
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **1.2** Создать `HH/templates/components/` — переиспользуемые компоненты
  - `form_field.html` — рендеринг поля формы с Bootstrap
  - `pagination.html` — стилизованная пагинация (из 0.4)
  - `messages.html` — вывод Django messages (см. 1.4)
  - `breadcrumbs.html` — навигационная цепочка
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **1.3** Обновить `base.html` — структурные исправления
  - **Убрать жёстко захардкоженный Portfolio** (строки 56-98) — перенести в `{% block portfolio %}{% endblock %}`
  - Если portfolio не используется ни на одной странице (кроме index.html) → удалить совсем
  - Подключить `common.css` (после строки 21)
  - Добавить блок для messages: `{% include 'components/messages.html' %}` (после `<nav>`)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **1.4** Настроить Django messages framework
  - Убедиться, что `django.contrib.messages` в INSTALLED_APPS (уже должен быть)
  - Создать `HH/templates/components/messages.html`:
  ```django
  {% if messages %}
  <div class="container mt-3">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
      {{ message }}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>
    </div>
    {% endfor %}
  </div>
  {% endif %}
  ```
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **1.5** Проверить все страницы после изменения base.html
  - index.html (hhapp)
  - login.html, registration.html, profile.html (userapp)
  - vacancy.html, vacancy_create.html (hhapp)
  - candidate_trainer страницы
  - **Критерий**: нет визуальных регрессий, все страницы открываются
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Компоненты созданы, base.html чистый, messages работают, нет регрессий.

---

### Этап 2: Формы
**Цель**: Единообразный рендеринг форм с валидацией и обратной связью  
**Время**: 6-8 часов  
**Зависимости**: Этап 1 завершён (нужны компоненты)  
**Стратегия отката**: Git branch `feature/markup-stage-2`, отдельный PR

- [ ] **2.1** Создать `HH/templatetags/form_tags.py` — кастомные теги для форм
  - `{% render_field field %}` — рендеринг одного поля с Bootstrap classes
  - `{% render_form form %}` — рендеринг всей формы
  - Обработка ошибок: добавлять `.is-invalid`, показывать `.invalid-feedback`
  - Поддержка help_text: `<small class="form-text text-muted">`
  - **Пример**: https://simpleisbetterthancomplex.com/tutorial/2018/08/13/how-to-use-bootstrap-4-forms-with-django.html
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **2.2** Обновить формы в `hhapp/forms.py`
  - Убрать placeholders из атрибутов (дублируют labels)
  - Добавить help_text там, где нужно (например, для URL вакансии)
  - Унифицировать классы виджетов (если есть кастомные)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **2.3** Обновить формы в `userapp/forms.py`
  - Добавить поля для обновления профиля (сейчас только создание через регистрацию)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **2.4** Переименовать `foto` → `photo` в модели WebSiteUser
  - **Вопрос к пользователю**: Хотите переименовать `foto` в `photo` для согласованности с английским кодом?
    - **Вариант A**: Да, переименовать (потребует миграции и обновления шаблонов)
    - **Вариант B**: Нет, оставить как есть (избежать миграции, но сохранить несогласованность)
  - Если A → создать миграцию `RenameField`, обновить profile.html, userapp/forms.py
  - **Статус**: ⬜ | **Решение**: _ожидает выбора пользователя_

- [ ] **2.5** Переписать шаблоны с формами
  - `hhapp/vacancy_create.html` — использовать `{% load form_tags %}` + `{% render_form form %}`
  - `userapp/login.html` — то же + убрать `.text-white` (уже в 0.3, проверить)
  - `userapp/registration.html` — то же
  - `userapp/profile.html` — то же (для формы редактирования, если будет добавлена)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **2.6** Тестирование форм
  - Отправить форму с валидными данными → проверить сохранение
  - Отправить форму с ошибками → проверить отображение `.invalid-feedback`
  - Проверить на мобильном (touch-friendly inputs)
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Все формы стилизованы через Bootstrap, ошибки видны, help_text работает.

---

### Этап 3: Страницы hhapp
**Цель**: Привести к современному виду, улучшить UX  
**Время**: 6-8 часов  
**Зависимости**: Этап 1 (компоненты) и Этап 2.5 (формы) завершены  
**Стратегия отката**: Git branch `feature/markup-stage-3`, отдельный PR

- [ ] **3.1** `index.html` — главная страница
  - Переработать форму поиска: уже хороша (строки 40-56), оставить как есть
  - Унифицировать отображение внутренних вакансий и HH.ru:
    - Добавить бейдж: `<span class="badge bg-secondary">Внутренняя</span>` / `<span class="badge bg-info">HH.ru</span>`
  - Добавить визуальное разделение между секциями: уже есть `<hr class="divider">`
  - Пагинация: использовать компонент из 1.2 (`{% include 'components/pagination.html' %}`)
  - **Решение по portfolio**: Если не используется, удалить блок. Если используется — переместить в `{% block portfolio %}` в index.html
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **3.2** `vacancy.html` — детальная страница вакансии
  - Компактная карточка вместо 4-колоночной сетки:
  ```html
  <div class="card">
    <div class="card-body">
      <h1 class="card-title">{{ vacancy.vac_name }}</h1>
      <p class="text-muted">{{ vacancy.employer }}</p>
      <div class="mb-3">
        <strong>URL:</strong> <a href="{{ vacancy.url }}">{{ vacancy.url }}</a>
      </div>
      <div>{{ vacancy.description|linebreaks }}</div>
    </div>
  </div>
  ```
  - Breadcrumbs навигация: `{% include 'components/breadcrumbs.html' with items=... %}`
  - Улучшить типографику описания (уже есть через `|linebreaks`)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **3.3** `vacancy_create.html` — создание вакансии
  - Увеличить контейнер формы (`col-lg-6` вместо `col-lg-3`)
  - Использовать `{% render_form form %}` (уже в 2.5)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **3.4** `employers_list.html`, `employer_detail.html` — работодатели
  - Просмотреть и привести к единому стилю (карточки, таблицы → Bootstrap)
  - Добавить breadcrumbs
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **3.5** Тестирование hhapp страниц
  - Проверить навигацию: главная → вакансия → главная
  - Проверить anchor-навигацию (#about, #services) — плавная прокрутка работает?
  - Проверить на мобильном
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Все страницы hhapp используют единый стиль, навигация понятна, карточки вакансий читаемы.

---

### Этап 4: Страницы userapp
**Цель**: Улучшить UX авторизации и профиля  
**Время**: 4-6 часов  
**Зависимости**: Этап 1 и 2 завершены  
**Стратегия отката**: Git branch `feature/markup-stage-4`, отдельный PR

- [ ] **4.1** `login.html` — страница входа
  - Убрать белый текст (уже в 0.3, проверить)
  - Использовать карточку (уже в 0.3)
  - Добавить ссылку "Забыли пароль?" — если view реализован в Django
  - Если нет → создать заглушку `password_reset.html` с сообщением "Функция в разработке"
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **4.2** `registration.html` — регистрация
  - То же: карточка, контрастность, валидация (через form_tags)
  - Увеличить контейнер (`col-lg-6` вместо `col-xs-12`)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **4.3** `profile.html` — профиль пользователя
  - **Перенести проверку прав во view**:
  ```python
  # userapp/views.py
  class ProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
      model = WebSiteUser
      template_name = 'userapp/profile.html'
      
      def test_func(self):
          return self.request.user.id == self.get_object().id
  ```
  - Убрать `{% if user.id == object.id %}` из шаблона
  - **Токен в карточку с кнопкой копирования**:
  ```html
  <div class="card mb-3">
    <div class="card-body">
      <h5 class="card-title">API Token</h5>
      <div class="input-group">
        <input type="text" class="form-control" value="{{ user.auth_token }}" id="apiToken" readonly>
        <button class="btn btn-outline-secondary" type="button" onclick="copyToken()">
          Копировать
        </button>
      </div>
    </div>
  </div>
  <script>
  function copyToken() {
    const token = document.getElementById('apiToken');
    token.select();
    document.execCommand('copy');
    alert('Токен скопирован');
  }
  </script>
  ```
  - Разделить на секции: Аватар, Информация, Токен, Редактирование
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **4.4** Тестирование userapp страниц
  - Регистрация → логин → профиль → logout
  - Попытка доступа к чужому профилю (должен 403)
  - Копирование токена работает
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Формы авторизации работают, профиль безопасен (проверка прав во view), токен удобно копировать.

---

### Этап 5: Accessibility и семантика
**Цель**: Привести к стандартам WCAG 2.1 AA  
**Время**: 4-6 часов  
**Зависимости**: Этапы 1-4 завершены  
**Стратегия отката**: Git branch `feature/markup-stage-5`, отдельный PR

- [ ] **5.1** Добавить alt к изображениям
  - base.html — portfolio: если не удалён, добавить осмысленный alt или удалить
  - profile.html — аватар пользователя: `alt="{{ user.username }} аватар"`
  - Заглушка для отсутствующего аватара: использовать placeholder или инициалы
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **5.2** Исправить heading hierarchy
  - Проверить все страницы: h1 → h2 → h3 без пропусков
  - index.html: `<h1>` в masthead, `<h2>` для секций, `<h3>` для подзаголовков
  - Вакансия: `<h1>` название вакансии, `<h2>` секции описания
  - **Инструмент**: HeadingsMap extension для Chrome/Firefox
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **5.3** Добавить aria-атрибуты
  - Формы: `aria-describedby` для ошибок и help_text (добавить в form_tags.py)
  - Навигация: 
    ```html
    <nav aria-label="Основная навигация">
      <a class="nav-link" href="..." aria-current="page">Home</a>
    </nav>
    ```
  - Модальные окна (если появятся в будущем): `aria-modal="true"`, `role="dialog"`
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **5.4** Keyboard navigation
  - Проверить tab-order: логичный порядок элементов
  - Добавить focus-visible стили в common.css:
  ```css
  :focus-visible {
    outline: 2px solid #0d6efd;
    outline-offset: 2px;
  }
  ```
  - Skip links для перехода к контенту (в base.html, первый элемент после `<body>`):
  ```html
  <a href="#main-content" class="visually-hidden-focusable">Перейти к содержимому</a>
  ```
  - Добавить `id="main-content"` на основной контент
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **5.5** Контрастность цветов
  - Проверить существующие цвета через WebAIM Contrast Checker
  - Белый текст на `bg-primary` (index.html masthead) — проверить соотношение ≥ 4.5:1
  - Если не проходит — затемнить `bg-primary` или осветлить текст
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Lighthouse Accessibility Score ≥ 90, навигация с клавиатуры работает, heading hierarchy корректна.

---

### Этап 6: Страницы ошибок и edge cases
**Цель**: Обработка ошибок с сохранением стиля  
**Время**: 2-3 часа  
**Зависимости**: Этап 1 завершён (base.html)  
**Стратегия отката**: Git branch `feature/markup-stage-6`, отдельный PR

- [ ] **6.1** Создать `HH/templates/404.html`
  - Использовать base.html
  - Дружелюбное сообщение + ссылки на главную и поиск:
  ```django
  {% extends "base.html" %}
  {% block header %}
  <header class="masthead">
    <div class="container text-center">
      <h1 class="text-white">404 — Страница не найдена</h1>
      <p class="text-white-75">Кажется, вы попали не туда</p>
      <a href="{% url 'hhapp:index' %}" class="btn btn-light btn-xl">На главную</a>
    </div>
  </header>
  {% endblock %}
  ```
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **6.2** Создать `HH/templates/500.html`
  - **Минимальный standalone HTML** (без зависимости от БД, т.к. ошибка может быть в БД):
  ```html
  <!DOCTYPE html>
  <html lang="ru">
  <head>
    <meta charset="UTF-8">
    <title>Ошибка сервера</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body class="bg-light">
    <div class="container text-center mt-5">
      <h1>500 — Ошибка сервера</h1>
      <p>Мы уже работаем над исправлением</p>
      <p>Если проблема повторяется, напишите на <a href="mailto:support@example.com">support@example.com</a></p>
    </div>
  </body>
  </html>
  ```
  - **Вопрос к пользователю**: Какой email указать для поддержки?
  - **Статус**: ⬜ | **Решение**: _ожидает email пользователя_

- [ ] **6.3** Включить кастомные страницы ошибок в settings.py
  - `DEBUG = False` (уже должно быть для production)
  - `ALLOWED_HOSTS = ['*']` (для тестирования локально, потом указать домен)
  - Проверить, что Django находит шаблоны 404.html, 500.html
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **6.4** Добавить обработку пустых состояний
  - index.html: если нет вакансий вообще (не только по запросу):
  ```django
  {% if not vacancies and not hh_vacancies %}
    <div class="text-center my-5">
      <p class="text-muted">Пока нет ни одной вакансии</p>
      <a href="{% url 'hhapp:vacancy_create' %}" class="btn btn-primary">Создать первую</a>
    </div>
  {% endif %}
  ```
  - profile.html: если нет токена (невозможно для DRF authtoken, но на будущее)
  - profile.html: если нет аватара — показывать placeholder или инициалы
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **6.5** Тестирование ошибок
  - Зайти на несуществующий URL → проверить 404
  - Сымитировать ошибку в view (raise Exception) → проверить 500
  - Проверить пустые состояния (очистить БД вакансий → проверить index.html)
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Страницы 404/500 существуют и стилизованы, пустые состояния обработаны.

---

### Этап 7: Тестирование и полировка
**Цель**: Проверить результат на разных устройствах и браузерах  
**Время**: 3-4 часа  
**Зависимости**: Этапы 0-6 завершены  
**Стратегия отката**: Только документирование проблем, не откатываем

- [ ] **7.1** Проверить на мобильных (responsive)
  - iOS Safari (через BrowserStack или реальное устройство)
  - Android Chrome (DevTools или реальное устройство)
  - Брейкпоинты: 375px (iPhone SE), 768px (iPad), 1024px (iPad Pro)
  - Навигация, формы, таблицы, карточки
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **7.2** Проверить на десктопе
  - Chrome (последняя версия)
  - Firefox (последняя версия)
  - Safari (macOS, если доступен)
  - Edge (Windows)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **7.3** Accessibility audit
  - Lighthouse (DevTools → Lighthouse → Accessibility)
  - Целевой score: ≥ 90
  - axe DevTools extension или WAVE (web accessibility evaluation tool)
  - Исправить критичные проблемы (contrast, missing labels)
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **7.4** Performance audit (опционально, но полезно)
  - Lighthouse Performance score
  - Если < 50 → оптимизировать изображения, отложить JS
  - SimpleLightbox — проверить, нужен ли, если portfolio удалён
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **7.5** Сделать скриншоты до/после
  - index.html (главная)
  - profile.html
  - login.html
  - vacancy.html
  - Сохранить в `docs/screenshots/markup_improvements/`
  - Добавить в README.md или отдельный документ `docs/markup_changelog.md`
  - **Статус**: ⬜ | **Комментарий**:

- [ ] **7.6** Финальный code review
  - Удалить неиспользуемый код (portfolio, если удалён)
  - Проверить консистентность отступов (использовать Prettier/Black)
  - Проверить комментарии в CSS/HTML
  - Убрать закомментированный код
  - Проверить `.gitignore` — не добавлены ли случайно изображения или кеш
  - **Статус**: ⬜ | **Комментарий**:

**Критерий готовности**: Приложение работает на всех основных браузерах и устройствах, Lighthouse Accessibility ≥ 90, скриншоты задокументированы.

---

## Вопросы к пользователю (требуют решения)

### Вопрос 1: Portfolio в base.html
**Контекст**: В base.html жёстко захардкожена галерея из 6 изображений (строки 56-98 текущего base.html). SimpleLightbox подключён только для неё.

**Ваш выбор**: **A** — Удалить portfolio и SimpleLightbox (упростить base.html, убрать неиспользуемый код)

---

### Вопрос 2: Переименование `foto` → `photo`
**Контекст**: В модели `WebSiteUser` используется поле `foto` (русское слово), хотя вся база кода на английском.

**Ваш выбор**: **A** — Переименовать в `photo` (потребует миграции, обновления шаблонов, форм — 30 минут работы)

---

### Вопрос 3: Email поддержки для 500.html
**Контекст**: На странице 500 (ошибка сервера) нужно указать контакт для сообщения о проблемах.

**Ваш выбор**: **B** — Указать заглушку `support@example.com`

---

### Вопрос 4: Anchor-навигация в index.html
**Контекст**: Сейчас index.html использует anchor-links (#about, #services, #contact) для одностраничного layout, но одновременно есть многостраничная навигация (профиль, тренажёр).

**Ваш выбор**: **A** — Оставить anchor-навигацию как есть (это допустимый паттерн для лендинга)

---

## Приоритеты

### 🔴 Критичные (ломают UX) — Этап 0
1. Навигация: кнопка Log Out без стилей
2. Навигация: отсутствует `.navbar-toggler` (мобильное меню не работает)
3. Формы: белый текст на тёмном фоне (login.html)
4. Пагинация в index.html без стилей

### 🟡 Важные (улучшают UX) — Этапы 1-4
1. Формы: `{{ form.as_p }}` → Bootstrap-стилизация
2. Страницы ошибок 404/500
3. Django messages framework
4. Breadcrumbs навигация
5. Токен в profile.html (карточка + копирование)

### 🟢 Желательные (полировка) — Этапы 5-7
1. Accessibility audit (WCAG 2.1 AA)
2. Keyboard navigation и focus styles
3. Скриншоты до/после
4. Удаление portfolio из base.html (если не используется)

---

## Зависимости между этапами

```
Этап 0 (hotfix)
   ↓
Этап 1 (инфраструктура: компоненты, base.html)
   ↓
   ├── Этап 2 (формы) ────→ Этап 3.3, Этап 4 (используют form_tags)
   │      ↓
   └── Этап 3 (hhapp) ───→ Этап 7 (тестирование)
          ↓
       Этап 5 (accessibility) ──→ Этап 7
          ↓
       Этап 6 (ошибки) ─────→ Этап 7
```

**Можно делать параллельно**:
- Этапы 3 и 4 (после завершения этапов 1-2)
- Этапы 5 и 6 (после завершения этапов 1-4)

**Нельзя начинать без предыдущих**:
- Этап 2 требует Этап 1 (компоненты)
- Этап 3 требует Этап 2.5 (формы для vacancy_create.html)
- Этап 7 требует все предыдущие

---

## Оценка времени

| Этап | Описание | Время | Сложность |
|------|----------|-------|-----------|
| **0** | Критические исправления (hotfix) | 1-2 ч | Низкая |
| **1** | Базовая инфраструктура | 4-6 ч | Средняя |
| **2** | Формы | 6-8 ч | Высокая |
| **3** | Страницы hhapp | 6-8 ч | Средняя |
| **4** | Страницы userapp | 4-6 ч | Средняя |
| **5** | Accessibility и семантика | 4-6 ч | Средняя |
| **6** | Страницы ошибок и edge cases | 2-3 ч | Низкая |
| **7** | Тестирование и полировка | 3-4 ч | Низкая |
| **Итого** | | **30-43 часа** | |

**Реалистичная оценка с учётом непредвиденных проблем**: 40-50 часов (5-7 рабочих дней при работе 8 ч/день).

---

## Метрики успеха

- [ ] Все формы работают с Bootstrap-стилями
- [ ] Lighthouse Accessibility Score ≥ 90
- [ ] Lighthouse Performance Score ≥ 70 (желательно)
- [ ] Нет визуальных различий между desktop и mobile (responsive работает)
- [ ] Все интерактивные элементы доступны с клавиатуры
- [ ] Страницы ошибок 404/500 существуют и стилизованы
- [ ] Django messages работают (проверено на login/logout)
- [ ] Мобильное меню работает (navbar-toggler)
- [ ] Нет регрессий в существующей функциональности (hhapp, userapp, candidate_trainer)

---

## Стратегия отката изменений

### Откат отдельного этапа
```bash
# Если этап в отдельной ветке
git checkout main
git branch -D feature/markup-stage-N

# Если этап в main, но последний коммит
git revert HEAD

# Если этап в main, несколько коммитов назад
git revert <commit-hash>
```

### Откат изменений base.html (критичный файл)
- **Перед изменением base.html**: создать копию `base.html.backup`
- **После изменения**: проверить ВСЕ страницы вручную (см. чеклист 1.5)
- **Если сломано**: `git checkout HEAD~1 HH/templates/base.html`

### Проверка перед merge в main
1. Запустить `docker compose up --build`
2. Проверить все основные страницы:
   - index.html (главная)
   - login/logout/registration
   - profile
   - vacancy_create, vacancy_detail
   - candidate_trainer/dashboard
3. Проверить на мобильном (DevTools, 375px)
4. Проверить консоль браузера (нет JS ошибок)
5. Только после этого → merge

---

## Git workflow

### Commit messages
- `fix: исправить стили кнопки Log Out`
- `feat: добавить компоненты form_field и pagination`
- `refactor: переместить portfolio в отдельный блок`
- `a11y: добавить aria-labels в навигацию`
- `docs: добавить скриншоты до/после в markup_changelog.md`

### Branch naming
- `feature/markup-stage-0-hotfix`
- `feature/markup-stage-1-infrastructure`
- `feature/markup-stage-2-forms`
- ...
- `feature/markup-stage-7-polish`

### Pull Requests (опционально, для code review)
- Каждый этап — отдельный PR
- В описании PR: что сделано, скриншоты до/после, чеклист проверки
- Reviewer проверяет: нет регрессий, accessibility, responsive

---

## Примечания

- Все изменения должны сохранять обратную совместимость с существующими view
- Не менять логику Django (forms, views, models) без явной необходимости
- SimpleLightbox — удалить, если portfolio удалён (экономия 20 КБ JS)
- Bootstrap 5.2.3 уже используется — не обновлять до 5.3 без необходимости
- Шрифты Merriweather уже подключены — использовать их, не добавлять новые

---

**Статусы задач**:
- ⬜ Не начато
- 🔄 В процессе
- ✅ Выполнено
- ⏸️ Приостановлено (ожидает решения пользователя)
- ❌ Отменено

**Формат комментариев**: краткое описание проделанной работы, найденных проблем, принятых решений.

---

## Дополнительно: Унификация с candidate_trainer (вынесено из основного плана)

**Документ**: `docs/future_improvements.md` (создать отдельно)

**Цель**: Опциональное сближение стилей hhapp/userapp с candidate_trainer

**Вопрос к пользователю**: Нужна ли единая палитра для всего проекта?

**Варианты**:
- **A**: Оставить два стиля (hhapp/userapp — Bootstrap defaults, candidate_trainer — кастомный)
- **B**: Перенести палитру из candidate_trainer в common.css и адаптировать все приложения

**Время**: 8-10 часов (если вариант B)

**Не включено в основной план**, т.к. это отдельная инициатива, не влияющая на функциональность.
