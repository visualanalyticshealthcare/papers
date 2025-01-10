#!/usr/bin/env python3

"""
generate_aggregate_html.py

Generates aggregate HTML pages that combine articles from multiple CSV files.
- Users can filter articles by time range (week/month/year)
- Users can adjust keyword weights in the browser
- Rankings are recalculated dynamically with JavaScript
- Articles link to their DOIs, opening in a new tab

Usage:
  python generate_aggregate_html.py --input_dir data/weekly_reports --output_html docs/aggregate.html
"""

import argparse
import csv
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_env_keywords():
    """Load keyword weights from environment variables."""
    weights_str = os.environ.get("EPMC_KEYWORD_WEIGHTS", "{}")
    try:
        return json.loads(weights_str)
    except json.JSONDecodeError:
        return {}


def parse_date_from_filename(filename):
    """Extract start and end dates from filename."""
    # Expected format: epmc_YYYY-MM-DD_to_YYYY-MM-DD.csv
    parts = filename.stem.replace("epmc_", "").split("_to_")
    if len(parts) == 2:
        start_date = datetime.strptime(parts[0], "%Y-%m-%d")
        end_date = datetime.strptime(parts[1], "%Y-%m-%d")
        return start_date, end_date
    return None, None


def combine_csv_files(input_dir):
    """Combine all CSV files in the directory, adding date information."""
    input_path = Path(input_dir)
    csv_files = sorted(input_path.glob("epmc_*.csv"))

    all_articles = []
    date_ranges = set()

    for csv_file in csv_files:
        start_date, end_date = parse_date_from_filename(csv_file)
        if not start_date or not end_date:
            continue

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["fetch_start_date"] = start_date.strftime("%Y-%m-%d")
                row["fetch_end_date"] = end_date.strftime("%Y-%m-%d")
                all_articles.append(row)

        date_ranges.add(
            (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        )

    return all_articles, sorted(date_ranges)


def generate_aggregate_html(input_dir, output_html):
    """Generate an aggregate HTML page from all CSV files."""
    articles, date_ranges = combine_csv_files(input_dir)
    initial_weights = load_env_keywords()

    # Get overall date range
    if date_ranges:
        overall_start = min(start for start, _ in date_ranges)
        overall_end = max(end for _, end in date_ranges)
        date_range_str = f"{overall_start} to {overall_end}"
    else:
        date_range_str = "No date range available"

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Analytics in Healthcare - Aggregate Report</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .filter-section {{
            margin: 20px 0;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }}
        .date-filter {{
            display: flex;
            gap: 20px;
            align-items: center;
            margin-bottom: 15px;
        }}
        .date-filter label {{
            min-width: 100px;
        }}
        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .filter-buttons button {{
            padding: 5px 15px;
            border: 1px solid #ddd;
            border-radius: 3px;
            background-color: white;
            cursor: pointer;
        }}
        .filter-buttons button:hover {{
            background-color: #f0f0f0;
        }}
        .filter-buttons button.active {{
            background-color: #007bff;
            color: white;
            border-color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1><a href="index.html">Visual Analytics in Healthcare Research</a></h1>
        <p>Aggregate report for articles from {date_range_str}</p>
        
        <div class="filter-section">
            <h2>Time Filter</h2>
            <div class="filter-buttons">
                <button onclick="setTimeFilter('week')">Last 7 Days</button>
                <button onclick="setTimeFilter('thisMonth')">{datetime.now().strftime('%B')}</button>
                <button onclick="setTimeFilter('lastMonth')">{(datetime.now().replace(day=1) - timedelta(days=1)).strftime('%B')}</button>
                <button onclick="setTimeFilter('thisYear')">This Year ({datetime.now().year})</button>
                <button onclick="setTimeFilter('lastYear')">Last Year ({datetime.now().year - 1})</button>
                <button onclick="setTimeFilter('all')" class="active">All Time</button>
            </div>
            <div class="date-filter">
                <label for="startDate">Custom Range:</label>
                <input type="date" id="startDate" onchange="updateDateFilter()">
                <label for="endDate">to</label>
                <input type="date" id="endDate" onchange="updateDateFilter()">
            </div>
            <p id="articleCount">Showing all articles</p>
        </div>
        
        <div class="weights-section">
            <h2>Keyword Weights</h2>
            <p>Adjust weights to recalculate article rankings. Matches are found in:</p>
            <ul>
                <li>Keywords (full weight)</li>
                <li>Title (80% weight)</li>
                <li>Abstract (50% weight)</li>
            </ul>
            <div class="weights-grid" id="weights">
                <!-- Weights will be injected here -->
            </div>
        </div>

        <table id="article-table">
            <thead>
                <tr>
                    <th class="sortable" data-sort="rank">Rank</th>
                    <th class="sortable" data-sort="score">Score</th>
                    <th class="sortable title-abstract" data-sort="title">Title & Abstract</th>
                    <th class="sortable authors" data-sort="authors">Authors & Affiliation</th>
                    <th class="sortable journal" data-sort="journal">Journal</th>
                    <th class="sortable date" data-sort="date">Date</th>
                    <th class="sortable api-keywords" data-sort="api_keywords">API Keywords</th>
                    <th class="sortable keywords" data-sort="keywords">Matched Keywords</th>
                </tr>
            </thead>
            <tbody>
                <!-- Articles will be injected here -->
            </tbody>
        </table>
    </div>

    <script>
        // Initial data and global variables
        window.articles = {json.dumps(articles)};
        window.initialWeights = {json.dumps(initial_weights)};
        window.currentSort = {{ field: 'score', direction: 'desc' }};
        window.currentTimeFilter = 'all';
        window.filteredArticles = [...window.articles];
    </script>
    <script src="script.js"></script>
    <script>
        // Initialize the page after loading script.js
        initializePage(window.articles, window.initialWeights, true);
    </script>
</body>
</html>
"""

    # Create output directory if it doesn't exist
    output_path = Path(output_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the HTML to the output file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Aggregate HTML file generated: {output_html}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate an aggregate HTML page from multiple CSV files."
    )
    parser.add_argument(
        "--input_dir",
        default="data/weekly_reports",
        help="Directory containing CSV files to process",
    )
    parser.add_argument(
        "--output_html",
        default="docs/aggregate.html",
        help="Path to the output HTML file",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")

    generate_aggregate_html(args.input_dir, args.output_html)


if __name__ == "__main__":
    main()
