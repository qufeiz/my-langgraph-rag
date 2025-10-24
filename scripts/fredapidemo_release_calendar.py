#!/usr/bin/env python3
"""Demo pulling the release calendar for a specific release ID/year from FRED."""

from __future__ import annotations

import os
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()

RELEASE_ID = 50  # Gross Domestic Product


def main() -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")

    params = {
        "api_key": api_key,
        "file_type": "json",
        "release_id": RELEASE_ID,
        "include_release_dates_with_no_data": "true",
    }

    response = requests.get(
        "https://api.stlouisfed.org/fred/release/dates", params=params, timeout=10
    )
    response.raise_for_status()
    data = response.json()
    dates = data.get("release_dates", [])
    if not dates:
        print("No release dates returned.")
        return

    year_candidates = [
        int(item["date"][:4])
        for item in dates
        if isinstance(item.get("date"), str) and item["date"][:4].isdigit()
    ]
    if not year_candidates:
        print("No valid release dates returned.")
        pprint(data)
        return

    latest_year = max(year_candidates)

    filtered_dates = [
        item
        for item in dates
        if isinstance(item.get("date"), str) and item["date"].startswith(str(latest_year))
    ]

    print(f"Release dates for release_id={RELEASE_ID} in {latest_year}:")
    pprint(filtered_dates)


if __name__ == "__main__":
    main()
