# Чеклист тестирования candidate_trainer

## Этап 1: Глобальные объяснения навыков

### Модели и миграции
- [x] Миграция 0003 применяется без ошибок
- [x] SkillExplanation.skill - обязательное поле
- [x] SkillExplanation.user - nullable (NULL = глобальное)
- [x] SkillExplanation.is_active работает корректно
- [x] Уникальный constraint (skill, user) для is_active=True
- [x] Индекс на (skill, user, is_active)

### Сервисы
- [x] `get_or_create_global_explanation()` создаёт глобальное объяснение
- [x] Автообновление объяснений старше 365 дней
- [x] Обработка ошибок LLM (RAGContextUnavailableError)
- [x] Корректные импорты в explanation.py

### Views
- [x] `analysis_detail()` загружает global_explanation через prefetch
- [x] `skill_explanation()` использует новый сервис
- [x] Импорт Count, Prefetch присутствует

## Этап 2: Sticky sidebar с навигацией

### HTML структура
- [x] `.analysis-layout` grid layout (240px + 1fr)
- [x] `.analysis-sidebar` с навигацией
- [x] Scroll targets с ID: #overview, #skills, #interviews
- [x] Badges с счётчиками навыков и интервью

### CSS стили
- [x] `.analysis-sidebar` sticky top: 80px
- [x] `.scroll-target` scroll-margin-top: 80px
- [x] `.sidebar-link.active` подсветка
- [x] Media query @media (max-width: 992px) скрывает sidebar

### JavaScript
- [x] Smooth scroll по клику на ссылки
- [x] Intersection Observer отслеживает видимые секции
- [x] Active класс применяется к текущей секции

### Визуальная проверка
- [ ] Sidebar фиксирован при скролле
- [ ] Подсветка активной секции работает
- [ ] Плавный переход между секциями
- [ ] На мобильных (<992px) sidebar скрыт
- [ ] Счётчики показывают правильные значения

## Этап 3: Markdown рендеринг

### Template filters
- [x] `render_markdown` фильтр зарегистрирован
- [x] Поддержка fenced_code, tables, nl2br
- [x] `strip_list_marker` удаляет * - + из начала строки
- [x] Regex `^\s*[\*\-\+]\s*` работает корректно

### Применение в шаблонах
- [x] `analysis_detail.html`: `{{ global_explanation.content|render_markdown }}`
- [x] `interview.html`: `{{ message.content|render_markdown }}`
- [x] `interview.html`: `{{ insight.summary|render_markdown }}`
- [x] `interview.html`: `{{ gap|strip_list_marker }}` в <li>
- [x] `interview.html`: `{{ recommendation|strip_list_marker }}` в <li>

### Тестирование
- [ ] **Объяснения навыков**: markdown корректно отображается
- [ ] **Сообщения интервью**: форматирование сохранено
- [ ] **Инсайты summary**: bold/italic работают
- [ ] **Списки пробелов**: маркеры * - + удалены
- [ ] **Списки рекомендаций**: маркеры * - + удалены
- [ ] Блоки кода с ``` отображаются правильно
- [ ] Таблицы форматируются корректно

## Регрессионное тестирование

### Создание анализа
- [ ] Поиск вакансий работает
- [ ] Анализ создаётся и сохраняется
- [ ] Навыки извлекаются и нормализуются
- [ ] Частота навыков считается корректно

### Интервью
- [ ] Создание новой сессии
- [ ] Генерация вопросов
- [ ] Сохранение ответов
- [ ] Создание инсайтов
- [ ] Завершение интервью

### Права доступа
- [ ] Анонимный -> редирект на логин
- [ ] Пользователь видит только свои анализы
- [ ] Пользователь видит только свои интервью

## Docker тестирование

```bash
# Проверка контейнеров
docker-compose ps

# Применение миграций
docker-compose exec web python manage.py migrate

# Проверка статики
docker-compose exec web python manage.py collectstatic --noinput

# Создание тестовых данных
docker-compose exec web python /app/create_test_data.py

# Запуск тестов
docker-compose exec web python manage.py test candidate_trainer
```

## Playwright UI тесты

```bash
# Установка (локально)
pip install playwright pytest-playwright
playwright install chromium

# Запуск автотестов
python test_ui_auto.py      # Автоматический тест
python test_full.py          # Полный тест с авторизацией
```

## Ручная проверка markdown

1. Откройте http://localhost:8000/trainer/
2. Авторизуйтесь (admin/admin или ваш пользователь)
3. Откройте любой анализ
4. Проверьте объяснения навыков - должен быть форматированный текст без markdown разметки
5. Откройте интервью
6. Проверьте списки "Пробелы" и "Рекомендации" - НЕ должно быть звёздочек/минусов в начале

**Ожидаемое поведение:**
- ❌ НЕПРАВИЛЬНО: `* Недостаточно информации`
- ✅ ПРАВИЛЬНО: `Недостаточно информации`

## Коммиты

Все изменения зафиксированы в истории:
- Stage 1: Модели, миграция, сервисы (множественные коммиты)
- Stage 2: Sidebar навигация (1 коммит)
- Stage 3: Markdown рендеринг (2+ коммита)
- Fixes: Исправления импортов, regex (отдельные коммиты)

## Проверка перед пушем

- [ ] Все миграции применены
- [ ] Нет незакоммиченных изменений
- [ ] Django tests проходят
- [ ] Markdown маркеры удалены визуально
- [ ] Sidebar навигация работает
- [ ] Скриншоты сделаны для документации
