import math
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.management.demo_utils import (
    build_embedding_service,
    ensure_database_ready,
    parse_int_list,
    resolve_area,
    resolve_user,
)
from candidate_trainer.models import KnowledgeCollection, VacancyAnalysis
from candidate_trainer.services.analysis import (
    create_or_get_analysis,
    run_analysis,
)
from candidate_trainer.services.exceptions import CandidateTrainerError
from candidate_trainer.services.knowledge import (
    KnowledgeRetriever,
    get_global_collection,
    split_content,
)
from candidate_trainer.services.llm import get_llm_client
from candidate_trainer.services.prompts import (
    EVALUATION_VARIANTS,
    EXPLANATION_VARIANTS,
    evaluation_prompt,
    explanation_prompt,
    initial_question_prompt,
)

EXPERIMENTS = (
    "frequency",
    "top-k",
    "chunk-size",
    "embedding",
    "prompt-explanation",
    "prompt-evaluation",
)

PROBE_TEXTS = (
    "Опыт разработки на Python и Django, понимание ORM",
    "Настройка CI/CD, Docker и Kubernetes",
    "Работа с PostgreSQL, оптимизация SQL-запросов",
    "Вёрстка интерфейсов на JavaScript и React",
)


def _cosine(left, right):
    if not left or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


