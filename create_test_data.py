import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HH.settings')
django.setup()

from django.contrib.auth import get_user_model
from candidate_trainer.models import (
    VacancyAnalysis, Skill, AnalysisSkill,
    InterviewSession, InterviewMessage, InterviewInsight
)

User = get_user_model()

print("Создание тестовых данных...")

# Получаем admin пользователя
try:
    user = User.objects.get(username='admin')
    print(f"✓ Используется пользователь: {user.username}")
except User.DoesNotExist:
    user = User.objects.create_user('admin', 'admin@example.com', 'admin')
    print(f"✓ Создан пользователь: admin")

# Создаём анализ
analysis, created = VacancyAnalysis.objects.get_or_create(
    user=user,
    query='Python Developer Test',
    region=1,
    defaults={
        'status': 'completed',
        'total_found': 5,
        'processed_count': 5
    }
)
print(f"✓ Анализ ID: {analysis.id}")

# Создаём навыки
skill1, _ = Skill.objects.get_or_create(
    canonical_name='Python',
    defaults={'frequency': 10}
)
skill2, _ = Skill.objects.get_or_create(
    canonical_name='Django',
    defaults={'frequency': 8}
)
print(f"✓ Навыки созданы")

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
session, created = InterviewSession.objects.get_or_create(
    user=user,
    analysis=analysis,
    defaults={'status': 'active', 'total_questions': 5}
)
print(f"✓ Интервью ID: {session.id}")

# Создаём сообщения
msg1, _ = InterviewMessage.objects.get_or_create(
    session=session,
    role='assistant',
    content='Расскажите о вашем опыте работы с Python',
    defaults={'skill': skill1}
)

msg2, _ = InterviewMessage.objects.get_or_create(
    session=session,
    role='user',
    content='Я работал с Python 3 года, делал веб-приложения на Django',
    defaults={'skill': skill1}
)

# Создаём инсайт с markdown маркерами
insight, created = InterviewInsight.objects.get_or_create(
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
print(f"✓ Инсайт создан")

print(f"\n✅ Готово!")
print(f"URL: http://localhost:8000/trainer/interviews/{session.id}/")
print(f"Логин: admin / admin")
