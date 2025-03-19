# Generated by Django 5.1.6 on 2025-03-13 06:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hhapp', '0005_alter_vacancies_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vacancies',
            name='employer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employer_vacancies', to='hhapp.employer'),
        ),
    ]
