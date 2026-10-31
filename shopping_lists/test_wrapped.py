from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from products.models import Category, Price, Product, Supermarket

from .models import ShoppingList, ShoppingListItem
from .services import build_wrapped


def make_catalog():
    granos = Category.objects.create(name='Granos', slug='granos')
    aseo = Category.objects.create(name='Aseo', slug='aseo')
    d1 = Supermarket.objects.create(name='D1')
    jumbo = Supermarket.objects.create(name='Jumbo')
    products = {
        'arroz': Product.objects.create(name='Arroz', category=granos),
        'jabon': Product.objects.create(name='Jabón', category=aseo),
        'sal': Product.objects.create(name='Sal', category=granos),
        'te': Product.objects.create(name='Té', category=granos),
    }
    Price.objects.create(product=products['arroz'], supermarket=d1, amount=2000)
    Price.objects.create(product=products['arroz'], supermarket=jumbo, amount=2600)
    Price.objects.create(product=products['jabon'], supermarket=d1, amount=5000)
    Price.objects.create(product=products['jabon'], supermarket=jumbo, amount=4000)
    Price.objects.create(product=products['sal'], supermarket=d1, amount=1000)
    return products


def make_list(owner, name, items):
    shopping_list = ShoppingList.objects.create(name=name, owner=owner)
    for product, quantity in items:
        ShoppingListItem.objects.create(shopping_list=shopping_list, product=product, quantity=quantity)
    return shopping_list


class BuildWrappedTests(TestCase):
    def setUp(self):
        p = make_catalog()
        self.products = p
        self.ana = User.objects.create_user('ana', password='clave-segura-1')
        beto = User.objects.create_user('beto', password='clave-segura-2')
        self.l1 = make_list(self.ana, 'L1', [(p['arroz'], 2), (p['jabon'], 1)])
        self.l2 = make_list(self.ana, 'L2', [(p['arroz'], 1), (p['sal'], 3), (p['te'], 1)])
        make_list(beto, 'De Beto', [(p['arroz'], 10)])

    def test_totals(self):
        w = build_wrapped(self.ana)
        self.assertEqual(w['total_with'], 13000)
        self.assertEqual(w['total_without'], 15800)
        self.assertEqual(w['saved'], 2800)
        self.assertEqual(w['saved_pct'], Decimal('17.7'))
        self.assertEqual(w['profile']['title'], 'Cazador de ofertas')

    def test_per_list_in_creation_order(self):
        w = build_wrapped(self.ana)
        self.assertEqual([(r['name'], r['with'], r['without']) for r in w['per_list']],
                         [('L1', 8000, 10200), ('L2', 5000, 5600)])
        self.assertEqual(w['first_date'], self.l1.created_at.date())
        self.assertEqual(w['last_date'], self.l2.created_at.date())

    def test_top_store_counts_items_with_two_prices_only(self):
        w = build_wrapped(self.ana)
        self.assertEqual(w['top_store'], {'name': 'D1', 'wins': 2, 'of': 3})
        self.assertEqual(w['runner_up'], {'name': 'Jumbo', 'wins': 1})

    def test_star_product_gap_is_per_unit(self):
        # Jabón's 1000 per unit beats Arroz's 600, even though Arroz has more units.
        self.assertEqual(build_wrapped(self.ana)['star_product'], {'name': 'Jabón', 'gap': 1000, 'lists': 1})

    def test_top_category(self):
        self.assertEqual(build_wrapped(self.ana)['top_category'], {'name': 'Granos', 'saved': 1800})

    def test_counts(self):
        w = build_wrapped(self.ana)
        self.assertEqual((w['list_count'], w['distinct_products'], w['units'], w['unpriced_items']), (2, 4, 8, 1))
        self.assertEqual(w['avg_per_list'], 6500)

    def test_other_users_lists_are_ignored(self):
        self.assertNotIn('De Beto', [r['name'] for r in build_wrapped(self.ana)['per_list']])

    def test_empty_list_counts_but_adds_nothing(self):
        make_list(self.ana, 'Vacía', [])
        w = build_wrapped(self.ana)
        self.assertEqual(w['list_count'], 3)
        self.assertEqual(w['total_with'], 13000)
        self.assertEqual(w['avg_per_list'], Decimal('4333.33'))

    def test_no_lists(self):
        w = build_wrapped(User.objects.create_user('carla', password='clave-segura-3'))
        self.assertEqual((w['list_count'], w['saved'], w['saved_pct']), (0, 0, 0))
        self.assertIsNone(w['top_store'])
        self.assertIsNone(w['star_product'])
        self.assertIsNone(w['top_category'])
        self.assertEqual(w['profile']['title'], 'Comprador tranquilo')

    def test_query_count_is_constant(self):
        with self.assertNumQueries(3):
            build_wrapped(self.ana)
        for i in range(5):
            make_list(self.ana, f'Extra {i}', [(self.products['arroz'], 1), (self.products['jabon'], 2)])
        with self.assertNumQueries(3):
            build_wrapped(self.ana)


