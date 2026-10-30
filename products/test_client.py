from unittest import mock

import requests
from django.test import SimpleTestCase

from products.integrations.lospreciosco import client as client_module
from products.integrations.lospreciosco.client import (LosPreciosClient, LosPreciosError,
                                                       parse_retry_after)


def response(status=200, json_data=None, headers=None, body_is_json=True):
    fake = mock.Mock(status_code=status, headers=headers or {})
    if body_is_json:
        fake.json.return_value = json_data if json_data is not None else {"ErrorID": 0, "Datos": ["ok"]}
    else:
        fake.json.side_effect = ValueError("no JSON")
    return fake


@mock.patch.object(client_module.time, "sleep")
class RetryPolicyTests(SimpleTestCase):
    def make_client(self, *responses):
        client = LosPreciosClient("secret-key", min_interval=0)
        client.session = mock.Mock()
        client.session.get.side_effect = list(responses)
        return client

    def test_success_returns_data(self, sleep):
        client = self.make_client(response())
        self.assertEqual(client.get_supermarkets(), ["ok"])

    def test_retries_server_errors_with_exponential_backoff(self, sleep):
        client = self.make_client(response(500), response(502), response(503), response())
        self.assertEqual(client.get_supermarkets(), ["ok"])
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2, 4])

    def test_gives_up_after_three_retries(self, sleep):
        client = self.make_client(*[response(500)] * 4)
        with self.assertRaises(LosPreciosError):
            client.get_supermarkets()
        self.assertEqual(client.session.get.call_count, 4)

    def test_retries_network_errors_and_timeouts(self, sleep):
        client = self.make_client(requests.ConnectionError("down"), requests.Timeout("slow"), response())
        self.assertEqual(client.get_supermarkets(), ["ok"])

    def test_429_waits_for_retry_after(self, sleep):
        client = self.make_client(response(429, headers={"Retry-After": "7"}), response())
        self.assertEqual(client.get_supermarkets(), ["ok"])
        self.assertEqual(sleep.call_args.args[0], 7)

    def test_429_with_too_long_retry_after_stops_without_retrying(self, sleep):
        client = self.make_client(response(429, headers={"Retry-After": "120"}), response())
        with self.assertRaisesMessage(LosPreciosError, "120s"):
            client.get_supermarkets()
        self.assertEqual(client.session.get.call_count, 1)
        sleep.assert_not_called()

    def test_other_4xx_errors_are_not_retried(self, sleep):
        client = self.make_client(response(404), response())
        with self.assertRaises(LosPreciosError) as raised:
            client.get_supermarkets()
        self.assertFalse(raised.exception.is_retryable)
        self.assertEqual(client.session.get.call_count, 1)

    def test_invalid_json_is_a_clear_non_retryable_error(self, sleep):
        client = self.make_client(response(body_is_json=False), response())
        with self.assertRaisesMessage(LosPreciosError, "not JSON"):
            client.get_supermarkets()
        self.assertEqual(client.session.get.call_count, 1)

    def test_api_rate_limit_error_id_is_retried(self, sleep):
        client = self.make_client(response(json_data={"ErrorID": 3, "Mensaje": "Solicitud muy frecuente"}), response())
        self.assertEqual(client.get_supermarkets(), ["ok"])

    def test_invalid_api_key_is_fatal_and_not_retried(self, sleep):
        client = self.make_client(response(json_data={"ErrorID": 1, "Mensaje": "Clave inválida"}), response())
        with self.assertRaises(LosPreciosError) as raised:
            client.get_supermarkets()
        self.assertTrue(raised.exception.is_fatal)
        self.assertEqual(client.session.get.call_count, 1)

    def test_api_key_is_redacted_from_network_errors(self, sleep):
        client = self.make_client(*[requests.ConnectionError("failed for ClaveAPI=secret-key")] * 4)
        with self.assertRaises(LosPreciosError) as raised:
            client.get_supermarkets()
        self.assertNotIn("secret-key", str(raised.exception))


class ParseRetryAfterTests(SimpleTestCase):
    def test_formats(self):
        self.assertEqual(parse_retry_after("5"), 5)
        self.assertIsNone(parse_retry_after(None))
        self.assertIsNone(parse_retry_after("soon"))
        self.assertEqual(parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT"), 0)
