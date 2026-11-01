from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User


class DescribedByMixin:
    """Links each field to the help text the template prints next to it (aria-describedby)."""

    described_by = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, help_id in self.described_by.items():
            self.fields[field_name].widget.attrs['aria-describedby'] = help_id


class RegisterForm(DescribedByMixin, UserCreationForm):
    """Registration form: Django's UserCreationForm plus a required email.

    UserCreationForm already provides username, password1 and password2,
    runs the AUTH_PASSWORD_VALIDATORS configured in settings, and hashes
    the password on save. Only the email field is added here.
    """

    email = forms.EmailField(
        required=True,
        help_text='Lo usamos para recuperar tu cuenta.',
    )

    described_by = {'username': 'username-help', 'email': 'email-help', 'password1': 'password-rules'}

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):

        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email


class ChangePasswordForm(DescribedByMixin, PasswordChangeForm):
    described_by = {'new_password1': 'password-rules'}
