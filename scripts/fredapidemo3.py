#!/usr/bin/env python3
"""Fetch and dump raw metadata for a FRED series."""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv
from fredapi import Fred


def to_json(value) -> str:
    """Serialize FRED responses to pretty JSON."""
    return json.dumps(value, indent=2, default=str, ensure_ascii=False)


def main(series_id: str) -> None:
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY environment variable is required.")

    fred = Fred(api_key=api_key)

    print(f"=== Series info for {series_id} ===")
    info = fred.get_series_info(series_id)
    print(to_json(info))

    print(f"\n=== Series sources for {series_id} ===")
    try:
        sources = fred.get_series_sources(series_id)
        print(to_json(sources))
    except Exception as exc:  # pragma: no cover - depends on series
        print(f"Could not fetch sources: {exc}")

    print(f"\n=== Series release for {series_id} ===")
    try:
        release = fred.get_series_release(series_id)
        print(to_json(release))
    except Exception as exc:  # pragma: no cover
        print(f"Could not fetch release: {exc}")

    print(f"\n=== Series categories for {series_id} ===")
    try:
        categories = fred.get_series_categories(series_id)
        print(to_json(categories))
    except Exception as exc:  # pragma: no cover
        print(f"Could not fetch categories: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series_id", help="FRED series identifier (e.g., GDP, CPIAUCSL)")
    args = parser.parse_args()
    main(args.series_id)
