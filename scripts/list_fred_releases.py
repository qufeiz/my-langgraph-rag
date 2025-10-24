#!/usr/bin/env python3
"""Fetch all FRED releases (official API, NOT scraping)."""

import os
import requests
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")

    params = {
        "api_key": api_key,
        "file_type": "json",      # get JSON instead of XML
        "limit": 10,            # max allowed per docs
        "offset": 0,              # start at beginning
        "order_by": "release_id", # default anyway — but explicit is good
        "sort_order": "asc",      # ascending ordering
    }

    response = requests.get(
        "https://api.stlouisfed.org/fred/releases",
        params=params,
        timeout=10,
    )
    response.raise_for_status()  # fail loudly on error
    data = response.json()

    print("✅ All available FRED releases:")
    pprint(data)

if __name__ == "__main__":
    main()