import os
from requests import get
from django.core.management.base import BaseCommand
from userapp.models import WebSiteUser
from hhapp.models import Vacancies, Employer
from dotenv import load_dotenv
load_dotenv('.env.dev')


class Command(BaseCommand):
    def handle(self, *args, **options):
        hh_parce('python developer', 'Москва')


def hh_parce(vacancy, area):
    # Загружаем переменные из окружения
    DOMAIN = os.getenv('HH_API_DOMAIN')
    ACCESS_TOKEN = os.getenv('HH_ACCESS_TOKEN')
    USER_AGENT = os.getenv('HH_USER_AGENT')

    try:
        parser_user = WebSiteUser.objects.get(username='parser_bot')
        print("✅ Пользователь parser_bot найден")
    except WebSiteUser.DoesNotExist:
        print("❌ Ошибка: пользователь 'parser_bot' не найден. Создайте его в админке.")
        return
    except Exception as e:
        print(f"❌ Ошибка при поиске пользователя: {e}")
        return

    url = f'{DOMAIN}vacancies'

    headers = {
        'User-Agent': USER_AGENT,
    }

    # Добавляем авторизацию, если есть токен
    if ACCESS_TOKEN:
        headers['Authorization'] = f'Bearer {ACCESS_TOKEN}'
    else:
        print("Внимание: HH_ACCESS_TOKEN не задан. Возможны ошибки 403.")

    params = {
        'text': f'{vacancy} {area}',
        'page': 0,
        'per_page': 20
    }

    response = get(url, headers=headers, params=params)
    results = response.json()

    print(f"Status code: {response.status_code}")

    if 'items' not in results:
        print(f"Ошибка API: {results}")
        return []

    count = 0
    for result in results['items']:
        employer = result['employer']['name']
        published = result['published_at']
        vacancy_name = result['name']
        url_vac = result['alternate_url']
        salary = result['salary']


        if salary and salary.get('from'):
            salary_from = int(salary['from'])
        else:
            salary_from = 0

        em, _ = Employer.objects.get_or_create(employer_name=employer)
        Vacancies.objects.create(
            vac_name=vacancy_name,
            employer=em,
            published=published,
            url_vac=url_vac,
            salaryFrom=salary_from,
            user=parser_user,
        )
        count += 1
        print(f"✓ Добавлена: {vacancy_name[:50]}...")

    print(f"\n✅ Готово! Добавлено {count} вакансий")
    return results['items']


if __name__ == '__main__':
    hh_parce('python developer', 'Москва')
