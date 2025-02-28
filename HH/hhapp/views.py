from symtable import Class


from django.shortcuts import render, get_list_or_404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin

from .models import Vacancies, Employer
from .forms import ContactForm
from django.core.mail import send_mail



class ContactView(FormView):
    """
    создаем форму для заполнения и отправки в терминал
    """
    template_name = 'hhapp/index.html'
    form_class = ContactForm
    success_url = reverse_lazy('hhapp:index')

    def form_valid(self, form):
        """
        :param form: запоняемая форма
        :send_email: функция отправки сообщения в терминал (ContactForm)
        :return: проверка валидности
        """
        form.send_email()
        return super().form_valid(form)


class VacanciesListView(ListView, ContactView):
    model = Vacancies
    template_name = 'hhapp/index.html'
    context_object_name = 'vacancies'
    def get_queryset(self):
        return Vacancies.objects.all


class RemoveDuplicContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class VacDetailView(DetailView,RemoveDuplicContextMixin):
    model = Vacancies
    template_name = 'hhapp/vacancy.html'


class FormPostValidMixin(FormMixin):

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        return super().form_valid(form)


class VacancyCreateView(CreateView,FormPostValidMixin):
    fields = '__all__'
    model = Vacancies
    success_url = reverse_lazy('hhapp:index')
    template_name = 'hhapp/vacancy_create.html'



class EmployersListView(ListView):
    model = Employer
    template_name = 'hhapp/employers_list.html'
    context_object_name = 'employers'

    def get_queryset(self):
        return Employer.objects.all()

class EmployerDetailView(DetailView,RemoveDuplicContextMixin):
    model = Employer
    template_name = 'hhapp/employer_detail.html'

class EmployerCreateView(CreateView, RemoveDuplicContextMixin, FormPostValidMixin):
    fields = '__all__'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')
    template_name = 'hhapp/employer_create.html'

class EmployerUpdateView(UpdateView):
    fields = '__all__'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')
    template_name = 'hhapp/employer_create.html'

class EmployerDeleteView(DeleteView):
    template_name = 'hhapp/employer_delete_confirm.HTML'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')

# def main_view(request):
#     vacancies = Vacancies.objects.all()
#     if request.method == 'POST':
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             name = form.cleaned_data['name']
#             email = form.cleaned_data['email']
#             phone_number = form.cleaned_data['phone_number']
#             message = form.cleaned_data['message']
#
#             send_mail(f'{name},{phone_number}',
#                       message,
#                       email,
#                       ['test@test.com'],
#                       fail_silently=True)
#             return HttpResponseRedirect(reverse('hhapp:index'))
#         else:
#             return render(request, 'hhapp/index.html',
#                   context={'vacancies': vacancies, 'form':form})
#     else:
#         form = ContactForm()
#         return render(request, 'hhapp/index.html',
#                       context={'vacancies': vacancies, 'form':form})
#
# def vac_view(request, id):
#     vacancy = get_list_or_404(Vacancies, id=id)
#     # vacancy = Vacancies.objects.get(id=id)
#     return render(request, 'hhapp/vacancy.html',
#                   context={'vacancy': vacancy})



