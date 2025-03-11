# Generated by Django 5.1.2 on 2025-03-02 18:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Employer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employer_name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vacancies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('vac_name', models.CharField(max_length=50)),
                ('url_vac', models.URLField()),
                ('salaryFrom', models.IntegerField(default=0)),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hhapp.employer')),
            ],
        ),
    ]
