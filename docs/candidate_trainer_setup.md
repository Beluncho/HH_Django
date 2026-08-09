# Запуск и настройка Candidate Trainer

Эта инструкция описывает локальный запуск проекта через Docker Compose,
настройку HH.ru, LLM, embeddings и подключение RAG к тестовому
собеседованию.

## 1. Что требуется разным функциям

| Функция | HH API | Embeddings | LLM | RAG-коллекция |
|---|---:|---:|---:|---:|
| Публичный поиск на главной | Да | Нет | Нет | Нет |
| Анализ до 20 вакансий | Да | Да | Нет | `skill-core` создаётся автоматически |
| Объяснение навыка | Нет | Да | Да | Непустая `skill-core` |
| Собеседование без interview RAG | Нет | Да | Да | Не требуется |
| Собеседование с interview RAG | Нет | Да | Да | Непустая `interview` |

Важно: `INTERVIEW_RAG_ENABLED=1` только разрешает retrieval. Этот флаг не
создаёт базу знаний и не добавляет в неё документы.

В текущей реализации RAG работает локально:

- текст разбивается на фрагменты;
- embeddings строятся локальной CPU-моделью;
- векторы сохраняются в PostgreSQL как JSON;
- релевантность считается точным cosine similarity;
- отдельный векторный сервер и pgvector для текущего объёма не нужны.

## 2. Быстрый запуск через Docker

Команды выполняются из корня репозитория `HH_Django`.

Для этого проекта основной способ запуска — Docker Compose. Файл `.env.dev`
передаётся контейнерам через `env_file` в `docker-compose.yml`. Если
запустить `python manage.py runserver` напрямую из каталога `HH`, файл
`.env.dev` сам по себе не загрузится: настройки читаются из переменных
окружения процесса.

Создайте рабочий файл окружения:

```bash
cp .env.dev.example .env.dev
```

Откройте `.env.dev` и как минимум замените:

```env
SECRET_KEY=your-local-secret
HH_USER_AGENT=HH_Django/1.0 (your-real-email@example.com)
HH_ACCESS_TOKEN=your-hh-access-token
```

Запустите PostgreSQL и Django:

```bash
docker compose up -d --build
```

При старте контейнер `web` сам ожидает PostgreSQL и выполняет миграции.
Первый build и первый вызов embeddings могут занять больше времени:
устанавливается PyTorch CPU и загружается embedding-модель.

Проверьте состояние:

```bash
docker compose ps
docker compose logs --tail=100 web
docker compose exec web python manage.py check
```

Создайте администратора:

```bash
docker compose exec web python manage.py createsuperuser
```

Адреса development-окружения:

- приложение: `http://127.0.0.1:8000/`;
- регистрация: `http://127.0.0.1:8000/user/registration`;
- вход: `http://127.0.0.1:8000/user/login/`;
- тренажёр: `http://127.0.0.1:8000/trainer/`;
- админ-панель: `http://127.0.0.1:8000/admin/`.

Остановка без удаления базы:

```bash
docker compose down
```

Не используйте `docker compose down -v`, если нужно сохранить PostgreSQL и
кеш embedding-модели: параметр `-v` удаляет именованные volumes.

Если Docker использовать нельзя, нужно заранее экспортировать переменные из
`.env.dev` в текущий shell и запускать команды из каталога `HH`. Самый
надёжный вариант для текущего проекта всё равно Docker Compose, потому что
он одновременно поднимает PostgreSQL и передаёт полный набор настроек.

## 3. Полный пример `.env.dev`

Ниже показана структура, а не готовые секреты:

```env
DEBUG=1
SECRET_KEY=replace-with-a-random-local-secret
ALLOWED_HOSTS=localhost 127.0.0.1 [::1]

POSTGRES_ENGINE=django.db.backends.postgresql
POSTGRES_DB=django_db
POSTGRES_USER=django_user
POSTGRES_PASSWORD=django_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE=postgres

HH_API_DOMAIN=https://api.hh.ru/
HH_ACCESS_TOKEN=replace-with-hh-token
HH_REQUIRE_ACCESS_TOKEN=1
HH_USER_AGENT=HH_Django/1.0 (your-real-email@example.com)
HH_REQUEST_TIMEOUT=10
HH_ANALYSIS_LIMIT=20

EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
EMBEDDING_DEVICE=cpu
EMBEDDING_CACHE_DIR=/app/.model-cache

LLM_PROVIDER=openai_compatible
LLM_MODEL=replace-with-provider-model-id
LLM_API_KEY=replace-with-provider-api-key
LLM_API_URL=https://provider.example/v1/chat/completions
LLM_TIMEOUT=30
LLM_MAX_TOKENS=1200

INTERVIEW_RAG_ENABLED=1
KNOWLEDGE_IMPORT_MAX_BYTES=2097152
```

