from django.test import SimpleTestCase

from candidate_trainer.services.normalization import (
    normalize_skill,
    normalize_vacancy_skills,
)


class SkillNormalizationTest(SimpleTestCase):
    def test_aliases_resolve_to_one_canonical_skill(self):
        postgres = normalize_skill(" Postgres ")
        postgresql = normalize_skill("PostgreSQL")

        self.assertEqual(postgres.key, "postgresql")
        self.assertEqual(postgres.key, postgresql.key)
        self.assertEqual(postgres.canonical_name, "PostgreSQL")

    def test_symbols_are_preserved(self):
        self.assertEqual(normalize_skill("C++").canonical_name, "C++")
        self.assertEqual(normalize_skill("C#").canonical_name, "C#")

    def test_duplicate_variants_inside_vacancy_are_removed(self):
        skills = normalize_vacancy_skills(["Python", "python3", "SQL", "sql"])

        self.assertEqual([skill.key for skill in skills], ["python", "sql"])
