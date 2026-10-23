"""Создание тестовых данных напрямую через Django ORM."""
import os
import sys
import django

# Настройка Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HH.settings')
django.setup()

from django.contrib.auth import get_user_model
from candidate_trainer.models import (
    VacancyAnalysis, Skill, AnalysisSkill,
    InterviewSession, InterviewMessage, InterviewInsight
)

User = get_user_model()

print("=== Создание тестовых данных ===\n")

# Получаем или создаём пользователя admin
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    user.set_password('admin')
    user.save()
    print(f"✓ Создан пользователь: {user.username}")
else:
    # Обновляем пароль на всякий случай
    user.set_password('admin')
    user.save()
    print(f"✓ Пользователь существует: {user.username} (пароль обновлён)")

# Создаём анализ
analysis, created = VacancyAnalysis.objects.get_or_create(
    user=user,
    query='Python Developer',
    region=1,
    defaults={
        'status': 'completed',
        'total_found': 10,
        'processed_count': 10
    }
)
print(f"{'✓ Создан' if created else '✓ Существует'} анализ ID: {analysis.id}")

# Создаём навыки с markdown маркерами для проверки
skill_python, _ = Skill.objects.get_or_create(
    canonical_name='Python',
    defaults={'frequency': 100}
)
skill_django, _ = Skill.objects.get_or_create(
    canonical_name='Django',
    defaults={'frequency': 80}
)
print(f"✓ Навыки созданы: Python, Django")

# Связываем с анализом
AnalysisSkill.objects.get_or_create(
    analysis=analysis,
    skill=skill_python,
    defaults={'frequency': 100, 'rank': 1}
)
AnalysisSkill.objects.get_or_create(
    analysis=analysis,
    skill=skill_django,
    defaults={'frequency': 80, 'rank': 2}
)

# Создаём интервью
session, created = InterviewSession.objects.get_or_create(
    user=user,
    analysis=analysis,
    defaults={
        'status': 'active',
        'total_questions': 5,
        'current_question': 1
    }
)
print(f"{'✓ Создано' if created else '✓ Существует'} интервью ID: {session.id}")

# Создаём сообщения
InterviewMessage.objects.get_or_create(
    session=session,
    role='assistant',
    content='Расскажите о вашем опыте работы с **Python**',
    defaults={'skill': skill_python}
)

InterviewMessage.objects.get_or_create(
    session=session,
    role='user',
    content='Работал с Python более 3 лет, создавал веб-приложения',
    defaults={'skill': skill_python}
)

print(f"✓ Созданы сообщения")

# Создаём инсайт с markdown маркерами (для проверки фильтра)
insight, created = InterviewInsight.objects.get_or_create(
    session=session,
    skill=skill_python,
    defaults={
        'correctness': 4,
        'depth': 3,
        'practical_application': 4,
        'summary': 'Кандидат демонстрирует **хороший уровень** знаний Python.',
        'gaps': [
            '* Недостаточно информации о работе с асинхронным кодом',
            '- Не упомянуты тесты и покрытие',
            '+ Отсутствует опыт оптимизации производительности',
        ],
        'recommendations': [
            '* Изучить asyncio и async/await',
            '- Освоить pytest и unittest',
            '+ Практиковать профилирование кода',
        ]
    }
)
print(f"{'✓ Создан' if created else '✓ Существует'} инсайт")

print(f"\n" + "="*50)
print(f"✅ Готово!")
print(f"")
print(f"Логин: admin")
print(f"Пароль: admin")
print(f"")
print(f"URL интервью: http://localhost:8000/trainer/interviews/{session.id}/")
print(f"URL анализа: http://localhost:8000/trainer/analyses/{analysis.id}/")
print("="*50)
