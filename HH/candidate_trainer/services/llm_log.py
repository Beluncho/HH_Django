"""Журнал обращений к LLM.

Каждый вызов модели — и удачный, и неудачный — оставляет строку в
``LLMRequestLog``. Тексты промтов и ответов модели в журнал не попадают:
правила проекта запрещают логировать пользовательские ответы и сформированные
промты, а для диагностики достаточно кода состояния и тела ответа провайдера.

Модуль живёт отдельно от ``services/llm.py``, чтобы инфраструктурный клиент не
импортировал модели Django.
"""

import time
from contextlib import contextmanager

from ..models import LLMRequestLog


class LLMCallRecorder:
    """Состояние одного вызова модели.

    Заполняется по ходу вызова и записывается в журнал один раз — при выходе из
    ``record_llm_call``.
    """

    def __init__(self, operation, user=None, provider="", model=""):
        self.operation = operation
        self.user = user
        self.provider = provider
        self.model = model
        self.prompt_tokens = None
        self.completion_tokens = None

    def remember(self, response):
        """Запоминает провайдера, модель и расход токенов из ответа.

        Возвращает ответ, чтобы вызов читался одной строкой:
        ``response = call.remember(client.complete(...))``.
        """
        self.provider = response.provider
        self.model = response.model
        self.prompt_tokens = response.prompt_tokens
        self.completion_tokens = response.completion_tokens
        return response


@contextmanager
def record_llm_call(operation, user=None, provider="", model=""):
    """Пишет в журнал один вызов модели, не подавляя исключение.

    Провайдер и модель известны до запроса, поэтому передаются на входе: у
    неудачного вызова ответа нет, и восстановить их будет неоткуда.
    """
    call = LLMCallRecorder(operation, user=user, provider=provider, model=model)
    started_at = time.monotonic()
    try:
        yield call
    except Exception as error:
        _write(call, started_at, error)
        raise
    else:
        _write(call, started_at, None)


def _write(call, started_at, error):
    try:
        LLMRequestLog.objects.create(
            user=_journal_user(call.user),
            operation=call.operation,
            status=(
                LLMRequestLog.Status.ERROR if error else LLMRequestLog.Status.OK
            ),
            provider=(call.provider or "")[:50],
            model=(call.model or "")[:200],
            duration_ms=int((time.monotonic() - started_at) * 1000),
            http_status=getattr(error, "http_status", None),
            error_detail=_error_detail(error),
            prompt_tokens=call.prompt_tokens,
            completion_tokens=call.completion_tokens,
        )
    except Exception:
        # Журнал не должен ломать основную операцию: если запись не удалась
        # (например, миграции ещё не применены), пользователь всё равно должен
        # получить и результат, и исходную ошибку.
        pass


def _error_detail(error):
    if error is None:
        return ""
    text = str(error)
    provider_detail = getattr(error, "provider_detail", "") or ""
    if provider_detail:
        text = f"{text}. Ответ провайдера: {provider_detail}"
    return text[:500]


def _journal_user(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    return user
