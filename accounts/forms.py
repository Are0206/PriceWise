from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """Registration form: Django's UserCreationForm plus a required email.

    UserCreationForm already provides username, password1 and password2,
    runs the AUTH_PASSWORD_VALIDATORS configured in settings, and hashes
    the password on save. Only the email field is added here.
    """

    email = forms.EmailField(
        required=True,
        help_text='Required. Used to recover your account.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def clean_email(self):

        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email