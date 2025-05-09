from django.shortcuts import render, get_list_or_404, HttpResponseRedirect
from django.urls import reverse

from .models import Vacancies
from .forms import ContactForm
from django.core.mail import send_mail


# Create your views here.
def main_view(request):
    vacancies = Vacancies.objects.all()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            message = form.cleaned_data['message']

            send_mail(f'{name},{phone_number}',
                      message,
                      email,
                      ['test@test.com'],
                      fail_silently=True)
            return HttpResponseRedirect(reverse('hhapp:index'))
        else:
            return render(request, 'hhapp/index.html',
                  context={'vacancies': vacancies, 'form':form})
    else:
        form = ContactForm()
        return render(request, 'hhapp/index.html',
                      context={'vacancies': vacancies, 'form':form})

def vac_view(request, id):
    vacancy = get_list_or_404(Vacancies, id=id)
    # vacancy = Vacancies.objects.get(id=id)
    return render(request, 'hhapp/vacancy.html',
                  context={'vacancy': vacancy})
