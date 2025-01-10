#!/usr/bin/env python3

"""
generate_html.py

Generates interactive HTML pages from parsed CSV files.
- Users can adjust keyword weights in the browser.
- Rankings are recalculated dynamically with JavaScript.
- Articles link to their DOIs, opening in a new tab.

Usage:
  python generate_html.py --input_csv data/weekly_reports/parsed_articles.csv --output_html docs/output.html
  python generate_html.py --input_dir data/weekly_reports  # Process all CSV files in directory
"""

import argparse
import csv
import json
import os
import shutil
from pathlib import Path
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


def generate_html(input_csv, output_html):
    # Read the CSV file
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        articles = [row for row in reader]

    # Get initial weights from environment
    initial_weights = load_env_keywords()

    # Extract date range from filename
    input_path = Path(input_csv)
    date_range = input_path.stem.replace("epmc_", "").replace("_articles", "")

    # Calculate relative path to script.js
    output_path = Path(output_html)
    script_path = Path("..") / "script.js"

    # HTML Template
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Analytics in Healthcare - {date_range}</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <div class="container">
        <h1><a href="../index.html">Visual Analytics in Healthcare Research</a></h1>
        <p>Articles from {date_range}</p>
        
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
        // Initial data
        const articles = {json.dumps(articles)};
        const initialWeights = {json.dumps(initial_weights)};
        let currentSort = {{ field: 'score', direction: 'desc' }};
    </script>
    <script src="{script_path}"></script>
    <script>
        // Initialize the page after loading script.js
        initializePage(articles, initialWeights, false);
    </script>
</body>
</html>
"""

    # Create output directory if it doesn't exist
    output_path = Path(output_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure styles.css exists in the output directory
    styles_path = Path(__file__).parent.parent / "docs" / "styles.css"
    if not styles_path.exists():
        raise FileNotFoundError(f"CSS file not found: {styles_path}")

    # Copy styles.css to output directory if it's not already there
    output_styles = output_path.parent / "styles.css"
    if not output_styles.exists():
        shutil.copy2(styles_path, output_styles)

    # Write the HTML to the output file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"HTML file generated: {output_html}")


def process_directory(input_dir, output_dir):
    """Process all CSV files in a directory."""
    input_path = Path(input_dir)
    csv_files = sorted(input_path.glob("epmc_*.csv"))

    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return

    # Create weekly_reports subdirectory
    weekly_reports_dir = Path(output_dir) / "weekly_reports"
    weekly_reports_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in csv_files:
        output_html = weekly_reports_dir / f"{csv_file.stem}.html"
        generate_html(csv_file, output_html)


def main():
    parser = argparse.ArgumentParser(
        description="Generate interactive HTML pages from parsed CSV files."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input_csv",
        help="Path to a single CSV file to process",
    )
    group.add_argument(
        "--input_dir",
        help="Directory containing CSV files to process",
    )
    parser.add_argument(
        "--output_html",
        help="Path to output HTML file (required with --input_csv)",
    )
    parser.add_argument(
        "--output_dir",
        default="docs",
        help="Directory for output HTML files (used with --input_dir)",
    )
    args = parser.parse_args()

    if args.input_csv:
        if not args.output_html:
            parser.error("--output_html is required when using --input_csv")
        if not os.path.exists(args.input_csv):
            raise FileNotFoundError(f"Input file not found: {args.input_csv}")
        generate_html(args.input_csv, args.output_html)
    else:
        if not os.path.exists(args.input_dir):
            raise FileNotFoundError(f"Input directory not found: {args.input_dir}")
        process_directory(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
