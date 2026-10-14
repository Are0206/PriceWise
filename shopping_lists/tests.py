from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ShoppingList


class ShoppingListOwnershipTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='ana', password='clave-segura-1')
        self.other = User.objects.create_user(username='beto', password='clave-segura-2')
        self.shopping_list = ShoppingList.objects.create(name='Mercado', owner=self.owner)

    def test_anonymous_user_must_log_in_to_create(self):
        response = self.client.get(reverse('shopping_lists:create'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('shopping_lists:create')}")

    def test_panel_only_shows_own_lists(self):
        ShoppingList.objects.create(name='Lista de Beto', owner=self.other)
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.get(reverse('shopping_lists:index'))
        self.assertContains(response, 'Mercado')
        self.assertNotContains(response, 'Lista de Beto')

    def test_other_user_cannot_edit_delete_or_duplicate(self):
        self.client.login(username='beto', password='clave-segura-2')
        pk = self.shopping_list.pk
        self.assertEqual(self.client.get(reverse('shopping_lists:edit', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('shopping_lists:delete', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('shopping_lists:duplicate', args=[pk])).status_code, 404)
        self.assertTrue(ShoppingList.objects.filter(pk=pk).exists())

    def test_shared_link_is_read_only_for_others(self):
        self.client.login(username='beto', password='clave-segura-2')
        response = self.client.get(reverse('shopping_lists:detail', args=[self.shopping_list.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse('shopping_lists:edit', args=[self.shopping_list.pk]))

    def test_new_and_duplicated_lists_belong_to_the_user(self):
        self.client.login(username='ana', password='clave-segura-1')
        self.client.post(reverse('shopping_lists:duplicate', args=[self.shopping_list.pk]))
        self.assertEqual(ShoppingList.objects.get(name='Mercado (copia)').owner, self.owner)

    def test_delete_returns_to_home_with_lists_panel_open(self):
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.post(reverse('shopping_lists:delete', args=[self.shopping_list.pk]), follow=True)
        self.assertRedirects(response, f"{reverse('index')}?open_lists=true")
        self.assertContains(response, 'Lista borrada.')
        self.assertFalse(ShoppingList.objects.filter(pk=self.shopping_list.pk).exists())
