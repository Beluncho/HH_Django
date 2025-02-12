from requests import get
from pprint import pprint
from django.core.management.base import BaseCommand
from hhapp.models import Vacancies, Employer


class Command(BaseCommand):
    def handle(self, *args, **options):
        hh_parce('python developer', 'Москва')



def hh_parce(vacancy, area):
    DOMAIN = 'https://api.hh.ru/'
    url = f'{DOMAIN}vacancies'
    params = {'text': f"'{vacancy}' AND '{area}'", 'page': '1', 'per_page': '20'}

    results = get(url, params=params).json()
    # pprint(results)

    for result in results['items']:

        employer = result['employer']['name']
        published = result['published_at']
        vacancy_name = result['name']
        url_vac = result['alternate_url']

        em = Employer.objects.get_or_create(employer_name=employer)[0]
        Vacancies.objects.create(vac_name=vacancy_name,
                                 employer = em,
                                 published=published,
                                 url_vac=url_vac)
    return results['items']
if __name__ == '__main__':
    hh_parce('python developer', 'Москва')
