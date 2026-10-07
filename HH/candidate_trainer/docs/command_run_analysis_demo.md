# Команда `run_analysis_demo`

Локальный прогон пайплайна анализа вакансий без UI и без Docker. Используется для получения
«первых результатов» этапа 3.

> Статус: команда реализована и проверена (`tests/test_demo_commands.py`).
> Служебный план работ в git не хранится.

## Что делает

1. ищет до N вакансий по запросу и региону через HH API;
2. нормализует и агрегирует навыки (частота = число вакансий, где встретился навык);
3. печатает таблицу топ-навыков;
4. по флагу `--explain` генерирует объяснение навыка через LLM.

## Подготовка окружения (один раз)

Нужен Python 3.12 — та же версия, что в `HH/Dockerfile`.

```bash
cd <корень репозитория>
python -m venv venv

# Windows (git bash)
venv/Scripts/python.exe -m pip install -r HH/requirements.txt
# Linux / macOS: . venv/bin/activate && pip install -r HH/requirements.txt
```

Полный `HH/requirements.txt` тянет `torch` (~2 ГБ), но для базового прогонщика он не обязателен.
Минимум — `Django`, `djangorestframework`, `requests`.

| Пакет | Нужен локально |
|---|---|
| `Django`, `djangorestframework`, `requests` | да, всегда |
| `torch`, `sentence-transformers` | только при `EMBEDDING_PROVIDER=sentence_transformers`; с `hash` не нужны |
| `psycopg2-binary` | нет: локально используется SQLite |
| `gunicorn` | нет: это production-сервер, локально запускается `manage.py` |
| `pytz` | нет: Django 5 обходится без него |

### Реальные embeddings: `torch` + `sentence-transformers`

Нужны, если запускать без `--embedding hash`, то есть с `EMBEDDING_PROVIDER=sentence_transformers`,
а также для эксперимента `run_experiment embedding`, который сравнивает оба провайдера.

```bash
# Windows (git bash), из корня репозитория
venv/Scripts/python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
venv/Scripts/python.exe -m pip install sentence-transformers==3.4.1
```

```bash
# Linux / macOS
. venv/bin/activate
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==3.4.1
```

Версии совпадают с `HH/requirements.txt`. Сборка torch — **CPU-версия**, как в `HH/Dockerfile`:
GPU не требуется, но на диске это ~2–3 ГБ (сам wheel 206 МБ, остальное — зависимости:
`sympy`, `networkx`, `jinja2`, `filelock`, `fsspec`, а у `sentence-transformers` — `numpy`,
`scipy`, `scikit-learn`, `transformers`, `tokenizers`, `huggingface-hub`). Скачивание 206 МБ
может оборваться по таймауту — тогда повторите ту же команду с `--timeout 300 --retries 10`.

