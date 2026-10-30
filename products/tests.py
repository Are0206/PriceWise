from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Favorite, Price, Product, ProductReview, Supermarket


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

    def test_prices_use_dots_for_thousands(self):
        response = self.client.get(reverse('products:compare', args=[self.product.pk]))
        self.assertContains(response, '$2.900,00')

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
        self.assertContains(response, 'Aún no hay precios disponibles')


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
        self.assertFalse(ProductReview.objects.filter(product=self.product).exists())

    def test_logged_in_user_can_submit_review(self):
        self.client.login(username='tester', password='testpass123')
        response = self.client.post(
            reverse('products:submit_review', args=[self.product.pk]),
            {'rating': '4', 'comment': 'Bueno'},
        )
        self.assertRedirects(response, reverse('products:detail', args=[self.product.pk]))
        review = ProductReview.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Bueno')

    def test_submitting_again_updates_instead_of_duplicating(self):
        self.client.login(username='tester', password='testpass123')
        self.client.post(reverse('products:submit_review', args=[self.product.pk]), {'rating': '4'})
        self.client.post(reverse('products:submit_review', args=[self.product.pk]), {'rating': '5'})

        self.assertEqual(ProductReview.objects.filter(product=self.product, user=self.user).count(), 1)
        self.assertEqual(ProductReview.objects.get(product=self.product, user=self.user).rating, 5)

    def test_owner_can_delete_own_review(self):
        review = ProductReview.objects.create(user=self.user, product=self.product, rating=3)
        self.client.login(username='tester', password='testpass123')

        response = self.client.post(reverse('products:delete_review', args=[review.pk]))

        self.assertRedirects(response, reverse('products:detail', args=[self.product.pk]))
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())

    def test_user_cannot_delete_someone_elses_review(self):
        other_user = User.objects.create_user(username='other', password='testpass123')
        review = ProductReview.objects.create(user=other_user, product=self.product, rating=3)
        self.client.login(username='tester', password='testpass123')

        response = self.client.post(reverse('products:delete_review', args=[review.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProductReview.objects.filter(pk=review.pk).exists())


class EmptyReviewsTests(TestCase):
    def test_product_and_supermarket_show_empty_reviews_message(self):
        category = Category.objects.create(name='Granos', slug='granos')
        product = Product.objects.create(name='Arroz Diana 500g', category=category)
        supermarket = Supermarket.objects.create(name='Exito')
        for url in (reverse('products:detail', args=[product.pk]),
                    reverse('products:supermarkets_details', args=[supermarket.pk])):
            self.assertContains(self.client.get(url), 'Aún no hay reseñas.')


class FavoriteProductsListTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.rice = Product.objects.create(name='Arroz Diana 500g', category=category)
        self.beans = Product.objects.create(name='Frijol Cargamanto', category=category)
        self.salt = Product.objects.create(name='Sal Refisal', category=category)
        self.user = User.objects.create_user(username='ana', password='clave-segura-1')
        other = User.objects.create_user(username='beto', password='clave-segura-2')
        Favorite.objects.create(user=self.user, product=self.rice)
        Favorite.objects.create(user=self.user, product=self.beans)
        Favorite.objects.create(user=other, product=self.salt)
        # Same-millisecond timestamps would make the order random; fix them.
        Favorite.objects.filter(product=self.rice).update(created_at=timezone.now() - timedelta(days=1))

    def test_anonymous_user_is_sent_to_login(self):
        url = reverse('products:favorites')
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_lists_only_the_users_favorites_newest_first(self):
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.get(reverse('products:favorites'))
        self.assertEqual(list(response.context['products']), [self.beans, self.rice])
        self.assertNotContains(response, 'Sal Refisal')

    def test_shows_empty_state_without_favorites(self):
        Favorite.objects.filter(user=self.user).delete()
        self.client.login(username='ana', password='clave-segura-1')
        self.assertContains(self.client.get(reverse('products:favorites')), 'Aún no tienes productos favoritos.')


class StarRatingTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz Diana 500g', category=category)
        self.user = User.objects.create_user(username='ana', password='clave-segura-1')

    def test_review_form_uses_five_star_radios(self):
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.get(reverse('products:detail', args=[self.product.pk]))
        self.assertContains(response, 'type="radio"', count=5)
        self.assertNotContains(response, 'id="review-rating"')

    def test_saved_rating_is_checked_and_shown_as_stars(self):
        ProductReview.objects.create(user=self.user, product=self.product, rating=4)
        self.client.login(username='ana', password='clave-segura-1')
        response = self.client.get(reverse('products:detail', args=[self.product.pk]))
        self.assertContains(response, 'value="4" required checked')
        self.assertContains(response, 'aria-label="4 de 5 estrellas"')
        self.assertContains(response, 'star--filled', count=4)


class CatalogPaginationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Abarrotes', slug='abarrotes')
        Product.objects.bulk_create([
            Product(name=f"Producto {i:03d}", category=self.category)
            for i in range(1, 56)
        ])

    def test_first_page_contains_24_products(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 24)
        self.assertEqual(page_obj.number, 1)
        self.assertEqual(page_obj.paginator.num_pages, 3)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())

    def test_second_page_navigation(self):
        response = self.client.get(reverse('index'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 24)
        self.assertEqual(page_obj.number, 2)
        self.assertTrue(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())

    def test_last_page_contains_remainder(self):
        response = self.client.get(reverse('index'), {'page': 3})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj), 7)
        self.assertEqual(page_obj.number, 3)
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())

    def test_invalid_page_defaults_to_first_or_last(self):
        response = self.client.get(reverse('index'), {'page': 'abc'})
        self.assertEqual(response.context['page_obj'].number, 1)
        response = self.client.get(reverse('index'), {'page': 999})
        self.assertEqual(response.context['page_obj'].number, 3)

    def test_pagination_links_preserve_active_filters(self):
        response = self.client.get(reverse('index'), {'category': 'abarrotes', 'page': 1})
        self.assertContains(response, 'category=abarrotes')
        self.assertContains(response, 'page=2')


