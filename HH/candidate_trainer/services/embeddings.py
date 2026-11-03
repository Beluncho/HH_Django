import hashlib
import math
import re
import threading
from functools import lru_cache

from django.conf import settings

from .exceptions import EmbeddingError


class BaseEmbeddingService:
    @property
    def model_name(self):
        raise NotImplementedError

    @property
    def dimension(self):
        raise NotImplementedError

    def embed_many(self, texts):
        raise NotImplementedError

    def embed(self, text):
        vectors = self.embed_many([text])
        return vectors[0]


class HashEmbeddingService(BaseEmbeddingService):
    def __init__(self, dimension=None, model_name="test-hash-v1"):
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        self._model_name = model_name

    @property
    def model_name(self):
        return self._model_name

    @property
    def dimension(self):
        return self._dimension

    def embed_many(self, texts):
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text):
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[\w#+.]+", str(text).casefold(), re.UNICODE)
        for token in tokens or [""]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            vector[index] += -1.0 if digest[4] & 1 else 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingService(BaseEmbeddingService):
    _load_lock = threading.Lock()

    def __init__(self, model_name=None, dimension=None, device=None, cache_dir=None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._dimension = dimension or settings.EMBEDDING_DIMENSION
        self.device = device or settings.EMBEDDING_DEVICE
        self.cache_dir = cache_dir or settings.EMBEDDING_CACHE_DIR
        self._model = None

    @property
    def model_name(self):
        return self._model_name

    @property
    def dimension(self):
        return self._dimension

    def _get_model(self):
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer

                        self._model = SentenceTransformer(
                            self.model_name,
                            device=self.device,
                            cache_folder=self.cache_dir,
                        )
                    except (ImportError, OSError, RuntimeError) as error:
                        raise EmbeddingError(
                            "Не удалось загрузить локальную embedding-модель"
                        ) from error
        return self._model

    def embed_many(self, texts):
        if not texts:
            return []
        try:
            vectors = self._get_model().encode(
                list(texts),
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except (OSError, RuntimeError, ValueError) as error:
            raise EmbeddingError("Не удалось построить embeddings") from error

        result = [vector.tolist() for vector in vectors]
        if any(len(vector) != self.dimension for vector in result):
            raise EmbeddingError(
                "Размерность embedding-модели не совпадает с настройкой "
                "EMBEDDING_DIMENSION"
            )
        return result


@lru_cache(maxsize=4)
def _cached_embedding_service(provider, model, dimension, device, cache_dir):
    if provider == "hash":
        return HashEmbeddingService(dimension=dimension, model_name=model)
    if provider == "sentence_transformers":
        return SentenceTransformerEmbeddingService(
            model_name=model,
            dimension=dimension,
            device=device,
            cache_dir=cache_dir,
        )
    raise EmbeddingError(f"Неизвестный embedding provider: {provider}")


def get_embedding_service():
    return _cached_embedding_service(
        settings.EMBEDDING_PROVIDER,
        settings.EMBEDDING_MODEL,
        settings.EMBEDDING_DIMENSION,
        settings.EMBEDDING_DEVICE,
        settings.EMBEDDING_CACHE_DIR,
    )
