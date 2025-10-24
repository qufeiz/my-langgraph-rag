#!/usr/bin/env python3
"""Demonstrate release series counts and table structure from the FRED API."""

from __future__ import annotations

import argparse
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def require_api_key() -> str:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")
    return api_key


def get_release_id_by_name(api_key: str, name_query: str) -> int | None:
    """Return first release_id whose name contains the query (case-insensitive)."""
    response = requests.get(
        "https://api.stlouisfed.org/fred/releases",
        params={
            "api_key": api_key,
            "file_type": "json",
            "limit": 1000,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    for release in data.get("releases", []):
        if name_query.lower() in release.get("name", "").lower():
            return int(release["id"])
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-name",
        default=os.getenv("FRED_RELEASE_NAME", "H.4.1"),
        help="Release name to search (default: H.4.1).",
    )
    args = parser.parse_args()

    api_key = require_api_key()
    release_name = args.release_name or "H.4.1"

    release_id = get_release_id_by_name(api_key, release_name)
    if release_id is None:
        raise RuntimeError(f"Could not find a release matching '{release_name}'.")

    series_resp = requests.get(
        "https://api.stlouisfed.org/fred/release/series",
        params={
            "api_key": api_key,
            "file_type": "json",
            "release_id": release_id,
            "limit": 1,
        },
        timeout=10,
    )
    series_resp.raise_for_status()
    series_payload = series_resp.json()

    print(f"Target release: {release_name} (release_id={release_id})")
    print("\n=== RELEASE SERIES (count + metadata) ===")
    print(json.dumps(series_payload, indent=2))

    tables_resp = requests.get(
        "https://api.stlouisfed.org/fred/release/tables",
        params={
            "api_key": api_key,
            "file_type": "json",
            "release_id": release_id,
        },
        timeout=10,
    )
    tables_resp.raise_for_status()
    tables_payload = tables_resp.json()

    print("\n=== RELEASE TABLES ===")
    print(json.dumps(tables_payload, indent=2))


if __name__ == "__main__":
    main()
