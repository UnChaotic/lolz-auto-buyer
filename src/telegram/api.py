import json
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class TelegramAPI:
    API_URL: str = "https://api.telegram.org/bot"

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.API_URL += self.bot_token
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
        response = self.client.request(
            method=request_method,
            url=f"{self.API_URL}/{method}",
            data=data,
        )
        response.raise_for_status()
        return response.json()

    def send_message(self, text: str, chat_id: int, **kwargs) -> dict:
        response = self.api_request(
            "sendMessage",
            {"text": text, "chat_id": chat_id, **kwargs},
        )
        return response
