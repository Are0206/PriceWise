from datetime import date
from decimal import Decimal

from django.test import TestCase

from products.integrations.lospreciosco.loaders import load_products, load_supermarkets
from products.models import Price, PriceHistory, Product, Supermarket

SUPERMARKETS = [{"api_id": 1, "name": "D1"}, {"api_id": 6, "name": "Éxito"}]


def product(amount_d1="2300.0", amount_exito=None, name="Crema de Leche Latti 200g"):
    prices = [{"supermarket_api_id": 1, "amount": Decimal(amount_d1)}]
    if amount_exito:
        prices.append({"supermarket_api_id": 6, "amount": Decimal(amount_exito)})
    return {"api_id": 9717, "name": name, "description": "marca: Latti",
            "image_url": "https://example.com/crema.jpg", "prices": prices}


class LoadSupermarketsTests(TestCase):
    def test_links_existing_supermarket_by_name_and_creates_new_ones(self):
        existing = Supermarket.objects.create(name="Éxito")
        by_id = load_supermarkets(SUPERMARKETS)
        self.assertEqual(by_id[6].pk, existing.pk)
        self.assertEqual(Supermarket.objects.get(name="D1").api_id, 1)
        load_supermarkets(SUPERMARKETS)
        self.assertEqual(Supermarket.objects.count(), 2)


class LoadProductsTests(TestCase):
    def setUp(self):
        self.stores = load_supermarkets(SUPERMARKETS)
        self.day1, self.day2 = date(2026, 10, 1), date(2026, 10, 2)

    def test_creates_product_prices_and_first_history(self):
        stats = load_products([product(amount_exito="2500")], self.stores, self.day1)
        self.assertEqual(stats["created"], 1)
        item = Product.objects.get(api_id=9717)
        self.assertEqual(item.category.name, "Otros")
        self.assertEqual(item.image_url, "https://example.com/crema.jpg")
        self.assertEqual(Price.objects.filter(product=item).count(), 2)
        self.assertEqual(PriceHistory.objects.count(), 2)

    def test_running_twice_does_not_duplicate_anything(self):
        load_products([product()], self.stores, self.day1)
        stats = load_products([product()], self.stores, self.day2)
        self.assertEqual((stats["created"], stats["updated"], stats["prices_changed"]), (0, 1, 0))
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Price.objects.count(), 1)
        self.assertEqual(PriceHistory.objects.count(), 1)

    def test_price_change_updates_price_and_adds_history(self):
        load_products([product("2300.0")], self.stores, self.day1)
        load_products([product("2450.0", name="Crema de Leche Latti 220g")], self.stores, self.day2)
        price = Price.objects.get()
        self.assertEqual(price.amount, Decimal("2450"))
        self.assertEqual(Product.objects.get().name, "Crema de Leche Latti 220g")
        self.assertEqual([h.amount for h in price.history.all()], [Decimal("2450"), Decimal("2300")])

    def test_second_change_on_the_same_day_replaces_that_days_row(self):
        load_products([product("2300.0")], self.stores, self.day1)
        load_products([product("2400.0")], self.stores, self.day1)
        self.assertEqual(PriceHistory.objects.get().amount, Decimal("2400"))

    def test_price_for_unknown_supermarket_is_skipped(self):
        data = product()
        data["prices"].append({"supermarket_api_id": 99, "amount": Decimal("1000")})
        stats = load_products([data], self.stores, self.day1)
        self.assertEqual(stats["skipped_prices"], 1)
        self.assertEqual(Price.objects.count(), 1)
