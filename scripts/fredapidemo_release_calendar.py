#!/usr/bin/env python3
"""Demo pulling the release calendar for a specific release ID/year from FRED."""

from __future__ import annotations

import os
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()

RELEASE_ID = 50  # Gross Domestic Product
YEAR = 2025


def main() -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")

    params = {
        "api_key": api_key,
        "file_type": "json",
        "release_id": RELEASE_ID,
        "year": YEAR,
        "include_release_dates_with_no_data": "true",
    }
    response = requests.get(
        "https://api.stlouisfed.org/fred/release/dates", params=params, timeout=10
    )
    response.raise_for_status()
    data = response.json()
    print(f"Release dates for release_id={RELEASE_ID} in {YEAR}:")
    pprint(data)


if __name__ == "__main__":
    main()
