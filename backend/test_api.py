from __future__ import annotations

import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

from .main import app


client = TestClient(app)


def main() -> bool:
    try:
        health_response = client.get("/health")
        assert health_response.status_code == 200, health_response.text
        assert health_response.json() == {"status": "ok", "service": "DealMind"}

        agent_result = {
            "response": "Discuss Ravi's monthly billing preference and address the annual-plan cost concern.",
            "memories_used": [
                "Ravi prefers monthly billing.",
                "Ravi considers the annual plan expensive.",
            ],
            "memory_count": 2,
            "customer": "Ravi",
            "stored_facts": [],
        }
        with patch("backend.main.agent.process_message", return_value=agent_result) as process_message:
            chat_response = client.post(
                "/chat",
                json={"message": "Prepare me for my meeting with Ravi."},
            )

        assert chat_response.status_code == 200, chat_response.text
        result = chat_response.json()
        assert result["response"], "Expected a generated response."
        assert result["memories"] == agent_result["memories_used"]
        process_message.assert_called_once_with("Prepare me for my meeting with Ravi.", None)

        print("API TEST PASSED")
        print("/health is healthy; /chat returns an agent response and recalled memories.")
        return True
    except Exception as exc:
        print(f"API TEST FAILED: {exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
