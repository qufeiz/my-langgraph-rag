#!/usr/bin/env python3
"""Quick demo for inspecting a FRED series' source metadata.

Fetches the series info for the specified series ID, extracts its source,
and then looks up the source details with the FRED sources endpoint.
"""

from __future__ import annotations

import os
from pprint import pprint

from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

SERIES_ID = "A939RX0Q048SBEA"


def main() -> None:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Please set FRED_API_KEY in your environment.")

    fred = Fred(api_key=api_key)
    series_info = fred.get_series_info(SERIES_ID)
    print(f"Series metadata for {SERIES_ID}:")
    pprint(series_info)

    source_id = series_info.get("source_id")
    if source_id is None:
        print("No source_id was returned for this series.")
        return

    source = fred.get_source(source_id)
    print(f"\nSource metadata (source_id={source_id}):")
    pprint(source)


if __name__ == "__main__":
    main()
