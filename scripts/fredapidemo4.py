#!/usr/bin/env python3
"""Fetch a FRED-generated chart image for a series (no matplotlib)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv


def build_chart_url(series_id: str, **params: str) -> str:
    """Construct the fredgraph.png URL for a series."""
    base = "https://fred.stlouisfed.org/graph/fredgraph.png"
    query = {"id": series_id, **params}
    return f"{base}?{urlencode(query)}"


def download_chart(series_id: str, out_path: Path, **params: str) -> Path:
    """Download the chart PNG to disk."""
    url = build_chart_url(series_id, **params)
    with urlopen(url) as response:  # noqa: S310 - simple script for manual use
        data = response.read()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return out_path


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series_id", help="FRED series identifier (e.g. GDP)")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output file path (defaults to ./fred_charts/<series>.png)",
    )
    parser.add_argument(
        "--width",
        type=str,
        default="670",
        help="Chart width in pixels (default: 670)",
    )
    parser.add_argument(
        "--height",
        type=str,
        default="445",
        help="Chart height in pixels (default: 445)",
    )
    parser.add_argument(
        "--cosd",
        type=str,
        default="",
        help="Chart start date (e.g. 2010-01-01). Optional.",
    )
    parser.add_argument(
        "--coed",
        type=str,
        default="",
        help="Chart end date. Optional.",
    )
    args = parser.parse_args()

    params = {
        "width": args.width,
        "height": args.height,
    }
    if args.cosd:
        params["cosd"] = args.cosd
    if args.coed:
        params["coed"] = args.coed

    output_path = (
        Path(args.out)
        if args.out
        else Path("fred_charts") / f"{args.series_id}.png"
    )
    saved = download_chart(args.series_id, output_path, **params)
    print(f"Saved chart to {saved}")
    print(f"Source URL: {build_chart_url(args.series_id, **params)}")


if __name__ == "__main__":
    main()
