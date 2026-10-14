from decimal import Decimal

from django.test import TestCase

from products.models import Category, Price, Product, Supermarket
from .models import ShoppingList, ShoppingListItem
from .services import (
    calculate_estimated_savings,
    calculate_supermarket_breakdown,
    get_cheapest_supermarket_recommendation,
)


class SupermarketBreakdownTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.rice = Product.objects.create(name='Arroz', category=category)
        self.beans = Product.objects.create(name='Frijol', category=category)
        self.exito = Supermarket.objects.create(name='Éxito')
        self.carulla = Supermarket.objects.create(name='Carulla')
        self.d1 = Supermarket.objects.create(name='D1')
        Price.objects.create(product=self.rice, supermarket=self.exito, amount='3000')
        Price.objects.create(product=self.beans, supermarket=self.exito, amount='5000')
        Price.objects.create(product=self.rice, supermarket=self.carulla, amount='3500')
        Price.objects.create(product=self.beans, supermarket=self.carulla, amount='6000')
        Price.objects.create(product=self.rice, supermarket=self.d1, amount='1000')  # no beans
        self.shopping_list = ShoppingList.objects.create(name='Mercado')
        ShoppingListItem.objects.create(shopping_list=self.shopping_list, product=self.rice, quantity=2)
        ShoppingListItem.objects.create(shopping_list=self.shopping_list, product=self.beans, quantity=1)

    def test_cheapest_complete_supermarket_wins_over_cheaper_partial_one(self):
        breakdown, best = get_cheapest_supermarket_recommendation(
            calculate_supermarket_breakdown(self.shopping_list))
        self.assertEqual(best['supermarket'], self.exito)
        self.assertEqual(best['total'], Decimal('11000'))  # 2 x 3000 + 5000
        partial = next(entry for entry in breakdown if entry['supermarket'] == self.d1)
        self.assertFalse(partial['complete'])
        self.assertEqual(partial['missing'], [self.beans])
        self.assertEqual(breakdown[-1]['supermarket'], self.d1)

    def test_savings_compare_cheapest_and_most_expensive_complete_supermarket(self):
        breakdown, _ = get_cheapest_supermarket_recommendation(
            calculate_supermarket_breakdown(self.shopping_list))
        self.assertEqual(calculate_estimated_savings(breakdown), Decimal('2000'))  # 13000 - 11000

    def test_no_savings_with_fewer_than_two_complete_supermarkets(self):
        Price.objects.filter(supermarket=self.carulla).delete()
        breakdown, _ = get_cheapest_supermarket_recommendation(
            calculate_supermarket_breakdown(self.shopping_list))
        self.assertIsNone(calculate_estimated_savings(breakdown))
