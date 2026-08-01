import os

import requests


class HHAPIError(Exception):
    pass


def search_hh_vacancies(query, per_page=20):
    if not query:
        return []

    domain = os.getenv('HH_API_DOMAIN', 'https://api.hh.ru/').rstrip('/')
    access_token = os.getenv('HH_ACCESS_TOKEN')
    user_agent = os.getenv('HH_USER_AGENT', 'HH_Django/1.0')

    headers = {'User-Agent': user_agent}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    try:
        response = requests.get(
            f'{domain}/vacancies',
            headers=headers,
            params={
                'text': query,
                'page': 0,
                'per_page': per_page,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise HHAPIError('Не удалось получить вакансии с HH.ru') from error

    items = payload.get('items')
    if not isinstance(items, list):
        raise HHAPIError('HH.ru вернул неожиданный формат ответа')

    vacancies = []
    for item in items:
        employer = item.get('employer') or {}
        salary = item.get('salary') or {}
        vacancies.append({
            'name': item.get('name', ''),
            'employer': employer.get('name', ''),
            'url': item.get('alternate_url', ''),
            'published_at': item.get('published_at'),
            'salary_from': salary.get('from'),
            'salary_to': salary.get('to'),
            'currency': salary.get('currency', ''),
        })

    return vacancies
