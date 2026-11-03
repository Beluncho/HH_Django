class CandidateTrainerError(Exception):
    pass


class AnalysisValidationError(CandidateTrainerError):
    pass


class HHAPIError(CandidateTrainerError):
    pass


class EmbeddingError(CandidateTrainerError):
    pass


class ReindexRequiredError(EmbeddingError):
    pass


class KnowledgeImportError(CandidateTrainerError):
    """Файл не удалось подготовить к индексации.

    Причина всегда во входных данных (расширение, размер, кодировка, пустой
    документ), поэтому сообщение можно показывать человеку как есть.
    """

    pass


class LLMError(CandidateTrainerError):
    """Ошибка обращения к LLM.

    http_status и provider_detail заполняются, когда провайдер ответил
    HTTP-ошибкой. Тело ответа содержит причину, которую нельзя восстановить из
    одного кода состояния: «Model not supported», «Unsupported parameter:
    max_tokens» и подобные. Без него сообщение «LLM-сервис вернул HTTP 400»
    не подсказывает, что именно править.
    """

    def __init__(self, message, *, http_status=None, provider_detail=""):
        super().__init__(message)
        self.http_status = http_status
        self.provider_detail = provider_detail


class RAGContextUnavailableError(CandidateTrainerError):
    pass


class InterviewStateError(CandidateTrainerError):
    pass
