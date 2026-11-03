# Generated manually for Этап 2: Глобальная база объяснений навыков

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_explanations_to_global(apps, schema_editor):
    """
    Миграция данных:
    1. Добавить поле skill через analysis_skill
    2. Дедуплицировать по skill.canonical_name
    3. Оставить самое свежее объяснение для каждого навыка
    4. Сделать его глобальным (user=NULL, is_active=True)
    """
    SkillExplanation = apps.get_model('candidate_trainer', 'SkillExplanation')

    # Собираем данные о существующих объяснениях
    explanations = list(
        SkillExplanation.objects.select_related('analysis_skill__skill')
        .order_by('analysis_skill__skill__canonical_name', '-created_at')
    )

    # Группируем по навыку и берём самое свежее
    skill_map = {}
    for exp in explanations:
        if exp.analysis_skill and exp.analysis_skill.skill:
            skill = exp.analysis_skill.skill
            canonical_name = skill.canonical_name

            if canonical_name not in skill_map:
                skill_map[canonical_name] = {
                    'skill_id': skill.id,
                    'explanation_id': exp.id,
                    'created_at': exp.created_at,
                }

    # Обновляем поле skill для всех объяснений
    for exp in explanations:
        if exp.analysis_skill and exp.analysis_skill.skill:
            exp.skill_id = exp.analysis_skill.skill.id
            exp.save(update_fields=['skill_id'])

    # Помечаем самые свежие как глобальные и активные
    for data in skill_map.values():
        SkillExplanation.objects.filter(id=data['explanation_id']).update(
            user_id=None,
            is_active=True,
        )

    # Остальные делаем неактивными
    global_ids = [data['explanation_id'] for data in skill_map.values()]
    SkillExplanation.objects.exclude(id__in=global_ids).update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidate_trainer', '0002_llmrequestlog'),
    ]

    operations = [
        # Шаг 1: Добавить новое поле skill (nullable)
        migrations.AddField(
            model_name='skillexplanation',
            name='skill',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='explanations',
                to='candidate_trainer.skill',
            ),
        ),

        # Шаг 2: Добавить поле is_active
        migrations.AddField(
            model_name='skillexplanation',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Только одна активная версия на skill+user пару'),
        ),

        # Шаг 3: Сделать user nullable ПЕРЕД миграцией данных
        migrations.AlterField(
            model_name='skillexplanation',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='skill_explanations',
                to=settings.AUTH_USER_MODEL,
                help_text='NULL = глобальное объяснение для всех пользователей',
            ),
        ),

        # Шаг 4: Миграция данных
        migrations.RunPython(
            migrate_explanations_to_global,
            reverse_code=migrations.RunPython.noop,
        ),

        # Шаг 5: Сделать skill обязательным
        migrations.AlterField(
            model_name='skillexplanation',
            name='skill',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='explanations',
                to='candidate_trainer.skill',
            ),
        ),

        # Шаг 6: Удалить старое поле analysis_skill
        migrations.RemoveField(
            model_name='skillexplanation',
            name='analysis_skill',
        ),

        # Шаг 7: Добавить индексы
        migrations.AddIndex(
            model_name='skillexplanation',
            index=models.Index(fields=['skill', 'user', 'is_active'], name='candidate_t_skill_i_idx'),
        ),

        # Шаг 8: Добавить уникальное ограничение
        migrations.AddConstraint(
            model_name='skillexplanation',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=('skill', 'user'),
                name='unique_active_explanation_per_skill_user',
            ),
        ),
    ]
