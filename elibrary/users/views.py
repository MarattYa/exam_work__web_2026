from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import render, redirect

from .forms import RegisterForm
from .models import Profile, Role


class LoginUserView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if remember_me:
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'Невозможно аутентифицироваться с указанными логином и паролем'
        )
        return super().form_invalid(form)


def register(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password1'],
                        last_name=form.cleaned_data['last_name'],
                        first_name=form.cleaned_data['first_name'],
                    )

                    role, _ = Role.objects.get_or_create(
                        name='Пользователь',
                        defaults={
                            'description': 'Может оставлять рецензии и создавать подборки книг'
                        }
                    )

                    Profile.objects.update_or_create(
                        user=user,
                        defaults={
                            'role': role,
                            'middle_name': form.cleaned_data.get('middle_name', '')
                        }
                    )

                login(request, user)
                messages.success(request, 'Регистрация выполнена успешно')
                return redirect('/')

            except Exception:
                messages.error(request, 'При регистрации возникла ошибка')

    else:
        form = RegisterForm()

    return render(request, 'register.html', {
        'form': form,
    })