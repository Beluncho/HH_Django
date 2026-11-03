#!/usr/bin/env bash
# Локальный запуск management-команд без Docker.
#
# Подгружает .env.local в окружение процесса (settings.py читает только
# os.environ и .env не разбирает) и передаёт аргументы в manage.py.
#
# Использование:
#   ./run_local.sh migrate
#   ./run_local.sh run_analysis_demo "Python-разработчик" --area 1
#   ./run_local.sh run_experiment top-k --query "Python-разработчик"
#
# Переопределить файл окружения: ENV_FILE=./.env.other ./run_local.sh check

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.local}"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [ -f "$ROOT_DIR/venv/Scripts/activate" ]; then
    . "$ROOT_DIR/venv/Scripts/activate"
elif [ -f "$ROOT_DIR/venv/bin/activate" ]; then
    . "$ROOT_DIR/venv/bin/activate"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "Не найден файл окружения: $ENV_FILE" >&2
    echo "Скопируйте .env.local.example в .env.local и заполните значения." >&2
    exit 1
fi

set -a
. "$ENV_FILE"
set +a

cd "$ROOT_DIR/HH"
exec "$PYTHON_BIN" manage.py "$@"