Модель `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~470 МБ) скачивается
при первом обращении и кешируется в `EMBEDDING_CACHE_DIR` (локально по умолчанию
`HH/.model-cache`). Интернет нужен только для этой первой загрузки.

**Порядок важен.** Если коллекция `skill-core` уже наполнена hash-векторами, переключение
провайдера без переиндексации смешает векторы разных моделей — поиск по ним станет мусором:

```bash
# 1. в .env.local поменять ДВЕ строки:
#    EMBEDDING_PROVIDER=sentence_transformers
#    EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# 2. пересобрать векторы коллекции
./run_local.sh reindex_embeddings
# 3. пересчитать анализ этой моделью, иначе навыки останутся с hash-векторами
./run_local.sh run_analysis_demo "Python-разработчик" --area 1 --force
```

Шаблоны `.env.dev.example`, `.env.prod.example` и `.env.local.example` уже поставляются с этой
парой значений, поэтому шаг 1 нужен только при возврате к `hash` — и тогда меняйте **обе**
строки сразу.

`EMBEDDING_MODEL` менять обязательно вместе с провайдером: `local-hash-v1` — это имя **не**
модели Hugging Face. Если оставить его при `EMBEDDING_PROVIDER=sentence_transformers`,
библиотека попытается скачать модель с таким именем и упадёт с ошибкой вида «не удалось
загрузить локальную embedding-модель». Флаг `--embedding sentence_transformers` берёт имя
модели из настроек, поэтому без правки `EMBEDDING_MODEL` он тоже не сработает.

Обратный переход (`EMBEDDING_PROVIDER=hash` при `EMBEDDING_MODEL=<реальная модель>`) ломать
ничего не будет: команды подставят имя `local-hash-v1` сами.

### Файл окружения и миграции

```bash
cp .env.local.example .env.local   # подставить только секреты: SECRET_KEY, HH_ACCESS_TOKEN, LLM_API_KEY
./run_local.sh migrate
```

Значения с пробелами и скобками (`HH_USER_AGENT`, `ALLOWED_HOSTS`) обязательно пишите
в кавычках: файл загружается шеллом (`set -a; . ./.env.local`), и строка без кавычек
ломает запуск с `syntax error` или `command not found`.

`EMBEDDING_CACHE_DIR` задавать не нужно. В `.env.dev` там стоит контейнерный путь
`/app/.model-cache`, и если скопировать строку как есть, то на Windows под git-bash MSYS
перепишет её в `C:/Program Files/Git/app/.model-cache` — модель (458 МБ) скачается внутрь
каталога установки Git. Без этой переменной используется локальный `HH/.model-cache`,
он добавлен в `.gitignore`.

**Про `migrate`.** Django не применяет миграции сам: ни `runserver`, ни management-команды
этого не делают. В Docker `python manage.py migrate --noinput` выполняет `HH/entrypoint.sh`
при каждом старте контейнера, поэтому там об этом думать не нужно. Локально `run_local.sh`
ничего не применяет — он только экспортирует `.env.local` и передаёт аргументы в `manage.py`,
так что `migrate` надо выполнить один раз вручную (и повторить, если в репозитории появились
новые миграции).

Признак, что шаг пропущен: `OperationalError: no such table: candidate_trainer_vacancyanalysis`.
Обе команды прогонщика проверяют это заранее и вместо трассировки пишут
`В базе нет таблиц candidate_trainer — миграции не применены. Выполните один раз: ./run_local.sh migrate`.

`migrate` не разрушительный: применяются только миграции, которых нет в журнале Django
(таблица `django_migrations`), создаются недостающие таблицы, существующие данные не
переписываются. Если `HH/db.sqlite3` остался от прежней версии проекта, для него это просто
означает, что таблицы нового приложения создаются поверх уже готовой базы.

## Как запустить

Рекомендуется через launcher — он подгружает `.env.local` в окружение:

```bash
./run_local.sh run_analysis_demo "Python-разработчик" --area 1
```

Напрямую, если переменные уже экспортированы в терминал:

```bash
cd HH && python manage.py run_analysis_demo "Python-разработчик" --area 1
```

## Параметры

| Параметр | Обязательный | По умолчанию | Что меняет |
|---|---|---|---|
| `query` | да | — | название вакансии или специальности, 2–200 символов |
| `--area` | нет | `1` (Москва) | регион, id из `settings.HH_AREA_CHOICES` |
| `--limit` | нет | `HH_ANALYSIS_LIMIT` (20) | сколько вакансий брать, 1–20 |
| `--embedding` | нет | `EMBEDDING_PROVIDER` | `hash` (быстро, без torch) или `sentence_transformers` |
| `--explain` | нет | выключено | сгенерировать объяснение топ-навыка через LLM |
| `--force` | нет | выключено | пересчитать уже готовый анализ того же запроса и региона |
| `--user` | нет | первый существующий или `demo` | от чьего имени выполняется анализ |

### Регионы (`--area`)

Значения берутся из `settings.HH_AREA_CHOICES`:

`1` Москва · `2` Санкт-Петербург · `3` Екатеринбург · `4` Новосибирск ·
`66` Нижний Новгород · `88` Казань · `76` Ростов-на-Дону · `104` Челябинск ·
`99` Уфа · `113` Россия.

## Что печатает

Сначала параметры прогона — они выводятся **до** обращения к HH API, чтобы терминал не
молчал, пока идут запросы:

```text
Запрос: Python-разработчик
Регион: Москва (area=1)
Пользователь: bel
Embeddings: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Ищу вакансии через HH API, беру до 20 шт. Это может занять до минуты...
```

Затем таблицу топ-навыков:

```text
РАНГ  НАВЫК                    ВАКАНСИЙ  ДОЛЯ     ВАРИАНТЫ НАПИСАНИЯ
1     Python                   18/20     90.00%   python, Python 3
2     Django                   14/20     70.00%   django, Джанго
...
```

При `--explain` дополнительно — текст объяснения и список источников, на которые он опирался.

## Примеры

```bash
# быстрый прогон: без LLM и без тяжёлых зависимостей
./run_local.sh run_analysis_demo "Python-разработчик" --area 1 --embedding hash

