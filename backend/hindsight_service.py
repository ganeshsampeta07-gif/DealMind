from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from .config import HINDSIGHT_API_KEY, HINDSIGHT_BANK_ID, HINDSIGHT_BASE_URL


class HindsightService:
    """Official Hindsight Cloud client using the current REST API contract."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, bank_id: Optional[str] = None):
        self.api_key = api_key or HINDSIGHT_API_KEY
        self.base_url = (base_url or HINDSIGHT_BASE_URL).rstrip("/")
        self.bank_id = bank_id or HINDSIGHT_BANK_ID or "dealmind"
        if not self.api_key:
            raise ValueError("HINDSIGHT_API_KEY is not configured.")
        if not self.base_url:
            raise ValueError("HINDSIGHT_BASE_URL is not configured.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, url: str, json_body: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None):
        try:
            response = requests.request(method=method, url=url, headers=self._headers(), json=json_body, params=params, timeout=60)
        except requests.RequestException as exc:
            raise RuntimeError(f"Hindsight network error: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}

        if response.status_code not in {200, 201, 202, 204}:
            detail = payload.get("detail") if isinstance(payload, dict) else None
            msg = detail or payload.get("message") or response.text or "Unknown Hindsight API error."
            raise RuntimeError(f"Hindsight request failed: {msg}")

        return payload

    def connect(self) -> bool:
        """Check the configured Hindsight endpoint is reachable."""
        try:
            response = requests.get(f"{self.base_url}/health", headers={"Authorization": f"Bearer {self.api_key}"}, timeout=20)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def retain_memory(
        self,
        customer: str,
        memory_type: str,
        value: str,
        source: Optional[str] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/memories"
        payload = {
            "async": False,
            "items": [
                {
                    "content": value,
                    "context": context or source or f"Customer: {customer}",
                    "document_id": f"dealmind-{customer.lower()}-{memory_type}",
                    "tags": [customer, memory_type, "dealmind"],
                    "metadata": metadata or {},
                }
            ],
        }
        return self._request("POST", endpoint, json_body=payload)

    def recall_memory(self, customer: str, query: Optional[str] = None, limit: int = 10):
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/memories/recall"
        payload = {
            "query": query or f"What do we know about {customer}?",
            "types": ["world", "experience", "observation"],
            "budget": "mid",
            "max_tokens": max(256, limit * 256),
            "tags": [customer],
        }
        return self._request("POST", endpoint, json_body=payload)

    def get_customer_memories(self, customer: str):
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/memories/list"
        params = {"q": customer, "limit": 20}
        return self._request("GET", endpoint, params=params)


hindsight_service = HindsightService()


def retain_memory(*args, **kwargs):
    return hindsight_service.retain_memory(*args, **kwargs)


def recall_memory(*args, **kwargs):
    return hindsight_service.recall_memory(*args, **kwargs)


def get_customer_memories(*args, **kwargs):
    return hindsight_service.get_customer_memories(*args, **kwargs)
