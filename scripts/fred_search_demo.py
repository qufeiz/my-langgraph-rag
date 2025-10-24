#!/usr/bin/env python3
"""Quick demos for the three FRED search endpoints."""

from __future__ import annotations

import os
import inspect
import json
from pathlib import Path

from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()


def require_api_key() -> str:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")
    return api_key


def normalize(df):
    return df.head(5).fillna("").to_dict(orient="records")


def demo_search(fred: Fred, query: str) -> None:
    print(f"\n🔎 Fred.search('{query}') → top 5 results")
    print(json.dumps(normalize(fred.search(query, limit=5)), indent=2, default=str))


def demo_search_by_category(fred: Fred, category_id: int) -> None:
    print(
        "\n📚 search_by_category(category_id, limit=5) → first results "
        f"(category_id={category_id}; this endpoint does not take a search text parameter)"
    )
    print(
        json.dumps(
            normalize(fred.search_by_category(category_id, limit=5)),
            indent=2,
            default=str,
        )
    )


def demo_search_by_release(fred: Fred, release_id: int) -> None:
    print(
        "\n📰 search_by_release(release_id, limit=5) → first results "
        f"(release_id={release_id}; this endpoint does not take a search text parameter)"
    )
    print(
        json.dumps(
            normalize(fred.search_by_release(release_id, limit=5)),
            indent=2,
            default=str,
        )
    )


def main() -> None:
    api_key = require_api_key()
    fred = Fred(api_key=api_key)
    output_path = Path("fred_search_demo_results.jsonl")
    output_path.unlink(missing_ok=True)

    print(
        "\nMethod signatures:"
        f"\n  search{inspect.signature(Fred.search)}"
        #f"\n  search_by_category{inspect.signature(Fred.search_by_category)}"
        f"\n  search_by_release{inspect.signature(Fred.search_by_release)}"
    )

    payload: dict[str, dict[str, object] | list[dict[str, object]] | str] = {}

    def capture(name: str, func) -> None:
        try:
            payload[name] = {
                "results": normalize(func()),
            }
        except Exception as exc:  # noqa: BLE001
            payload[name] = {"error": str(exc)}

    capture("search", lambda: fred.search("H.4.1", limit=5))
    #capture("search_by_category", lambda: fred.search_by_category(9, limit=5))
    capture("search_by_release", lambda: fred.search_by_release(20, limit=5))

    output_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nSaved full output to {output_path.resolve()}")

    for name, value in payload.items():
        print(f"\n=== {name} ===")
        print(json.dumps(value, indent=2, default=str))


if __name__ == "__main__":
    main()
