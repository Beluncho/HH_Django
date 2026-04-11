from symtable import Class

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_list_or_404, HttpResponseRedirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin

from .models import Vacancies, Employer
from .forms import ContactForm, VacanciesEmployerForm
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
    paginate_by = 5


    def get_queryset(self):
        return Vacancies.objects.all().order_by('-id')


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

# LoginRequiredMixin - first
class VacancyCreateView(LoginRequiredMixin, CreateView, FormPostValidMixin):
    fields = ('vac_name','url_vac', 'employer', 'salaryFrom')
    model = Vacancies
    success_url = reverse_lazy('hhapp:index')
    template_name = 'hhapp/vacancy_create.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class EmployersListView(ListView):
    model = Employer
    template_name = 'hhapp/employers_list.html'
    context_object_name = 'employers'
    paginate_by = 5

    def get_queryset(self):
        return Employer.objects.all().order_by('id')

class EmployerDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView,RemoveDuplicContextMixin):
    model = Employer
    template_name = 'hhapp/employer_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = VacanciesEmployerForm()
        return context

    def test_func(self):
        return self.request.user.is_employer

class VacanciesEmployerCreateView(CreateView):
    model = Vacancies
    template_name = 'hhapp/employer_detail.html'
    form_class = VacanciesEmployerForm

    def post(self, request, *args, **kwargs):
        self.employer_pk = kwargs['pk']
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        form.instance.user = user
        employer = get_object_or_404(Employer, pk=self.employer_pk)
        form.instance.employer = employer
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('hhapp:employer_detail', kwargs={'pk': self.employer_pk})


class EmployerCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView, RemoveDuplicContextMixin, FormPostValidMixin):
    fields = '__all__'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')
    template_name = 'hhapp/employer_create.html'

    def test_func(self):
        return self.request.user.is_employer

class EmployerUpdateView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    fields = '__all__'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')
    template_name = 'hhapp/employer_create.html'

    def test_func(self):
        return self.request.user.is_employer

class EmployerDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    template_name = 'hhapp/employer_delete_confirm.HTML'
    model = Employer
    success_url = reverse_lazy('hhapp:employers_list')

    def test_func(self):
        return self.request.user.is_employer




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



