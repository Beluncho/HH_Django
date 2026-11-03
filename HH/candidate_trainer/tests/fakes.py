import json

from candidate_trainer.services.exceptions import HHAPIError, LLMError
from candidate_trainer.services.llm import LLMResponse


class FakeHHClient:
    def __init__(self, cards, vacancy_ids=None, failing_ids=None):
        self.cards = {card.external_id: card for card in cards}
        self.vacancy_ids = vacancy_ids or list(self.cards)
        self.failing_ids = set(failing_ids or ())
        self.search_calls = []
        self.detail_calls = []

    def search_vacancy_ids(self, query, area_id, limit=20):
        self.search_calls.append((query, area_id, limit))
        return self.vacancy_ids[:limit]

    def get_vacancy(self, external_id):
        self.detail_calls.append(external_id)
        if external_id in self.failing_ids:
            raise HHAPIError("Ошибка карточки")
        return self.cards[external_id]


class QueueLLMClient:
    provider = "test"
    model = "test-llm"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, system_prompt, messages, max_tokens=None):
        self.calls.append((system_prompt, messages, max_tokens))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if isinstance(response, dict):
            response = json.dumps(response, ensure_ascii=False)
        return LLMResponse(
            text=response,
            provider=self.provider,
            model=self.model,
        )


class FailingLLMClient(QueueLLMClient):
    def __init__(self, message="LLM недоступен"):
        super().__init__([LLMError(message)])


class FailingRetriever:
    def retrieve(self, *args, **kwargs):
        raise AssertionError("Retriever не должен вызываться")
