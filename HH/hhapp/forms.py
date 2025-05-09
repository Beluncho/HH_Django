from django.forms import Form, CharField, EmailField


class ContactForm(Form):
    name = CharField(label= 'Full name')
    email = EmailField(label= 'Email address')
    phone_number = CharField(label='Phone number')
    message = CharField(label='Message')