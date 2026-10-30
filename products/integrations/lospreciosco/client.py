import logging
import time
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://losprecios.co"

# Longest wait the client accepts from a Retry-After header before giving up.
MAX_RETRY_WAIT = 30


class LosPreciosError(Exception):
    FATAL_IDS = {1, 12}      # invalid or disabled API key: stop the whole run
    RETRYABLE_IDS = {2, 3}   # server error, too many requests: retry later

    def __init__(self, message, error_id=None, retryable=None, retry_after=None):
        super().__init__(message)
        self.error_id = error_id
        self._retryable = retryable
        self.retry_after = retry_after

    @property
    def is_fatal(self):
        return self.error_id in self.FATAL_IDS

    @property
    def is_retryable(self):
        if self._retryable is not None:
            return self._retryable
        return self.error_id in self.RETRYABLE_IDS


def parse_retry_after(value):
    """Seconds from a Retry-After header (delta-seconds or HTTP date); None if absent or unreadable."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return int(value)
    try:
        from email.utils import parsedate_to_datetime
        from datetime import datetime, timezone
        return max(0, int((parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()))
    except (TypeError, ValueError):
        return None


#RF-38: Get Products and prices from API
class LosPreciosClient:
    def __init__(self, api_key, min_interval=1.5, timeout=20, max_retries=3):
        if not api_key:
            raise LosPreciosError("Missing Los Precios API key.", error_id=1)
        self.api_key = api_key
        self.min_interval = min_interval  # API limit: 1 request per second
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._last_request = 0.0

    def _throttle(self):
        wait = self.min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _get(self, path, **params):
        #gets data from the API
        params = {key: value for key, value in params.items() if value is not None}
        params["ClaveAPI"] = self.api_key
        url = f"{BASE_URL}/{path}"

        # Only GET requests are made, so repeating one is safe.
        for attempt in range(self.max_retries + 1):
            self._throttle()
            result = self._request(url, params)
            if not isinstance(result, LosPreciosError):
                return result
            error = result

            if not error.is_retryable or attempt == self.max_retries:
                raise error
            delay = 2 ** attempt  # 1, 2, 4 s
            if error.retry_after is not None:
                if error.retry_after > MAX_RETRY_WAIT:
                    logger.warning("Los Precios asked to wait %ss (more than %ss); giving up.",
                                   error.retry_after, MAX_RETRY_WAIT)
                    raise LosPreciosError(
                        f"Rate limited: the API asked to wait {error.retry_after}s, "
                        f"more than the {MAX_RETRY_WAIT}s limit.", retryable=False)
                delay = max(delay, error.retry_after)
            logger.warning("%s (attempt %d), retrying in %ds", error, attempt + 1, delay)
            time.sleep(delay)

    def _request(self, url, params):
        """One GET. Returns the API data, or a LosPreciosError that says whether to retry."""
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except (requests.Timeout, requests.ConnectionError) as exc:
            return LosPreciosError(f"Network error: {self._redact(exc)}", retryable=True)
        except requests.RequestException as exc:
            return LosPreciosError(f"Request error: {self._redact(exc)}", retryable=False)

        status = response.status_code
        if status == 429 or status >= 500:
            return LosPreciosError(f"HTTP {status} from Los Precios", retryable=True,
                                   retry_after=parse_retry_after(response.headers.get("Retry-After")))
        if status >= 400:
            return LosPreciosError(f"HTTP {status} from Los Precios", retryable=False)

        try:
            response_json = response.json()
        except ValueError:
            return LosPreciosError("Invalid response from Los Precios: the body is not JSON.", retryable=False)
        if not isinstance(response_json, dict):
            return LosPreciosError("Invalid response from Los Precios: unexpected JSON shape.", retryable=False)

        error_id = response_json.get("ErrorID", 0)
        if error_id == 0:
            return response_json.get("Datos")
        return LosPreciosError(response_json.get("Mensaje") or f"API error {error_id}", error_id)

    def _redact(self, exc):
        return str(exc).replace(self.api_key, "***")

    def get_supermarkets(self, municipio_id=2):
        return self._get("tienda/lista", MunicipioID=municipio_id)

    def get_supermarket_category_page(self, id=None, municipio_id=2, category=None, subcategory=None, page=None):
        return self._get(
            "tienda/detalles",
            ID=id,
            MunicipioID=municipio_id,
            Categoría=category,
            Subcategoría=subcategory,
            Página=page,
        )

    def get_supermarkets_details(self, id=None, municipio_id=2, category=None, subcategory=None, page=None):
        return self.get_supermarket_category_page(
            id=id,
            municipio_id=municipio_id,
            category=category,
            subcategory=subcategory,
            page=page,
        )
    
    def get_product_details(self, id=None, ean13=None, municipio_id=2):
        return self._get(
            "ítem/detalles",
            ID=id,
            CódigoEAN13=ean13,
            MunicipioID=municipio_id,
        )