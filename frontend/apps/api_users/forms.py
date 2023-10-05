from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from api_users.models import APIKey, CustomUser

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
        fields = ["name", "usage_reason", "api_plan"]
        widgets = {"usage_reason": forms.Textarea(attrs={"style": ""})}

    def __init__(self, **kwargs):
        self.user: CustomUser = kwargs.pop("user")
        self.has_prod_key = self.user.api_keys.exclude(
            api_plan="hobbyists"
        ).exists()
        super().__init__(**kwargs)
        if self.user.api_plan == "hobbyists" or self.has_prod_key:
            del self.fields["api_plan"]
            return
        choices = (
            ("hobbyists", "Development key"),
            (self.user.api_plan, "Production key"),
        )
        self.fields["api_plan"].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        key_plan = cleaned_data.get("api_plan", "hobbyists")
        if key_plan != "hobbyists" and self.has_prod_key:
            raise ValidationError("Only one production key allowed")

        if key_plan == "hobbyists" and self.user.api_plan != "enterprise":
            if self.user.api_plan == "hobbyists":
                has_existing_dev_keys = self.user.api_keys.exists()
                if has_existing_dev_keys:
                    raise ValidationError(
                        "Can't make more than one hobbyist key"
                    )
            if self.user.api_plan == "standard":
                has_existing_dev_keys = self.user.api_keys.exclude(
                    api_plan="standard"
                ).exists()
                if has_existing_dev_keys:
                    raise ValidationError(
                        "Can't make more than one development key"
                    )

        return cleaned_data
