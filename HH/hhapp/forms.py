from django.forms import Form, CharField, EmailField, ModelForm, Textarea, TextInput, NumberInput, URLField, \
    IntegerField
from django.core.mail import send_mail
from hhapp.models import Vacancies


class ContactForm(Form):
    name = CharField(
        label='Имя',
        max_length=100
    )
    email = EmailField(
        label='Email',
        help_text='Мы не передаём ваш email третьим лицам'
    )
    phone_number = CharField(
        label='Номер телефона',
        max_length=20,
        help_text='В формате +7 (XXX) XXX-XX-XX'
    )
    message = CharField(
        label='Сообщение',
        widget=Textarea(attrs={'rows': 4})
    )

    def send_email(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        phone_number = self.cleaned_data['phone_number']
        message = self.cleaned_data['message']

        send_mail(f'{name},{phone_number}',
                      message,
                      email,
                      ['test@test.com'],
                      fail_silently=True)


class VacanciesEmployerForm(ModelForm):
    class Meta:
        model = Vacancies
        fields = ('vac_name', 'url_vac', 'salaryFrom')
        labels = {
            'vac_name': 'Название вакансии',
            'url_vac': 'URL вакансии',
            'salaryFrom': 'Зарплата от',
        }
        help_texts = {
            'url_vac': 'Ссылка на страницу вакансии (например, на HH.ru)',
            'salaryFrom': 'Минимальная зарплата в рублях',
        }




