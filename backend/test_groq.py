from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from groq import Groq


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def main() -> None:
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing from the .env file.")
        if not model:
            raise ValueError("GROQ_MODEL is missing from the .env file.")

        client = Groq(api_key=api_key)
        prompt = "Explain in one sentence why remembering customer preferences is useful for a sales assistant."

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        response = completion.choices[0].message.content
        print(response)
        print("\nGROQ TEST PASSED")

    except Exception as exc:
        print(f"GROQ TEST FAILED: {exc}")


if __name__ == "__main__":
    main()
