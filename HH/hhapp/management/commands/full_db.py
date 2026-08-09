from django.core.management.base import BaseCommand
from userapp.models import WebSiteUser
from hhapp.models import Vacancies, Employer
from hhapp.services import HHAPIError, search_hh_vacancies


class Command(BaseCommand):
    def handle(self, *args, **options):
        hh_parce('python developer', 'Москва')


def hh_parce(vacancy, area):
    try:
        parser_user = WebSiteUser.objects.get(username='parser_bot')
        print("✅ Пользователь parser_bot найден")
    except WebSiteUser.DoesNotExist:
        print("❌ Ошибка: пользователь 'parser_bot' не найден. Создайте его в админке.")
        return
    except Exception as e:
        print(f"❌ Ошибка при поиске пользователя: {e}")
        return

    try:
        results = search_hh_vacancies(f'{vacancy} {area}')
    except HHAPIError as error:
        print(f"Ошибка API: {error}")
        return []

    count = 0
    for result in results:
        employer = result['employer']
        published = result['published_at']
        vacancy_name = result['name']
        url_vac = result['url']
        salary_from = result['salary_from'] or 0

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
    return results


if __name__ == '__main__':
    hh_parce('python developer', 'Москва')
