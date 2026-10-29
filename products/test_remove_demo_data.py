from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from products.models import Category, Price, Product, Supermarket
from shopping_lists.models import ShoppingList, ShoppingListItem


class RemoveDemoDataTests(TestCase):
    def setUp(self):
        demo_category = Category.objects.create(name="Granos", slug="granos")
        real_category = Category.objects.create(name="Lácteos", slug="lacteos")
        self.demo = Product.objects.create(name="Arroz demo", category=demo_category)
        self.real = Product.objects.create(name="Leche", category=real_category, api_id=10)
        fake_store = Supermarket.objects.create(name="Supermu")
        real_store = Supermarket.objects.create(name="D1", api_id=1)
        Price.objects.create(product=self.demo, supermarket=fake_store, amount=1000)
        Price.objects.create(product=self.real, supermarket=real_store, amount=3000)
        shopping_list = ShoppingList.objects.create(name="Mercado")
        ShoppingListItem.objects.create(shopping_list=shopping_list, product=self.demo, quantity=1)
        ShoppingListItem.objects.create(shopping_list=shopping_list, product=self.real, quantity=1)

    def test_without_yes_only_reports(self):
        out = StringIO()
        call_command("remove_demo_data", stdout=out)
        self.assertIn("Nothing deleted", out.getvalue())
        self.assertEqual(Product.objects.count(), 2)

    def test_with_yes_keeps_only_imported_data(self):
        call_command("remove_demo_data", "--yes", stdout=StringIO())
        self.assertEqual(list(Product.objects.all()), [self.real])
        self.assertEqual(list(Supermarket.objects.values_list("name", flat=True)), ["D1"])
        self.assertEqual(list(Category.objects.values_list("name", flat=True)), ["Lácteos"])
        self.assertEqual(ShoppingListItem.objects.get().product, self.real)

    def test_refuses_when_nothing_was_imported(self):
        Product.objects.filter(api_id__isnull=False).update(api_id=None)
        call_command("remove_demo_data", "--yes", stdout=StringIO())
        self.assertTrue(Product.objects.filter(pk=self.demo.pk).exists())
