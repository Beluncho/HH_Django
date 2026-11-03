"""
Management команда для создания тестовых данных интервью с markdown.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from candidate_trainer.models import (
    VacancyAnalysis, Skill, AnalysisSkill,
    InterviewSession, InterviewMessage, InterviewInsight
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт тестовые данные для проверки markdown рендеринга'

    def handle(self, *args, **options):
        # Получаем или создаём пользователя
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь: {user.username}'))
        else:
            self.stdout.write(f'Используется существующий пользователь: {user.username}')

        # Создаём анализ
        analysis, _ = VacancyAnalysis.objects.get_or_create(
            user=user,
            query='Python Developer Test',
            region=1,
            defaults={
                'status': 'completed',
                'total_found': 5,
                'processed_count': 5
            }
        )

        # Создаём навыки
        skill1, _ = Skill.objects.get_or_create(
            canonical_name='Python',
            defaults={'frequency': 10}
        )
        skill2, _ = Skill.objects.get_or_create(
            canonical_name='Django',
            defaults={'frequency': 8}
        )

        # Связываем с анализом
        AnalysisSkill.objects.get_or_create(
            analysis=analysis,
            skill=skill1,
            defaults={'frequency': 10, 'rank': 1}
        )
        AnalysisSkill.objects.get_or_create(
            analysis=analysis,
            skill=skill2,
            defaults={'frequency': 8, 'rank': 2}
        )

        # Создаём интервью
        session, _ = InterviewSession.objects.get_or_create(
            user=user,
            analysis=analysis,
            status='active',
            defaults={'total_questions': 5}
        )

        # Создаём сообщения
        InterviewMessage.objects.get_or_create(
            session=session,
            role='assistant',
            content='Расскажите о вашем опыте работы с Python',
            defaults={'skill': skill1}
        )

        InterviewMessage.objects.get_or_create(
            session=session,
            role='user',
            content='Я работал с Python 3 года, делал веб-приложения на Django',
            defaults={'skill': skill1}
        )

        # Создаём инсайт с markdown маркерами
        InterviewInsight.objects.get_or_create(
            session=session,
            skill=skill1,
            defaults={
                'correctness': 4,
                'depth': 3,
                'practical_application': 4,
                'summary': 'Кандидат демонстрирует **хороший опыт** с Python и Django.',
                'gaps': [
                    '* Недостаточно информации о работе с асинхронным кодом',
                    '- Не упомянуты тесты и покрытие',
                    '+ Отсутствует опыт оптимизации производительности'
                ],
                'recommendations': [
                    '* Изучить asyncio и async/await',
                    '- Освоить pytest и unittest',
                    '+ Практиковать профилирование кода'
                ]
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Тестовые данные созданы:\n'
            f'   - Пользователь: {user.username}\n'
            f'   - Анализ ID: {analysis.id}\n'
            f'   - Интервью ID: {session.id}\n'
            f'   - URL: http://localhost:8000/trainer/interviews/{session.id}/\n'
        ))
