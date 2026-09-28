from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from .agent import DealMindAgent


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

INTERACTION_1 = (
    "Ravi is interested in our software. He thinks the annual plan is expensive, "
    "prefers monthly billing, and is comparing us with Zoho."
)
INTERACTION_2 = "Prepare me for my meeting with Ravi."


def main() -> bool:
    try:
        agent = DealMindAgent()

        first = agent.process_message(INTERACTION_1)
        print("--- INTERACTION 1 ---")
        print(first["response"])

        second = agent.process_message(INTERACTION_2)
        print("\n--- INTERACTION 2 ---")
        print(second["response"])

        recalled = second["memories_used"]
        print("\n--- RECALLED MEMORY ---")
        if recalled:
            for index, memory in enumerate(recalled, start=1):
                print(f"{index}. {memory}")
        else:
            print("No memories were returned.")

        if not first["stored_facts"]:
            raise RuntimeError("The first interaction did not produce any durable customer facts to store.")
        if not recalled:
            raise RuntimeError("The second interaction did not recall any memories for Ravi.")

        recalled_text = "\n".join(recalled).lower()
        if not any(term in recalled_text for term in ("monthly", "annual", "zoho", "software")):
            raise RuntimeError("Recalled memories did not show facts from the first Ravi interaction.")

        response_text = second["response"].lower()
        if not any(term in response_text for term in ("monthly", "annual", "zoho", "interested")):
            raise RuntimeError("The meeting-prep response did not use Ravi's recalled information.")

        print("\nDEALMIND AGENT TEST PASSED")
        return True
    except Exception as exc:
        print(f"\nDEALMIND AGENT TEST FAILED: {exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
