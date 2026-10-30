from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from products.integrations.lospreciosco import pipeline
from products.integrations.lospreciosco.client import LosPreciosError
from products.models import Category, Product


def raw_item(item_id, price=2300):
    return {"ID": item_id, "Producto": f"Producto {item_id}", "Marca": None, "Tamaño": None,
            "Unidad": None, "Complemento": None, "RutaImagen": None,
            "ÍtemsTiendas": [{"TiendaID": 1, "Precio": price}]}


class FakeClient:
    """Stores: store 1 has 3 items over two pages, store 2 fails, store 6 is Éxito (no products)."""

    def __init__(self, fail_store=None):
        self.fail_store = fail_store
        self.pages_requested = []

    def get_supermarkets(self, municipio_id=2):
        return [{"ID": 1, "Nombre": "D1"}, {"ID": 2, "Nombre": "Jumbo"}, {"ID": 6, "Nombre": "Éxito"}]

    def get_supermarkets_details(self, id=None, page=None, **kwargs):
        self.pages_requested.append((id, page))
        if id == self.fail_store:
            raise LosPreciosError("server error", error_id=2)
        pages = {1: [raw_item(1), raw_item(2)], 2: [raw_item(3)]} if id == 1 else {}
        return {"Ítems": pages.get(page, []), "TotalÍtems": 3 if id == 1 else 0}


class PipelineTests(TestCase):
    def test_walks_every_page_and_stops_at_the_total(self):
        client = FakeClient()
        summary = pipeline.run(client, store_api_ids=[1], categories=["Despensa"])
        self.assertEqual(summary["created"], 3)
        self.assertEqual(client.pages_requested, [(1, 1), (1, 2)])

    def test_supermarkets_without_products_are_skipped_automatically(self):
        client = FakeClient()
        summary = pipeline.run(client, categories=["Despensa"])
        # Store 6 (Éxito) must not be queried for catalog pages
        requested_stores = [store_id for store_id, _ in client.pages_requested]
        self.assertNotIn(6, requested_stores)
        self.assertIn(1, requested_stores)

    def test_a_failing_store_is_skipped_not_fatal(self):
        summary = pipeline.run(FakeClient(fail_store=2), categories=["Despensa"])
        self.assertEqual(summary["failed_stores"], ["Jumbo / Despensa"])
        self.assertEqual(Product.objects.count(), 3)

    def test_fatal_api_error_stops_the_run(self):
        client = FakeClient()
        client.get_supermarkets = mock.Mock(side_effect=LosPreciosError("bad key", error_id=1))
        with self.assertRaises(LosPreciosError):
            pipeline.run(client)


class SyncCommandTests(TestCase):
    def test_command_reads_key_and_prints_summary(self):
        with mock.patch.dict("os.environ", {"LOSPRECIOS_API_KEY": "test-key"}), \
             mock.patch("products.management.commands.sync_losprecios.LosPreciosClient",
                        return_value=FakeClient()) as client_class:
            from io import StringIO
            out = StringIO()
            call_command("sync_losprecios", "--store", "1", stdout=out)
        client_class.assert_called_once_with("test-key")
        self.assertIn("3 products created", out.getvalue())


class CategoryTests(TestCase):
    def test_products_get_the_api_category_they_were_fetched_from(self):
        pipeline.run(FakeClient(), store_api_ids=[1], categories=["Despensa"])
        self.assertEqual(set(Product.objects.values_list("category__name", flat=True)), {"Despensa"})

    def test_reimport_moves_products_out_of_the_default_category(self):
        pipeline.run(FakeClient(), store_api_ids=[1], categories=["Despensa"])
        Product.objects.update(category=Category.objects.create(name="Otros", slug="otros"))
        pipeline.run(FakeClient(), store_api_ids=[1], categories=["Bebidas"])
        self.assertEqual(set(Product.objects.values_list("category__name", flat=True)), {"Bebidas"})
