import time

import requests
from requests import RequestException

DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 30
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS = 1
DEFAULT_STATUS_RETRY_CODES = {408, 429, 500, 502, 503, 504}


def post_with_retries(url, data, timeout=None, max_attempts=DEFAULT_MAX_ATTEMPTS, backoff_seconds=DEFAULT_BACKOFF_SECONDS, retry_status_codes=None):
    timeout = timeout or (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
    retry_status_codes = retry_status_codes or DEFAULT_STATUS_RETRY_CODES
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, data, timeout=timeout)
            if response.status_code not in retry_status_codes or attempt == max_attempts:
                return response
            last_error = requests.HTTPError(f"Retryable HTTP status: {response.status_code}", response=response)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
            if attempt == max_attempts:
                raise
        except RequestException:
            raise

        time.sleep(backoff_seconds * (2 ** (attempt - 1)))

    if last_error:
        raise last_error
