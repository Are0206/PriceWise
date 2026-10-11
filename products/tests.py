from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Price, Product, Review, Supermarket


class ProductDetailViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(
            name='Arroz Diana 500g',
            description='Arroz blanco, paquete de 500 gramos.',
            category=category,
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
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz Diana 500g', category=category)
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
        category = Category.objects.get(slug='granos')
        lonely_product = Product.objects.create(name='Producto sin precios', category=category)
        response = self.client.get(reverse('products:compare', args=[lonely_product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No prices available yet')


class ReviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz Diana 500g', category=category)
        self.user = User.objects.create_user(username='tester', password='testpass123')

    def test_anonymous_cannot_submit_review(self):
        response = self.client.post(
            reverse('products:submit_review', args=[self.product.pk]),
            {'rating': '4'},
        )
        self.assertRedirects(response, f"/accounts/login/?next=/products/{self.product.pk}/review/")
        self.assertFalse(Review.objects.filter(product=self.product).exists())

    def test_logged_in_user_can_submit_review(self):
        self.client.login(username='tester', password='testpass123')
        response = self.client.post(
            reverse('products:submit_review', args=[self.product.pk]),
            {'rating': '4', 'comment': 'Bueno'},
        )
        self.assertRedirects(response, reverse('products:detail', args=[self.product.pk]))
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Bueno')

    def test_submitting_again_updates_instead_of_duplicating(self):
        self.client.login(username='tester', password='testpass123')
        self.client.post(reverse('products:submit_review', args=[self.product.pk]), {'rating': '4'})
        self.client.post(reverse('products:submit_review', args=[self.product.pk]), {'rating': '5'})

        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)
        self.assertEqual(Review.objects.get(product=self.product, user=self.user).rating, 5)

    def test_owner_can_delete_own_review(self):
        review = Review.objects.create(user=self.user, product=self.product, rating=3)
        self.client.login(username='tester', password='testpass123')

        response = self.client.post(reverse('products:delete_review', args=[review.pk]))

        self.assertRedirects(response, reverse('products:detail', args=[self.product.pk]))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_user_cannot_delete_someone_elses_review(self):
        other_user = User.objects.create_user(username='other', password='testpass123')
        review = Review.objects.create(user=other_user, product=self.product, rating=3)
        self.client.login(username='tester', password='testpass123')

        response = self.client.post(reverse('products:delete_review', args=[review.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())
