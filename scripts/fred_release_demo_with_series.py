#!/usr/bin/env python3
"""Demo: give me a series_id (e.g. UNRATE) → I fetch its release calendar automatically."""

from __future__ import annotations

import os
from pprint import pprint

import requests
from dotenv import load_dotenv

load_dotenv()

SERIES_ID = "GDP"  # try CPIAUCSL, GDPC1, CPILFESL, DGS10, etc.


def get_release_from_series(series_id: str, api_key: str) -> dict:
    """Call official fred/series/release endpoint"""
    resp = requests.get(
        "https://api.stlouisfed.org/fred/series/release",
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    releases = data.get("releases", [])
    if not releases:
        raise RuntimeError(f"No release found for series_id={series_id}")
    return releases[0]  # first is enough — there's usually only 1


def main() -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")

    # 1) resolve series → release metadata
    release_meta = get_release_from_series(SERIES_ID, api_key)
    release_id = release_meta["id"]
    release_name = release_meta["name"]
    print(f"\n✅ {SERIES_ID} belongs to release_id={release_id}  ({release_name})")

    # 2) now query official release calendar
    resp = requests.get(
        "https://api.stlouisfed.org/fred/release/dates",
        params={
            "api_key": api_key,
            "file_type": "json",
            "release_id": release_id,
            "include_release_dates_with_no_data": "true",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    dates = data.get("release_dates", [])
    if not dates:
        print("No release dates returned.")
        return

    # 3) auto-pick latest available year
    years = [
        int(item["date"][:4])
        for item in dates
        if isinstance(item.get("date"), str) and item["date"][:4].isdigit()
    ]
    latest_year = max(years)
    filtered = [d for d in dates if d["date"].startswith(str(latest_year))]

    print(f"\n📅 Release dates for {SERIES_ID} ({release_name}) in {latest_year}:")
    pprint(filtered)


if __name__ == "__main__":
    main()