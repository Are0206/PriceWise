from django.test import TestCase
from django.urls import reverse

from .models import ShoppingList


class DeleteShoppingListTests(TestCase):
    def test_delete_returns_to_home_with_lists_panel_open(self):
        shopping_list = ShoppingList.objects.create(name='Mercado')
        response = self.client.post(reverse('shopping_lists:delete', args=[shopping_list.pk]), follow=True)
        self.assertRedirects(response, f"{reverse('index')}?open_lists=true")
        self.assertContains(response, 'Lista borrada.')
        self.assertFalse(ShoppingList.objects.filter(pk=shopping_list.pk).exists())
