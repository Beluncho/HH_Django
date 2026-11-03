import re
import unicodedata
from dataclasses import dataclass


ALIASES = {
    "ci cd": ("ci/cd", "CI/CD"),
    "django rest framework": ("django rest framework", "Django REST Framework"),
    "drf": ("django rest framework", "Django REST Framework"),
    "git": ("git", "Git"),
    "javascript": ("javascript", "JavaScript"),
    "js": ("javascript", "JavaScript"),
    "k8s": ("kubernetes", "Kubernetes"),
    "kubernetes": ("kubernetes", "Kubernetes"),
    "postgres": ("postgresql", "PostgreSQL"),
    "postgresql": ("postgresql", "PostgreSQL"),
    "python 3": ("python", "Python"),
    "python3": ("python", "Python"),
    "rest api": ("rest api", "REST API"),
    "sql": ("sql", "SQL"),
}

CANONICAL_CASE = {
    "api": "API",
    "aws": "AWS",
    "c#": "C#",
    "c++": "C++",
    "css": "CSS",
    "html": "HTML",
    "http": "HTTP",
    "linux": "Linux",
    "ml": "ML",
    "nosql": "NoSQL",
    "oop": "ООП",
    "ооп": "ООП",
    "php": "PHP",
    "qa": "QA",
    "sql": "SQL",
    "typescript": "TypeScript",
}


@dataclass(frozen=True)
class NormalizedSkill:
    key: str
    canonical_name: str
    variant: str


def _clean(value):
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _key(value):
    value = value.casefold()
    value = re.sub(r"[\s_-]*[/\\][\s_-]*", " ", value)
    value = re.sub(r"[^\w#+.]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip(" .")


def normalize_skill(value):
    variant = _clean(value)
    key = _key(variant)
    if not key:
        return None

    if key in ALIASES:
        normalized_key, canonical_name = ALIASES[key]
    else:
        normalized_key = key
        canonical_name = CANONICAL_CASE.get(key)
        if canonical_name is None:
            canonical_name = " ".join(
                CANONICAL_CASE.get(part, part.capitalize())
                for part in key.split()
            )

    return NormalizedSkill(
        key=normalized_key,
        canonical_name=canonical_name,
        variant=variant,
    )


def normalize_vacancy_skills(values):
    normalized = {}
    for value in values or ():
        skill = normalize_skill(value)
        if skill is not None:
            normalized.setdefault(skill.key, skill)
    return tuple(normalized.values())
