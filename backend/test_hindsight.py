from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from backend.hindsight_service import HindsightService


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def print_memory_section(title: str, memories):
    print(f"\n{title}")
    if not memories:
        print("No memories returned.")
        return

    for index, memory in enumerate(memories, start=1):
        if isinstance(memory, dict):
            content = memory.get("content") or memory.get("value") or memory.get("summary") or memory.get("text") or str(memory)
            score = memory.get("score")
            print(f"{index}. {content}")
            if score is not None:
                print(f"   Score: {score}")
        else:
            print(f"{index}. {memory}")


def main() -> None:
    try:
        api_key = os.getenv("HINDSIGHT_API_KEY", "")
        base_url = os.getenv("HINDSIGHT_BASE_URL", "")
        bank_id = os.getenv("HINDSIGHT_BANK_ID", "dealmind")

        if not api_key:
            raise ValueError("HINDSIGHT_API_KEY is missing from the .env file.")
        if not base_url:
            raise ValueError("HINDSIGHT_BASE_URL is missing from the .env file.")

        service = HindsightService(api_key=api_key, base_url=base_url, bank_id=bank_id)

        if not service.connect():
            raise RuntimeError("Hindsight health check failed. Check HINDSIGHT_BASE_URL and the API key.")

        print(f"Connected to Hindsight bank: {bank_id}")

        facts = [
            ("Ravi", "interest", "Ravi is interested in our software."),
            ("Ravi", "pricing_concern", "Ravi thinks the annual plan is expensive."),
            ("Ravi", "preference", "Ravi prefers monthly billing."),
            ("Ravi", "competitor", "Ravi is comparing our product with Zoho."),
        ]

        for customer, memory_type, value in facts:
            result = service.retain_memory(
                customer=customer,
                memory_type=memory_type,
                value=value,
                source="demo_seed",
                context="sales discovery",
                metadata={"bank_id": bank_id, "customer": customer},
            )
            print(f"Stored: {value}")
            print(f"Retain response: {result}")

        query = "What do we know about Ravi's preferences, pricing concerns, interests, and competitors?"
        recall_result = service.recall_memory(customer="Ravi", query=query, limit=10)

        items = recall_result.get("results", []) if isinstance(recall_result, dict) else recall_result
        print_memory_section("RECALLED MEMORIES", items)

        if isinstance(recall_result, dict) and recall_result.get("results") is not None:
            print("\nHINDSIGHT TEST PASSED")
        else:
            raise RuntimeError("Recall did not return a valid results array.")

    except Exception as exc:  # pragma: no cover - debugging output only; secrets are not exposed
        print(f"HINDSIGHT TEST FAILED: {exc}")


if __name__ == "__main__":
    main()