class Command(BaseCommand):
    help = (
        "Прогон эксперимента для файла этапа 4: сравнение вариантов промтов "
        "и параметров поиска. Печатает готовый блок «параметры -> результат» "
        "и, при указании --out, сохраняет его в файл."
    )

    def add_arguments(self, parser):
        parser.add_argument("experiment", choices=EXPERIMENTS)
        parser.add_argument("--query", default="Python-разработчик")
        parser.add_argument("--area", default="1")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument(
            "--embedding",
            choices=("hash", "sentence_transformers"),
            default=None,
        )
        parser.add_argument("--top-k", default="5", help="Список через запятую: 3,4,6")
        parser.add_argument(
            "--chunk-size",
            default="600,900,1200",
            help="Список размеров фрагмента через запятую",
        )
        parser.add_argument("--chunk-overlap", type=int, default=120)
        parser.add_argument(
            "--prompt-variant",
            default="1",
            help="Список номеров вариантов: 1,2",
        )
        parser.add_argument("--answer", default="", help="Ответ кандидата для оценки")
        parser.add_argument("--question", default="", help="Вопрос; если пуст — сгенерируется")
        parser.add_argument("--out", default=None, help="Файл для сохранения блока")
        parser.add_argument("--user", default=None)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        self.options = options
        self.lines = []

        handler = getattr(
            self,
            "_experiment_{0}".format(options["experiment"].replace("-", "_")),
        )
        try:
            handler()
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        block = "\n".join(self.lines)
        self.stdout.write(block)

        out = options["out"]
        if out:
            path = Path(out)
            if path.is_dir():
                path = path / f"experiment_{options['experiment']}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(block + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Блок сохранён: {path}"))

    # --- общие помощники -------------------------------------------------

    def emit(self, text=""):
        self.lines.append(text)

    def header(self, goal):
        self.emit(f"=== ЭКСПЕРИМЕНТ: {self.options['experiment']} ===")
        self.emit(f"Цель: {goal}")
        self.emit(f"Запрос: {self.options['query']}, регион: {self._area_name}")
        self.emit(f"Вакансий обработано: {self._analysis.vacancies_processed}")
        self.emit("")

    def ensure_analysis(self):
        ensure_database_ready()
        area_id, area_name = resolve_area(self.options["area"])
        self._area_id = area_id
        self._area_name = area_name
        user, _ = resolve_user(self.options["user"])
        self._user = user

        if self.options["limit"] is not None:
            if self.options["limit"] < 1:
                raise CommandError("--limit должен быть не меньше 1")
            settings.HH_ANALYSIS_LIMIT = self.options["limit"]

        self._embedding_service = build_embedding_service(self.options["embedding"])

        analysis, _ = create_or_get_analysis(
            user=user,
            query=self.options["query"],
            area_id=area_id,
            area_name=area_name,
        )
        self._analysis = run_analysis(
            analysis.pk,
            embedding_service=self._embedding_service,
            force=self.options["force"],
        )
        return self._analysis

    def skill_core_collection(self):
        collection = get_global_collection(KnowledgeCollection.Kind.SKILL_CORE)
        if collection is None:
            raise CommandError(
                "Нет включённой коллекции skill-core. Выполните анализ вакансий "
                "или импортируйте документ командой import_knowledge."
            )
        return collection

    def top_skill(self):
        top = (
            self._analysis.analysis_skills.select_related("skill")
            .order_by("rank")
            .first()
        )
        if top is None:
            raise CommandError("В анализе нет навыков")
        return top

    def retrieve_contexts(self, limit):
        collection = self.skill_core_collection()
        top = self.top_skill()
        retriever = KnowledgeRetriever(embedding_service=self._embedding_service)
        return top, retriever.retrieve(
            collection,
            top.skill.canonical_name,
            skill=top.skill,
            limit=limit,
        )

    def variant_names(self, option_key, registry):
        names = []
        for number in parse_int_list(self.options[option_key], minimum=1):
            name = f"v{number}"
            if name not in registry:
                raise CommandError(
                    f"Нет варианта {name}. Доступные: {', '.join(registry)}"
                )
            names.append(name)
        return names

    # --- эксперименты ----------------------------------------------------

    def _experiment_frequency(self):
        analysis = self.ensure_analysis()
        self.header(
            "сравнить подсчёт частоты по числу вакансий и по числу упоминаний в текстах"
        )
        snapshots = [
            snapshot
            for snapshot in analysis.vacancies.all()
            if snapshot.description
        ]

        rows = []
        for item in analysis.analysis_skills.select_related("skill"):
            name = item.skill.canonical_name.casefold()
            mentions = sum(
                snapshot.description.casefold().count(name) for snapshot in snapshots
            )
            rows.append((item.rank, item.skill.canonical_name, item.vacancy_count, mentions))

        self.emit(f"{'РАНГ':<6}{'НАВЫК':<30}{'ВАКАНСИЙ':>9}{'УПОМИНАНИЙ':>12}")
        for rank, skill_name, count, mentions in rows:
            self.emit(f"{rank:<6}{skill_name:<30}{count:>9}{mentions:>12}")

        reordered = sum(
            1
            for position, row in enumerate(
                sorted(rows, key=lambda item: (-item[3], item[1])),
                start=1,
            )
            if row[0] != position
        )
        self.emit("")
        self.emit(
            "Наблюдение: при подсчёте по упоминаниям меняют позицию "
            f"{reordered} из {len(rows)} навыков."
        )
        self.emit(
            "Вывод: подсчёт по вакансиям устойчив к повторам слова внутри одного "
            "описания и используется в приложении по умолчанию."
        )

    def _experiment_top_k(self):
        values = parse_int_list(self.options["top_k"], minimum=1, maximum=20)
        self.ensure_analysis()
        self.header("выбрать количество фрагментов RAG, попадающих в контекст")

        for value in values:
            top, contexts = self.retrieve_contexts(limit=value)
            self.emit(f"--- top-k={value} ---")
            self.emit(f"Навык: {top.skill.canonical_name}")
            self.emit(f"Фрагментов получено: {len(contexts)}")
            for context in contexts:
                self.emit(f"    score={context.score:.4f}  {context.document_title}")
            self.emit("")

        self.emit(
            "Вывод (заполнить): какой top-k даёт достаточно контекста без лишнего шума."
        )

    def _experiment_chunk_size(self):
        sizes = parse_int_list(self.options["chunk_size"], minimum=100)
        overlap = self.options["chunk_overlap"]
        analysis = self.ensure_analysis()
        self.header("оценить разбиение описаний вакансий на фрагменты разного размера")

        snapshots = [
            snapshot
            for snapshot in analysis.vacancies.all()
            if snapshot.description.strip()
        ]
        if not snapshots:
            raise CommandError("Нет описаний вакансий для разбиения")

        self.emit(f"Описаний в выборке: {len(snapshots)}, overlap={overlap}")
        self.emit("")
        for size in sizes:
            counts = [
                len(split_content(snapshot.description, max_chars=size, overlap=overlap))
                for snapshot in snapshots
            ]
            total = sum(counts)
            average = total / len(counts)
            self.emit(
                f"max_chars={size}: всего фрагментов {total}, "
                f"в среднем {average:.1f} на вакансию"
            )

        self.emit("")
        self.emit(
            "Вывод (заполнить): размер фрагмента определяет, сколько контекста "
            "получит LLM на один запрос."
        )

    def _experiment_embedding(self):
        query = self.options["query"]
        self.emit("=== ЭКСПЕРИМЕНТ: embedding ===")
        self.emit("Цель: сравнить ранжирование тестовых фраз двумя провайдерами")
        self.emit(f"Запрос: {query}")
        self.emit(
            "Примечание: это микробенчмарк на фиксированном наборе фраз, "
            "он не заменяет переиндексацию коллекции."
        )
        self.emit("")

        for provider in ("hash", "sentence_transformers"):
            try:
                service = build_embedding_service(provider)
                query_vector = service.embed(query)
                scored = [
                    (_cosine(query_vector, service.embed(text)), text)
                    for text in PROBE_TEXTS
                ]
            except CandidateTrainerError as error:
                self.emit(f"--- {provider}: недоступен ({error}) ---")
                self.emit("")
                continue

            scored.sort(key=lambda item: item[0], reverse=True)
            self.emit(f"--- {provider} (модель {service.model_name}) ---")
            for score, text in scored:
                self.emit(f"    {score:+.4f}  {text}")
            self.emit("")

        self.emit(
            "Вывод (заполнить): какая модель даёт более осмысленное ранжирование."
        )

    def _experiment_prompt_explanation(self):
        variants = self.variant_names("prompt_variant", EXPLANATION_VARIANTS)
        self.ensure_analysis()
        self.header("сравнить варианты промта объяснения навыка")
        top, contexts = self.retrieve_contexts(limit=5)
        if not contexts:
            raise CommandError(
                "Для навыка нет содержательных фрагментов базы знаний — "
                "объяснение невозможно"
            )

        llm_client = get_llm_client()
        self.emit(f"Навык: {top.skill.canonical_name}")
        self.emit(f"Фрагментов контекста: {len(contexts)}")
        self.emit("")

        for variant in variants:
            system_prompt, messages = explanation_prompt(top, contexts, variant=variant)
            response = llm_client.complete(system_prompt, messages)
            self.emit(f"--- вариант {variant} ---")
            self.emit(response.text)
            self.emit("")

        self.emit("Вывод (заполнить): какой вариант понятнее и полнее.")

    def _experiment_prompt_evaluation(self):
        answer = (self.options["answer"] or "").strip()
        if not answer:
            raise CommandError(
                "Для prompt-evaluation нужен ответ кандидата: --answer \"...\""
            )
        variants = self.variant_names("prompt_variant", EVALUATION_VARIANTS)

        self.ensure_analysis()
        self.header("сравнить варианты промта оценки ответа")

        top, contexts = self.retrieve_contexts(limit=5)
        llm_client = get_llm_client()

        question = (self.options["question"] or "").strip()
        if not question:
            system_prompt, messages = initial_question_prompt(
                self._analysis,
                [top.skill],
                contexts,
            )
            question = llm_client.complete(system_prompt, messages).text
            self.emit(f"Сгенерирован вопрос: {question}")

        self.emit(f"Навык: {top.skill.canonical_name}")
        self.emit(f"Ответ кандидата: {answer}")
        self.emit("")

        for variant in variants:
            system_prompt, messages = evaluation_prompt(
                question,
                answer,
                top.skill,
                contexts,
                variant=variant,
            )
            response = llm_client.complete(system_prompt, messages)
            self.emit(f"--- вариант {variant} ---")
            self.emit(response.text)
            self.emit("")

        self.emit("Вывод (заполнить): какая рубрика точнее и полезнее кандидату.")
