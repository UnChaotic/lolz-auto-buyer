import json
import logging
import time
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .errors import MarketBuyError

logger = logging.getLogger(__name__)


class BaseMarketAPI:
    API_URL: str = "https://api.lzt.market/"
    # Lolzteam API for market have a limit of 1 requests per 3 second
    delay: int = 3

    def __init__(self, token: str, headers: Optional[dict] = None):
        self.token = token
        self.headers = headers or {}
        self.headers.setdefault("Authorization", f"Bearer {self.token}")
        self.client = httpx.Client(
            http2=True,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    def __del__(self):
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def api_request(
        self,
        method: str,
        data: Optional[dict] = None,
        request_method: str = "GET",
    ) -> dict:
        time.sleep(self.delay)  # Respect API rate limit
        
        try:
            response = self.client.request(
                method=request_method,
                url=self.API_URL + method,
                data=data,
                headers=self.headers,
            )
            response.raise_for_status()
            
            response_data = response.json()
            is_error = response_data.get("error")
            if is_error:
                raise MarketBuyError(response_data["error_description"])
            return response_data

        except httpx.HTTPError as http_error:
            error_response = http_error.response.text if http_error.response else str(http_error)
            logger.warning("Received error: %s", error_response)
            try:
                error_data = json.loads(error_response)
                error_message = error_data.get("errors", ["Received unknown error"])[0]
            except json.JSONDecodeError:
                error_message = "Received unknown error"
            raise MarketBuyError(error_message)
