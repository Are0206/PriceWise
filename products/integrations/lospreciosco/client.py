import logging
import time
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://losprecios.co"

class LosPreciosError(Exception):
    FATAL_IDS = {1, 12}      # invalid or disabled API key: stop the whole run
    RETRYABLE_IDS = {2, 3}   # server error, too many requests: retry later

    def __init__(self, message, error_id=None):
        super().__init__(message)
        self.error_id = error_id

    @property
    def is_fatal(self):
        return self.error_id in self.FATAL_IDS

    @property
    def is_retryable(self):
        # error_id=None means a network or parsing failure, which is retryable
        return self.error_id in self.RETRYABLE_IDS or self.error_id is None

#RF-
class LosPreciosClient:
    def __init__(self, api_key, min_interval=1.1, timeout=20, max_retries=3):
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

        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                response_json = response.json()
            except (requests.RequestException, ValueError) as exc:
                error = LosPreciosError(f"Network or parsing error: {exc}")
            else:
                error_id = response_json.get("ErrorID", 0)
                if error_id == 0:
                    return response_json.get("Datos")
                error = LosPreciosError(
                    response_json.get("Mensaje") or f"API error {error_id}",
                    error_id,
                )

            if not error.is_retryable or attempt == self.max_retries:
                raise error
            delay = 2 ** attempt
            logger.warning("%s (attempt %d), retrying in %ds", error, attempt + 1, delay)
            time.sleep(delay)


    def get_supermarkets(self, municipio_id=2):
        return self._get("tienda/lista", MunicipioID=municipio_id)
    
    def get_supermarket_details(self, id=None, municipio_id=2):
        return self._get("tienda/detalles", ID=id, MunicipioID=municipio_id)
    
    def get_product_details(self, id=None, municipio_id=2):
        return self._get("item/detalles", ID=id, MunicipioID=municipio_id)