После изменения `.env.dev` пересоздайте контейнер `web`, чтобы он получил
новые переменные:

```bash
docker compose up -d --force-recreate web
```

Обычный `docker compose restart web` может перезапустить контейнер со
старыми значениями окружения.

## 4. Настройка HH API

Для анализа вакансий используются:

- `HH_API_DOMAIN` — базовый адрес API;
- `HH_ACCESS_TOKEN` — access token;
- `HH_REQUIRE_ACCESS_TOKEN` — обязательность токена;
- `HH_USER_AGENT` — непустой корректный User-Agent с контактом;
- `HH_REQUEST_TIMEOUT` — timeout одного HTTP-запроса;
- `HH_ANALYSIS_LIMIT` — количество карточек, максимум 20.

При `HH_REQUIRE_ACCESS_TOKEN=1` и пустом `HH_ACCESS_TOKEN` анализ завершится
ошибкой до обращения к HH.ru.

Для локальной диагностики можно установить:

```env
HH_REQUIRE_ACCESS_TOKEN=0
```

Это только отключает внутреннюю обязательную проверку. Возможность
фактического запроса без токена всё равно определяется HH API.

## 5. Настройка embeddings

Рекомендуемая конфигурация:

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
EMBEDDING_DEVICE=cpu
EMBEDDING_CACHE_DIR=/app/.model-cache
```

Модель загружается лениво при первом анализе вакансий, импорте документа
или retrieval. Docker volume `model_cache` сохраняет загрузку между
перезапусками контейнера.

Провайдер `hash` есть для тестов и технической диагностики:

```env
EMBEDDING_PROVIDER=hash
EMBEDDING_MODEL=local-hash-v1
EMBEDDING_DIMENSION=384
```

Он не является полноценной семантической моделью и не рекомендуется для
рабочего RAG.

После смены `EMBEDDING_MODEL` или `EMBEDDING_DIMENSION` выполните явную
переиндексацию:

```bash
docker compose exec web \
  python manage.py reindex_embeddings --collection all
```

Можно переиндексировать только нужную коллекцию:

```bash
docker compose exec web \
  python manage.py reindex_embeddings --collection interview
```

## 6. Настройка LLM

Анализ вакансий работает без LLM. Объяснение навыков и интервью требуют
LLM.

Значение:

```env
LLM_PROVIDER=disabled
```

явно отключает LLM. При нём вопрос собеседования не будет сформирован.

Текущий адаптер ожидает HTTP API, совместимый с OpenAI Chat Completions:

- POST-запрос на адрес из `LLM_API_URL`;
- Bearer token из `LLM_API_KEY`;
- поля `model`, `messages`, `max_tokens`, `temperature`;
- ответ в `choices[0].message.content`.

Пример конфигурации:

```env
LLM_PROVIDER=openai_compatible
LLM_MODEL=provider-model-id
LLM_API_KEY=provider-secret-key
LLM_API_URL=https://provider.example/v1/chat/completions
LLM_TIMEOUT=30
LLM_MAX_TOKENS=1200
```

`LLM_PROVIDER` сейчас используется как имя провайдера в сохранённых
результатах. Любое значение, кроме `disabled`, включает
OpenAI-compatible клиент. Конкретные `LLM_MODEL` и `LLM_API_URL` нужно
взять из документации выбранного провайдера.

Для локального OpenAI-compatible сервера ключ всё равно должен быть
непустым, потому что текущий клиент проверяет наличие всех четырёх
параметров и отправляет `Authorization: Bearer ...`.

После редактирования `.env.dev`:

```bash
docker compose up -d --force-recreate web
docker compose exec web python manage.py shell -c \
  "from django.conf import settings; print({'provider': settings.LLM_PROVIDER, 'model': settings.LLM_MODEL, 'url_set': bool(settings.LLM_API_URL), 'key_set': bool(settings.LLM_API_KEY)})"