class ProfileThresholdTests(TestCase):
    def test_boundaries(self):
        from .services import _profile
        cases = {'0': 'Comprador tranquilo', '4.9': 'Comprador tranquilo', '5.0': 'Buen ojo',
                 '15.0': 'Buen ojo', '15.1': 'Cazador de ofertas'}
        for pct, title in cases.items():
            self.assertEqual(_profile(Decimal(pct))['title'], title, pct)


class WrappedChartTests(TestCase):
    def rows(self, *pairs):
        return [{'name': f'L{i}', 'created_at': None, 'with': Decimal(w), 'without': Decimal(wo)}
                for i, (w, wo) in enumerate(pairs, 1)]

    def points(self, text):
        return [tuple(map(float, pair.split(','))) for pair in text.split()]

    def test_none_for_fewer_than_two_lists(self):
        from .services import wrapped_chart
        self.assertIsNone(wrapped_chart([]))
        self.assertIsNone(wrapped_chart(self.rows(('8000', '10200'))))

    def test_cumulative_and_inside_plot(self):
        from .services import wrapped_chart
        chart = wrapped_chart(self.rows(('8000', '10200'), ('5000', '5600'), ('3000', '3000')))
        with_pts, without_pts = self.points(chart['with_points']), self.points(chart['without_points'])
        self.assertEqual(len(with_pts), 3)
        self.assertLess(with_pts[-1][1], with_pts[0][1])  # higher on screen = more money
        for (x, y) in with_pts + without_pts:
            self.assertTrue(0 <= x <= chart['width'] and 0 <= y <= chart['height'], (x, y))
        for (_, y_with), (_, y_without) in zip(with_pts, without_pts):
            self.assertGreaterEqual(y_with, y_without)  # "without" never below "with"
        self.assertEqual([l['text'] for l in chart['labels']], ['Compra 1', 'Compra 3'])

    def test_colors_are_the_validated_pair(self):
        from .services import wrapped_chart
        chart = wrapped_chart(self.rows(('1', '2'), ('1', '2')))
        self.assertEqual(chart['colors'], {'with': '#1A7F37', 'without': '#2a78d6'})


class WrappedPageTests(TestCase):
    def setUp(self):
        from django.urls import reverse
        self.url = reverse('shopping_lists:wrapped')
        self.products = make_catalog()
        self.ana = User.objects.create_user('ana', password='clave-segura-1')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_full_wrapped(self):
        p = self.products
        make_list(self.ana, 'L1', [(p['arroz'], 2), (p['jabon'], 1)])
        make_list(self.ana, 'L2', [(p['arroz'], 1), (p['sal'], 3), (p['te'], 1)])
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="wrapped-card', count=8)
        self.assertContains(response, '$2.800,00')
        self.assertContains(response, '17,7 %')
        self.assertContains(response, 'Cazador de ofertas')
        self.assertContains(response, 'Comparamos cada producto contra el supermercado más caro que lo vende.')
        self.assertRegex(response.content.decode(), r'<polyline[^>]*points="12\.0,\d')

    def test_one_list_has_no_chart(self):
        make_list(self.ana, 'L1', [(self.products['arroz'], 1)])
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertContains(response, 'Crea otra lista para ver tu curva')
        self.assertNotContains(response, '<polyline')

    def test_no_lists_shows_one_invitation_card(self):
        from django.urls import reverse
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertContains(response, 'class="wrapped-card', count=1)
        self.assertContains(response, f'href="{reverse("shopping_lists:create")}"')

    def test_panel_links_to_wrapped_only_with_session(self):
        from django.urls import reverse
        panel = reverse('shopping_lists:index')
        self.assertNotContains(self.client.get(panel), self.url)
        self.client.force_login(self.ana)
        self.assertContains(self.client.get(panel), self.url)
