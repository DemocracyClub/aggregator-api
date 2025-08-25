from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from api_users.models import APIKey, CustomUser
from common.conf import settings

User = get_user_model()

__all__ = ["LoginForm"]


class LoginForm(forms.Form):
    """
    Login form for a User.
    """

    email = forms.EmailField(required=True)

    def clean_email(self):
        """
        Normalize the entered email
        """
        email = self.cleaned_data["email"]
        return User.objects.normalize_email(email)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("name",)


class APIKeyForm(forms.ModelForm):
    class Meta:
        model = APIKey
        fields = ["name", "usage_reason", "key_type"]
        widgets = {"usage_reason": forms.Textarea(attrs={"style": ""})}

    def __init__(self, **kwargs):
        self.user: CustomUser = kwargs.pop("user")
        super().__init__(**kwargs)

        choices = self.get_allowed_key_types()
        if not choices:
            del self.fields["key_type"]
            return
        self.fields["key_type"].choices = choices

    def get_allowed_key_types(self):
        """
        There are three cases:

        1. The user is a hobbyist. This means they can't pick their key type
        2. The user is a standard user. They can make one production key and multiple development keys
        3. The user is an enterprise user, they can make multiple of any sort of keys
        """

        if self.user.api_plan == "hobbyists":
            return None

        choices = [
            ("development", "Development"),
        ]
        if (
            self.user.api_plan == settings.API_PLANS["enterprise"].value
            or not self.user.api_keys.filter(key_type="production").exists()
        ):
            choices.append(("production", "Production key"))
            return choices

        return None

    def clean(self):
        cleaned_data = super().clean()

        api_plan = self.user.api_plan

        if api_plan == "enterprise":
            # For "enterprise" we don't need to validate because any combo is valid.
            # That's what you get for giving us the big bucks
            return cleaned_data

        if api_plan == settings.API_PLANS["hobbyists"].value:
            has_existing_keys = self.user.api_keys.exists()
            if has_existing_keys:
                raise ValidationError("Can't make more than one hobbyist key")
            return cleaned_data

        # Standard is the only remaining option
        has_prod_key = self.user.api_keys.filter(key_type="production").exists()
        if has_prod_key and cleaned_data.get("key_type") == "production":
            # We should never get here, because the option is removed from the
            # form in self.__init__
            raise ValidationError("Only one production key allowed")

        return cleaned_data

    def save(self, commit=True):
        model: CustomUser = super().save(commit=False)
        model.user = self.user
        return super().save(commit=True)