```

Команда показывает только наличие настроек и не печатает API-ключ.

## 7. Подключение RAG к собеседованию

Для включения нужны все условия:

1. `LLM_PROVIDER` не равен `disabled`.
2. `LLM_MODEL`, `LLM_API_KEY` и `LLM_API_URL` заполнены.
3. `INTERVIEW_RAG_ENABLED=1`.
4. Существует глобальная включённая коллекция `interview`.
5. В коллекции есть хотя бы один документ и его chunks с embeddings.
6. После настройки создана новая сессия собеседования.

### 7.1. Включите флаг

В `.env.dev`:

```env
INTERVIEW_RAG_ENABLED=1
```

Затем пересоздайте web-контейнер:

```bash
docker compose up -d --force-recreate web
```

Флаг копируется в поле `InterviewSession.interview_rag_enabled` в момент
создания сессии. Поэтому изменение `.env.dev` не меняет уже созданные
собеседования. После переключения начните новое собеседование.

### 7.2. Подготовьте материал

Команда импорта принимает UTF-8 файлы:

- `.txt`;
- `.md`;
- `.json`.

Для JSON предпочтителен формат:

```json
{
  "content": "Вопросы, эталонные ответы и рубрика оценки..."
}
```

Размер одного файла ограничен `KNOWLEDGE_IMPORT_MAX_BYTES`. Значение по
умолчанию `2097152` равно 2 MiB.

При Docker-разработке каталог `HH/` на хосте смонтирован в `/app` внутри
контейнера. Например, файл:

```text
HH/knowledge_sources/python_backend_interview.md
```

будет доступен контейнеру как:

```text
/app/knowledge_sources/python_backend_interview.md
```

### 7.3. Импортируйте документ

```bash
docker compose exec web python manage.py import_knowledge \
  /app/knowledge_sources/python_backend_interview.md \
  --collection interview \
  --source-type interview \
  --title "Python backend: вопросы и рубрики" \
  --external-id "python-backend-interview-v1"
```

Дополнительные параметры:

- `--source-url` — URL происхождения материала;
- `--external-id` — стабильный внешний идентификатор;
- `--title` — отображаемое название;
- `--source-type` — `imported`, `verified`, `generated` или `interview`;
- `--skill` — связать документ с конкретным нормализованным навыком.

Для проверенного внешнего материала:

```bash
docker compose exec web python manage.py import_knowledge \
  /app/knowledge_sources/django_interview.md \
  --collection interview \
  --source-type verified \
  --skill Django \
  --title "Django interview handbook" \
  --source-url "https://source.example/django"
```

Сгенерированный LLM-текст импортируйте только с маркировкой:

```text
--source-type generated
```

### 7.4. Проверьте коллекцию

```bash
docker compose exec web python manage.py shell -c \
  "from candidate_trainer.models import KnowledgeCollection, KnowledgeChunk; c=KnowledgeCollection.objects.filter(owner__isnull=True, slug='interview').first(); print({'exists': bool(c), 'enabled': c.enabled if c else None, 'documents': c.documents.count() if c else 0, 'chunks': KnowledgeChunk.objects.filter(document__collection=c).count() if c else 0})"
```

Ожидаемый смысл результата:

```text
{'exists': True, 'enabled': True, 'documents': 1, 'chunks': 1}
```

Количество chunks может быть больше одного: длинный документ автоматически
разбивается на фрагменты.

Коллекцию также можно проверить в админ-панели:

```text
/admin/candidate_trainer/knowledgecollection/
```

У глобальной interview-коллекции должны быть:

- пустой `owner`;
- `slug = interview`;
- тип `Собеседование`;
- включённый `enabled`.

### 7.5. Запустите пользовательский сценарий

1. Зарегистрируйтесь и войдите.
2. Откройте `/trainer/`.
3. Введите название вакансии и выберите регион.
4. Дождитесь завершения анализа.
5. Откройте анализ и нажмите «Начать собеседование».
6. Для новой сессии первый вопрос использует до четырёх найденных
   фрагментов `interview`, если коллекция непустая.
7. При отправке ответа retrieval выполняется ещё раз для оценки и
   следующего вопроса.

Если коллекция выключена, отсутствует или пуста, приложение не падает:
собеседование продолжает работу на LLM без interview RAG.

## 8. Чем `skill-core` отличается от `interview`

`skill-core` обязателен для объяснений навыков. Во время анализа вакансий
он создаётся автоматически и наполняется фрагментами описаний HH.ru,
связанными с найденными навыками.

Дополнительный материал можно импортировать вручную:

```bash
docker compose exec web python manage.py import_knowledge \
  /app/knowledge_sources/python_guide.md \
  --collection skill-core \
  --source-type verified \
  --skill Python \
  --title "Python guide"
