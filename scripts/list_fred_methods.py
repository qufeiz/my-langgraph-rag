#!/usr/bin/env python3
"""Print available fredapi.Fred helper methods (avoids surprises)."""

from __future__ import annotations

import inspect

from fredapi import Fred


def main() -> None:
    methods = [
        name
        for name, member in inspect.getmembers(Fred, predicate=callable)
        if not name.startswith("_")
    ]
    for name in sorted(methods):
        print(name)


if __name__ == "__main__":
    main()
