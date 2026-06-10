from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views
from django.contrib import messages
from .forms import LoginForm
from django.utils.decorators import method_decorator 
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import decorator_from_middleware
from django_ratelimit.middleware import RatelimitMiddleware
from .forms import CustomPasswordResetForm

ratelimit_url = lambda **kwargs: decorator_from_middleware(RatelimitMiddleware)(ratelimit(**kwargs))


@method_decorator(ratelimit(key='ip', rate='10/m', block=True, group='auth'), name='dispatch')
class CustomLoginView(auth_views.LoginView):
    template_name = 'auth/login.html'
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        storage = messages.get_messages(request)
        for _ in storage:
            pass 
        return super().get(request, *args, **kwargs)


urlpatterns = [
    # Login / Logout
    #path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url=reverse_lazy('password_change_done')), name='password_change'),

    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'), name='password_change_done'),

    path('password_reset/', ratelimit_url(key='ip', rate='10/m', block=True, group='auth')(
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            email_template_name='auth/password_reset_email.html',
            subject_template_name='auth/password_reset_subject.txt',
            form_class=CustomPasswordResetForm
        )
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', ratelimit_url(key='ip', rate='5/m', block=True, group='auth')(
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html'
        )
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    path('registro/', views.registrar_usuario, name='registro'),

]

