from dataclasses import dataclass

import requests
from django.conf import settings

from .exceptions import HHAPIError


@dataclass(frozen=True)
class HHVacancyData:
    external_id: str
    title: str
    employer: str
    url: str
    published_at: str | None
    description: str
    key_skills: tuple[str, ...]


class HHClient:
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.base_url = settings.HH_API_DOMAIN.rstrip("/")
        self.timeout = settings.HH_REQUEST_TIMEOUT
        self.headers = {"User-Agent": settings.HH_USER_AGENT}
        if settings.HH_ACCESS_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.HH_ACCESS_TOKEN}"

    def _get_json(self, path, params=None):
        if not self.headers["User-Agent"].strip():
            raise HHAPIError("Для HH API не настроен User-Agent")
        if settings.HH_REQUIRE_ACCESS_TOKEN and not settings.HH_ACCESS_TOKEN:
            raise HHAPIError("Для анализа вакансий не настроен HH_ACCESS_TOKEN")

        try:
            response = self.session.get(
                f"{self.base_url}{path}",
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise HHAPIError("HH.ru временно недоступен") from error

        if not isinstance(payload, dict):
            raise HHAPIError("HH.ru вернул неожиданный формат ответа")
        return payload

    def search_vacancy_ids(self, query, area_id, limit=20):
        limit = min(max(int(limit), 1), 20)
        payload = self._get_json(
            "/vacancies",
            params={
                "text": query,
                "area": area_id,
                "page": 0,
                "per_page": limit,
            },
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise HHAPIError("HH.ru вернул неожиданный формат списка вакансий")

        vacancy_ids = []
        seen = set()
        for item in items:
            external_id = str(item.get("id", "")).strip() if isinstance(item, dict) else ""
            if external_id and external_id not in seen:
                seen.add(external_id)
                vacancy_ids.append(external_id)
            if len(vacancy_ids) >= limit:
                break
        return vacancy_ids

    def get_vacancy(self, external_id):
        payload = self._get_json(f"/vacancies/{external_id}")
        employer = payload.get("employer") or {}
        key_skills = payload.get("key_skills") or []

        names = []
        for skill in key_skills:
            if isinstance(skill, dict):
                name = str(skill.get("name", "")).strip()
                if name:
                    names.append(name)

        return HHVacancyData(
            external_id=str(payload.get("id") or external_id),
            title=str(payload.get("name") or "Без названия").strip(),
            employer=str(employer.get("name") or "").strip(),
            url=str(payload.get("alternate_url") or "").strip(),
            published_at=payload.get("published_at"),
            description=str(payload.get("description") or ""),
            key_skills=tuple(names),
        )
