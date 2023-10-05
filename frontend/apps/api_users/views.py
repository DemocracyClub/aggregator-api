# Create your views here.
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView
from sesame.utils import get_query_string, get_user

from api_users.forms import APIKeyForm, LoginForm, UserProfileForm
from api_users.utils import get_domain

User = get_user_model()

__all__ = ["LoginView"]


class LoginView(FormView):
    form_class = LoginForm
    template_name = "users/login.html"

    def form_valid(self, form):
        """
        Create or retrieve a user trigger the send login email
        """
        user, created = User.objects.get_or_create(
            email=form.cleaned_data["email"]
        )
        if created:
            user.set_unusable_password()
            user.save()

        self.send_login_url(user=user)
        messages.success(
            self.request,
            "Thank you, please check your email for your magic link to log in to your account.",
            fail_silently=True,
        )
        return HttpResponseRedirect(self.get_success_url())

    def send_login_url(self, user):
        """
        Send an email to the user with a link to authenticate and log in
        """
        querystring = get_query_string(user=user)
        domain = get_domain(request=self.request)
        path = reverse("api_users:authenticate")
        url = f"{self.request.scheme}://{domain}{path}{querystring}"
        subject = "Your magic link to log in to the Democracy Club API"
        txt = render_to_string(
            template_name="users/email/login_message.txt",
            context={
                "authenticate_url": url,
                "subject": subject,
            },
        )
        return user.email_user(subject=subject, message=txt)

    def get_success_url(self):
        """
        Redirect to same page where success message will be displayed
        """
        return reverse("api_users:login")


class AuthenticateView(TemplateView):
    template_name = "users/authenticate.html"

    def get(self, request, *args, **kwargs):
        """
        Attempts to get user from the request, log them in, and redirect them to
        their profile page. Renders an error message if django-sesame fails to
        get a user from the request.
        """
        user = get_user(request)
        if not user:
            return super().get(request, *args, **kwargs)

        login(request, user)
        if not user.name:
            return redirect("api_users:add_profile_details")
        return redirect("api_users:profile")


class UpdateProfileDetailsView(UpdateView):
    form_class = UserProfileForm
    template_name = "users/update_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("api_users:profile")


class ProfileView(LoginRequiredMixin, FormView):
    template_name = "users/profile.html"
    form_class = APIKeyForm
    redirect_field_name = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_keys"] = self.request.user.api_keys.all()
        return context

    def form_valid(self, form):
        """
        Build a APIKey via the form, attach the user from the request and save.
        """
        key = form.save(commit=False)
        key.user = self.request.user
        key.save()
        messages.success(self.request, f"{key.name} API key was created")
        return super().form_valid(form=form)

    def get_success_url(self):
        return reverse("api_users:profile")


class DeleteAPIKeyView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "users/delete_key.html"
    context_object_name = "key"

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"{self.object.name} API key was deleted")
        return response

    def get_queryset(self):
        return self.request.user.api_keys.all()

    def get_success_url(self):
        return reverse("api_users:profile")


class RefreshAPIKeyView(LoginRequiredMixin, DetailView):
    template_name = "users/refresh_key.html"
    context_object_name = "key"

    def get_queryset(self):
        return self.request.user.api_keys.all()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.refresh_key()
        messages.success(
            request,
            f"{self.object.name} API key was refreshed",
            extra_tags="refreshed",
        )
        return redirect("api_users:profile")
