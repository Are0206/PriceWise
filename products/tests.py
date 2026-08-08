from django.test import TestCase
from django.urls import reverse

from .models import Price, Product, Supermarket


class ProductDetailViewTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Arroz Diana 500g',
            description='Arroz blanco, paquete de 500 gramos.',
        )

    def test_returns_200_for_existing_product(self):
        response = self.client.get(reverse('products:detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, self.product.description)

    def test_returns_404_for_missing_product(self):
        response = self.client.get(reverse('products:detail', args=[9999]))
        self.assertEqual(response.status_code, 404)


class ComparePricesViewTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Arroz Diana 500g')
        exito = Supermarket.objects.create(name='Exito')
        carulla = Supermarket.objects.create(name='Carulla')
        jumbo = Supermarket.objects.create(name='Jumbo')
        Price.objects.create(product=self.product, supermarket=exito, amount='3200.00')
        Price.objects.create(product=self.product, supermarket=carulla, amount='2900.00')
        Price.objects.create(product=self.product, supermarket=jumbo, amount='3100.00')

    def test_returns_200_for_existing_product(self):
        response = self.client.get(reverse('products:compare', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_prices_sorted_cheapest_first(self):
        response = self.client.get(reverse('products:compare', args=[self.product.pk]))
        prices = list(response.context['prices'])
        self.assertEqual([p.supermarket.name for p in prices], ['Carulla', 'Jumbo', 'Exito'])

    def test_cheapest_supermarket_is_highlighted(self):
        response = self.client.get(reverse('products:compare', args=[self.product.pk]))
        self.assertContains(response, 'class="cheapest"')
        self.assertContains(response, 'Carulla')

    def test_returns_404_for_missing_product(self):
        response = self.client.get(reverse('products:compare', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_product_with_no_prices_shows_empty_state(self):
        lonely_product = Product.objects.create(name='Producto sin precios')
        response = self.client.get(reverse('products:compare', args=[lonely_product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No prices available yet')