```

`interview` содержит вопросы, эталонные ответы, рубрики и методические
материалы. Она создаётся только при первом ручном импорте.

`user-analytics` создаётся автоматически отдельно для каждого пользователя
после успешной оценки ответа. Сырой текст ответа в эту RAG-коллекцию не
копируется; сохраняется структурированный вывод.

## 9. Диагностика

### «LLM не настроен»

Причина: `LLM_PROVIDER=disabled` или не заполнены `LLM_MODEL`,
`LLM_API_URL`, `LLM_API_KEY`.

Проверьте настройки без вывода секрета:

```bash
docker compose exec web python manage.py shell -c \
  "from django.conf import settings; print(settings.LLM_PROVIDER, settings.LLM_MODEL, bool(settings.LLM_API_URL), bool(settings.LLM_API_KEY))"
```

### Первый вопрос не появляется

Проверьте:

```bash
docker compose logs --tail=200 web
```

Основные причины:

- LLM отключён;
- endpoint или модель указаны неверно;
- API-ключ не принят провайдером;
- endpoint не совместим с Chat Completions;
- ответ LLM пустой или имеет неожиданный формат.

### `INTERVIEW_RAG_ENABLED=1`, но retrieval не используется

Проверьте по порядку:

1. web-контейнер пересоздан после изменения `.env.dev`;
2. создана новая сессия собеседования;
3. глобальная коллекция `interview` существует;
4. `enabled=True`;
5. в коллекции есть документы и chunks;
6. модель и размерность коллекции совпадают с текущими embedding-настройками.

В интерфейсе сейчас нет отдельного индикатора, показывающего использованные
interview-фрагменты. Наличие RAG определяется перечисленными условиями.

### Требуется переиндексация

Если менялись embedding-модель или размерность:

```bash
docker compose exec web \
  python manage.py reindex_embeddings --collection all
```

Не смешивайте в одной базе embeddings разных моделей.

### Не загружается embedding-модель

Проверьте:

- доступ контейнера к сети при первой загрузке;
- свободное место;
- наличие volume `model_cache`;
- соответствие `EMBEDDING_DIMENSION` реальной размерности модели;
- логи `docker compose logs web`.

### Анализ не запускается из-за HH token

При текущем безопасном значении:

```env
HH_REQUIRE_ACCESS_TOKEN=1
```

нужно заполнить `HH_ACCESS_TOKEN`. Также укажите корректный
`HH_USER_AGENT`.

## 10. Проверки проекта

После настройки:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py makemigrations --check --dry-run
```

Unit-тесты используют fakes и не должны обращаться к HH.ru, LLM-провайдеру
или Hugging Face.

## 11. Production

Для production создайте `.env.prod`:

```bash
cp .env.prod.example .env.prod
```

Заполните сильные секреты, домены, HH и LLM. Для model cache в production
используется путь:

```env
EMBEDDING_CACHE_DIR=/home/app/web/.model-cache
```

Запуск:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Приложение доступно через Nginx на:

```text
http://127.0.0.1:1337/
```

Импорт interview-документа в production-контейнер требует, чтобы файл был
доступен внутри контейнера. Один из вариантов:

```bash
docker compose -f docker-compose.prod.yml cp \
  ./python_backend_interview.md \
  web:/tmp/python_backend_interview.md

docker compose -f docker-compose.prod.yml exec web \
  python manage.py import_knowledge \
  /tmp/python_backend_interview.md \
  --collection interview \
  --source-type interview \
  --title "Python backend interview"
```
