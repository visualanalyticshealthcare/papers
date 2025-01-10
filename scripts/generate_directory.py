#!/usr/bin/env python3

"""
generate_directory.py

Generates a directory page (index.html) listing all HTML files.
- Lists aggregate reports at the top
- Groups weekly reports by month
- Includes metadata like date ranges and article counts

Usage:
  python generate_directory.py --input_dir docs/ --output_html docs/index.html
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path
import json


def extract_date_range(filename):
    """Extract date range from filename."""
    match = re.search(r"epmc_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})", filename)
    if match:
        start_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        end_date = datetime.strptime(match.group(2), "%Y-%m-%d")
        return start_date, end_date
    return None, None


def count_articles_in_html(html_path):
    """Count articles in an HTML file by looking for table rows."""
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Count table rows (tr) in tbody, excluding the header
            tbody_match = re.search(r"<tbody>(.*?)</tbody>", content, re.DOTALL)
            if tbody_match:
                return len(re.findall(r"<tr>", tbody_match.group(1)))
    except Exception as e:
        print(f"Error reading {html_path}: {e}")
    return 0


def generate_directory_page(input_dir, output_html):
    """Generate a directory page listing all HTML files."""
    input_path = Path(input_dir)

    # Find aggregate and weekly reports
    aggregate_files = list(input_path.glob("aggregate*.html"))
    weekly_files = list((input_path / "weekly_reports").glob("epmc_*.html"))

    # Group weekly files by month
    weekly_by_month = {}
    for file in weekly_files:
        start_date, end_date = extract_date_range(file.stem)
        if end_date:
            month_key = end_date.strftime("%Y-%m")
            if month_key not in weekly_by_month:
                weekly_by_month[month_key] = []
            weekly_by_month[month_key].append(
                {
                    "path": file.relative_to(input_path),
                    "start_date": start_date,
                    "end_date": end_date,
                    "article_count": count_articles_in_html(file),
                }
            )

    # Sort months in reverse chronological order
    sorted_months = sorted(weekly_by_month.keys(), reverse=True)

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Analytics in Healthcare Research - Directory</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .directory-section {
            margin: 20px 0;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .month-section {
            margin: 10px 0;
            padding: 10px;
            background-color: white;
            border-radius: 3px;
        }
        .report-list {
            list-style: none;
            padding: 0;
        }
        .report-item {
            margin: 10px 0;
            padding: 10px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .report-item a {
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
        }
        .report-item a:hover {
            text-decoration: underline;
        }
        .metadata {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Visual Analytics in Healthcare Research</h1>
        
        <div class="directory-section">
            <h2>Aggregate Reports</h2>
            <ul class="report-list">
"""

    # Add aggregate reports
    for file in aggregate_files:
        article_count = count_articles_in_html(file)
        html_template += f"""
                <li class="report-item">
                    <a href="{file.name}">{file.stem.replace('_', ' ').title()}</a>
                </li>"""

    html_template += """
            </ul>
        </div>
        
        <div class="directory-section">
            <h2>Individual Reports</h2>
"""

    # Add weekly reports grouped by month
    for month in sorted_months:
        month_date = datetime.strptime(month, "%Y-%m")
        month_name = month_date.strftime("%B %Y")

        html_template += f"""
            <div class="month-section">
                <h3>{month_name}</h3>
                <ul class="report-list">
"""

        # Sort reports within month by date (newest first)
        sorted_reports = sorted(
            weekly_by_month[month], key=lambda x: x["start_date"], reverse=True
        )

        for report in sorted_reports:
            date_range = f"{report['start_date'].strftime('%b %d')} to {report['end_date'].strftime('%b %d, %Y')}"
            html_template += f"""
                    <li class="report-item">
                        <a href="{report['path']}">{date_range}</a>
                    </li>"""

        html_template += """
                </ul>
            </div>"""

    html_template += """
        </div>
    </div>
</body>
</html>
"""

    # Write the HTML file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Directory page generated: {output_html}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a directory page listing all HTML files."
    )
    parser.add_argument(
        "--input_dir",
        default="docs",
        help="Directory containing HTML files",
    )
    parser.add_argument(
        "--output_html",
        default="docs/index.html",
        help="Path to the output index.html file",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")

    generate_directory_page(args.input_dir, args.output_html)


if __name__ == "__main__":
    main()