# другой регион и меньше вакансий
./run_local.sh run_analysis_demo "Data Analyst" --area 2 --limit 10

# с объяснением навыка (нужны LLM_* в .env.local)
./run_local.sh run_analysis_demo "Python-разработчик" --area 1 --explain
```

## Типичные ошибки

| Сообщение | Причина | Что сделать |
|---|---|---|
| `В базе нет таблиц candidate_trainer — миграции не применены` | локально ни разу не выполнялся `migrate` | `./run_local.sh migrate` |
| не настроен `HH_ACCESS_TOKEN` | пустой токен при `HH_REQUIRE_ACCESS_TOKEN=1` | заполнить токен в `.env.local` |
| LLM не настроен | `LLM_PROVIDER=disabled` или пустые `LLM_MODEL`/`LLM_API_URL`/`LLM_API_KEY` | заполнить `LLM_*` либо убрать `--explain` |
| LLM-сервис временно недоступен | чаще всего в `LLM_API_URL` указана база (`https://host/v1`) вместо полного endpoint'а `/chat/completions` — клиент отправляет POST ровно по этому URL и получает 404 | указать полный адрес endpoint'а |
| `LLM вернул пустой ответ` | reasoning-модель израсходовала весь лимит на «размышление» (оно тарифицируется как выход) и вернула пустой текст, в ответе `finish_reason: length` | поднять `LLM_MAX_TOKENS` — для объяснения навыка хватает 1600 — или взять модель без reasoning |
| HTTP 400 `Unsupported parameter: 'max_tokens'` | модель принимает только `max_completion_tokens` | `LLM_MAX_TOKENS_PARAM=max_completion_tokens` |
| HTTP 400 `Unsupported value: 'temperature'` | модель принимает только значение по умолчанию | оставить `LLM_TEMPERATURE=` пустым — параметр не будет отправлен |
| ответ оборван на полуслове | упёрся в `LLM_MAX_TOKENS` | поднять лимит; признак — `finish_reason: length` в сыром ответе |
| `sentence_transformers` недоступен, `No module named 'torch'` | не установлены зависимости для реальных embeddings | см. раздел «Реальные embeddings» |
| нет содержательных фрагментов базы знаний | коллекция `skill-core` пуста для навыка | повторить анализ (коллекция наполняется автоматически) |
| HH.ru временно недоступен | сеть или лимиты HH | повторить позже, проверить `HH_USER_AGENT` |

## Связанные настройки `.env.local`

`HH_ACCESS_TOKEN`, `HH_USER_AGENT`, `HH_REQUIRE_ACCESS_TOKEN`, `HH_ANALYSIS_LIMIT`,
`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `LLM_PROVIDER`, `LLM_MODEL`,
`LLM_API_URL`, `LLM_API_KEY`, `LLM_MAX_TOKENS`, `LLM_MAX_TOKENS_PARAM`, `LLM_TEMPERATURE`.

Все шаблоны (`.env.dev.example`, `.env.prod.example`, `.env.local.example`) поставляются с уже
заполненным блоком LLM: провайдер, модель `google/gemini-2.5-flash-lite`, полный адрес
endpoint'а и лимит 1600. Подставить нужно только сам ключ `LLM_API_KEY`.

Предупреждение: с `--embedding hash` в коллекцию `skill-core` пишутся hash-векторы. Перед
переходом на реальную модель выполните `reindex_embeddings`, иначе смешаются векторы разных
моделей.
