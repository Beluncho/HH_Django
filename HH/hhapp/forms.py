from django.forms import Form, CharField, EmailField, ModelForm, Textarea, TextInput, NumberInput, URLField, \
    IntegerField
from django.core.mail import send_mail
from hhapp.models import Vacancies


class ContactForm(Form):
    name = CharField( widget=TextInput(attrs={'placeholder': 'Name', 'class': 'form-control'}))
    email = EmailField(widget=TextInput(attrs={'placeholder': 'You email', 'class': 'form-control'}))
    phone_number = CharField(widget=NumberInput(attrs={'placeholder': 'You phone number',
                                                       'class': 'form-control'}))
    message = CharField(widget=Textarea(attrs={'placeholder': 'You message', 'class': 'form-control'}))

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
    vac_name = CharField(widget=TextInput(attrs={'placeholder': 'Vacancy', 'class': 'form-control'}))
    url_vac = URLField(widget=TextInput(attrs={'placeholder': 'URL', 'class': 'form-control'}))
    salaryFrom = IntegerField(widget=NumberInput(attrs={'placeholder': 'Salary From', 'class': 'form-control'}) )

    class Meta:
        model = Vacancies
        fields = ('vac_name', 'url_vac', 'salaryFrom')




