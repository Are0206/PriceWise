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


class QuickAddToListTests(TestCase):
    def setUp(self):
        from products.models import Category, Product
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz Diana 500g', category=category)
        self.owner = User.objects.create_user(username='ana', password='clave-segura-1')
        User.objects.create_user(username='beto', password='clave-segura-2')
        self.shopping_list = ShoppingList.objects.create(name='Mercado', owner=self.owner)
        self.url = reverse('shopping_lists:add_product', args=[self.shopping_list.pk])

    def test_adds_one_unit_then_one_more(self):
        self.client.login(username='ana', password='clave-segura-1')
        self.client.post(self.url, {'product': self.product.pk})
        response = self.client.post(self.url, {'product': self.product.pk}, HTTP_X_REQUESTED_WITH='fetch')
        self.assertEqual(response.json()['quantity'], 2)
        self.assertEqual(self.shopping_list.items.get(product=self.product).quantity, 2)

    def test_without_javascript_redirects_back_with_a_message(self):
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.post(self.url, {'product': self.product.pk, 'next': '/products/favorites/'})
        self.assertRedirects(response, '/products/favorites/', fetch_redirect_response=False)
        response = self.client.post(self.url, {'product': self.product.pk, 'next': 'https://evil.example.com/'})
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)

    def test_only_the_owner_can_add(self):
        self.client.login(username='beto', password='clave-segura-2')
        self.assertEqual(self.client.post(self.url, {'product': self.product.pk}).status_code, 404)
        self.assertFalse(self.shopping_list.items.exists())

    def test_bad_product_id_is_a_404(self):
        self.client.login(username='ana', password='clave-segura-1')
        self.assertEqual(self.client.post(self.url, {'product': 'abc'}).status_code, 404)

    def test_card_menu_lists_only_my_lists(self):
        ShoppingList.objects.create(name='Lista de Beto', owner=User.objects.get(username='beto'))
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Agregar a lista')
        self.assertContains(response, self.url)
        self.assertNotContains(response, 'Lista de Beto')
