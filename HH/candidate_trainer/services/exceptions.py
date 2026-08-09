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


class LLMError(CandidateTrainerError):
    pass


class RAGContextUnavailableError(CandidateTrainerError):
    pass


class InterviewStateError(CandidateTrainerError):
    pass
