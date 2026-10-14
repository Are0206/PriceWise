from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ana', password='vieja-clave-123')
        self.client.login(username='ana', password='vieja-clave-123')

    def test_confirmation_message_is_shown_after_changing_password(self):
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'vieja-clave-123',
            'new_password1': 'nueva-clave-456',
            'new_password2': 'nueva-clave-456',
        }, follow=True)
        self.assertContains(response, 'Tu contraseña se cambió correctamente.')
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class AuthPagesTests(TestCase):
    def test_login_and_register_pages_are_in_spanish(self):
        self.assertContains(self.client.get(reverse('accounts:login')), 'Iniciar sesión')
        self.assertContains(self.client.get(reverse('accounts:register')), 'Crea tu cuenta')

    def test_wrong_password_shows_spanish_error(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'nadie', 'password': 'x'})
        self.assertContains(response, 'Por favor')


class LoginRedirectTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='ana', password='clave-segura-1')

    def test_login_returns_to_the_page_in_next(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'ana', 'password': 'clave-segura-1', 'next': '/products/supermarkets/'})
        self.assertRedirects(response, '/products/supermarkets/', fetch_redirect_response=False)

    def test_login_ignores_next_pointing_to_another_site(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'ana', 'password': 'clave-segura-1', 'next': 'https://evil.example.com/'})
        self.assertRedirects(response, '/', fetch_redirect_response=False)
