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
