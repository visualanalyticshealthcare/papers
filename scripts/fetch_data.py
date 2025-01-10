#!/usr/bin/env python3
"""
fetch_data.py

Fetches research article metadata from Europe PMC for a given date range.
- Reads QUERY_KEYWORDS from EPMC_QUERY_KEYWORDS environment variable.
- Accepts --end_date and --days_back as CLI arguments.

Usage:
  python fetch_data.py [--end_date YYYY-MM-DD] [--days_back N]

Example:
  python fetch_data.py --days_back 14
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE_SIZE = 1000  # Max allowed by Europe PMC


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Europe PMC data.")
    parser.add_argument(
        "--end_date",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD). Defaults to today's date if not provided.",
    )
    parser.add_argument(
        "--days_back",
        type=int,
        default=7,
        help="Number of days before end_date to start searching (default: 7).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Retrieve the query from the environment
    # If not set, fall back to a minimal query or raise an error
    query_keywords = os.environ.get("EPMC_QUERY_KEYWORDS")
    if not query_keywords:
        raise ValueError("Environment variable EPMC_QUERY_KEYWORDS is not set.")

    # Compute date range
    if args.end_date:
        try:
            end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid end_date format: {args.end_date}")
    else:
        end_date = datetime.date.today()

    start_date = end_date - datetime.timedelta(days=args.days_back)

    # Construct final query with date filter
    query = f"{query_keywords} AND E_PDATE:[{start_date} TO {end_date}]"
    print(f"Fetching from {start_date} to {end_date} with query:\n{query}\n")

    cursor_mark = "*"
    all_results = []

    while True:
        params = {
            "query": query,
            "format": "json",
            "resultType": "core",
            "cursorMark": cursor_mark,
            "pageSize": PAGE_SIZE,
        }

        resp = requests.get(EUROPE_PMC_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("resultList", {}).get("result", [])
        all_results.extend(results)

        next_cursor = data.get("nextCursorMark")
        if not next_cursor or next_cursor == cursor_mark:
            break
        cursor_mark = next_cursor

    print(f"Total articles fetched: {len(all_results)}")

    # Save results
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"epmc_{start_date}_to_{end_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "records_fetched": len(all_results),
                "articles": all_results,
            },
            f,
            indent=2,
        )

    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