class ParsePriceTests(TestCase):
    def test_valid_prices(self):
        from .services import parse_price
        self.assertEqual(str(parse_price('2500')), '2500')
        self.assertEqual(str(parse_price(' 99.50 ')), '99.50')
        self.assertEqual(str(parse_price('0')), '0')

    def test_invalid_prices_are_ignored(self):
        from .services import parse_price
        for raw in (None, '', 'abc', 'NaN', 'nan', 'Infinity', '-Infinity', 'sNaN', '-5', '1e', '1,000'):
            self.assertIsNone(parse_price(raw), raw)

    def test_catalog_does_not_crash_on_non_finite_prices(self):
        for params in ({'min_price': 'NaN', 'max_price': '5000'}, {'min_price': '0', 'max_price': 'Infinity'}):
            response = self.client.get(reverse('index'), params)
            self.assertEqual(response.status_code, 200, params)


class ToggleFavoriteTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz', category=category)
        self.user = User.objects.create_user('ana', password='clave-segura-123')
        self.client.force_login(self.user)
        self.url = reverse('products:toggle_favorite', args=[self.product.pk])

    def test_toggle_adds_then_removes(self):
        self.client.post(self.url)
        self.assertTrue(Favorite.objects.filter(user=self.user, product=self.product).exists())
        self.client.post(self.url)
        self.assertFalse(Favorite.objects.filter(user=self.user, product=self.product).exists())

    def test_get_does_not_change_favorites(self):
        self.client.get(self.url)
        self.assertFalse(Favorite.objects.exists())

    def test_redirects_back_to_same_site_referer(self):
        response = self.client.post(self.url, HTTP_REFERER='http://testserver/?page=2')
        self.assertEqual(response['Location'], 'http://testserver/?page=2')

    def test_external_referer_is_not_followed(self):
        response = self.client.post(self.url, HTTP_REFERER='https://evil.example.com/phish')
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])
        self.assertFalse(Favorite.objects.exists())


class CatalogFiltersKeepEachOtherTests(TestCase):
    def setUp(self):
        Category.objects.create(name='Granos', slug='granos')

    def test_filter_form_carries_active_category_and_sort(self):
        response = self.client.get(reverse('index'), {'category': 'granos', 'sort': 'price_desc', 'q': 'arroz'})
        self.assertContains(response, '<input type="hidden" name="category" value="granos">', html=True)
        self.assertContains(response, '<input type="hidden" name="sort" value="price_desc">', html=True)
        self.assertContains(response, '<input type="hidden" name="q" value="arroz">', html=True)

    def test_clicked_button_wins_over_hidden_value(self):
        # The hidden category comes first in the form; the clicked button is sent last.
        response = self.client.get('/?category=granos&sort=price_asc&category=lacteos')
        self.assertEqual(response.context['category_filter'], 'lacteos')
        self.assertEqual(response.context['sort'], 'price_asc')


class ReviewFeedbackTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz', category=category)
        self.supermarket = Supermarket.objects.create(name='D1')
        self.user = User.objects.create_user('ana', password='clave-segura-123')
        self.client.force_login(self.user)

    def test_invalid_rating_shows_an_error_and_saves_nothing(self):
        for rating in ('', '0', '6', 'cinco'):
            response = self.client.post(reverse('products:submit_review', args=[self.product.pk]),
                                        {'rating': rating, 'comment': 'x'}, follow=True)
            self.assertContains(response, 'Elige una calificación de 1 a 5 estrellas')
        self.assertFalse(ProductReview.objects.exists())

    def test_valid_rating_is_saved_with_confirmation(self):
        response = self.client.post(reverse('products:submit_review', args=[self.product.pk]),
                                    {'rating': '4', 'comment': '  Buen arroz  '}, follow=True)
        self.assertContains(response, 'Tu reseña quedó guardada')
        review = ProductReview.objects.get()
        self.assertEqual((review.rating, review.comment), (4, 'Buen arroz'))

    def test_supermarket_review_uses_the_same_rules(self):
        from .models import SupermarketReview
        url = reverse('products:submit_supermarket_review', args=[self.supermarket.pk])
        self.client.post(url, {'rating': '9'})
        self.assertFalse(SupermarketReview.objects.exists())
        self.client.post(url, {'rating': '5', 'comment': 'Bien'})
        self.assertEqual(SupermarketReview.objects.get().rating, 5)


class DataIntegrityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz', category=self.category)
        self.user = User.objects.create_user('ana', password='clave-segura-123')

    def test_category_with_products_cannot_be_deleted(self):
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.category.delete()
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_empty_category_can_be_deleted(self):
        empty = Category.objects.create(name='Vacía', slug='vacia')
        empty.delete()
        self.assertFalse(Category.objects.filter(slug='vacia').exists())

    def test_database_rejects_out_of_range_ratings(self):
        from django.db import IntegrityError, transaction
        from .models import SupermarketReview
        supermarket = Supermarket.objects.create(name='D1')
        for rating in (0, 6):
            with self.assertRaises(IntegrityError), transaction.atomic():
                ProductReview.objects.create(user=self.user, product=self.product, rating=rating)
            with self.assertRaises(IntegrityError), transaction.atomic():
                SupermarketReview.objects.create(user=self.user, supermarket=supermarket, rating=rating)


class NegativeAuthorizationTests(TestCase):
    """User B must not read or change user A's private resources."""

    def setUp(self):
        from .models import SupermarketReview
        category = Category.objects.create(name='Granos', slug='granos')
        self.product = Product.objects.create(name='Arroz', category=category)
        self.supermarket = Supermarket.objects.create(name='D1')
        self.ana = User.objects.create_user('ana', password='clave-segura-123')
        self.beto = User.objects.create_user('beto', password='clave-segura-456')
        self.product_review = ProductReview.objects.create(user=self.ana, product=self.product, rating=5, comment='A')
        self.supermarket_review = SupermarketReview.objects.create(user=self.ana, supermarket=self.supermarket, rating=4)
        Favorite.objects.create(user=self.ana, product=self.product)
        self.client.force_login(self.beto)

    def test_cannot_delete_someone_elses_reviews(self):
        from .models import SupermarketReview
        response = self.client.post(reverse('products:delete_review', args=[self.product_review.pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('products:delete_supermarket_review', args=[self.supermarket_review.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProductReview.objects.filter(pk=self.product_review.pk).exists())
        self.assertTrue(SupermarketReview.objects.filter(pk=self.supermarket_review.pk).exists())

    def test_reviewing_does_not_overwrite_someone_elses_review(self):
        self.client.post(reverse('products:submit_review', args=[self.product.pk]), {'rating': '1', 'comment': 'B'})
        self.product_review.refresh_from_db()
        self.assertEqual((self.product_review.rating, self.product_review.comment), (5, 'A'))
        self.assertEqual(ProductReview.objects.count(), 2)

    def test_favorites_page_and_toggle_only_touch_own_favorites(self):
        response = self.client.get(reverse('products:favorites'))
        self.assertNotContains(response, 'Arroz')
        self.client.post(reverse('products:toggle_favorite', args=[self.product.pk]))
        self.client.post(reverse('products:toggle_favorite', args=[self.product.pk]))
        self.assertTrue(Favorite.objects.filter(user=self.ana, product=self.product).exists())
