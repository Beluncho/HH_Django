from django.forms import Form, CharField, EmailField, ModelForm, Textarea, TextInput, NumberInput, URLField, \
    IntegerField
from django.core.mail import send_mail
from hhapp.models import Vacancies


class ContactForm(Form):
<<<<<<< HEAD
    name = CharField( widget=TextInput(attrs={'placeholder': 'Name', 'class': 'form-control'}))
    email = EmailField(widget=TextInput(attrs={'placeholder': 'You email', 'class': 'form-control'}))
    phone_number = CharField(widget=NumberInput(attrs={'placeholder': 'You phone number',
                                                       'class': 'form-control'}))
    message = CharField(widget=Textarea(attrs={'placeholder': 'You message', 'class': 'form-control'}))
=======
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
>>>>>>> AI_Agents_diploma

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
<<<<<<< HEAD
    vac_name = CharField(widget=TextInput(attrs={'placeholder': 'Vacancy', 'class': 'form-control'}))
    url_vac = URLField(widget=TextInput(attrs={'placeholder': 'URL', 'class': 'form-control'}))
    salaryFrom = IntegerField(widget=NumberInput(attrs={'placeholder': 'Salary From', 'class': 'form-control'}) )

    class Meta:
        model = Vacancies
        fields = ('vac_name', 'url_vac', 'salaryFrom')
=======
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
>>>>>>> AI_Agents_diploma




