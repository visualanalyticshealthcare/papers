#!/usr/bin/env python3

"""
parse_data.py

Parses JSON files from Europe PMC and ranks articles based on keyword matches.
Each JSON file is processed separately, creating a corresponding CSV file.

Usage:
  python parse_data.py --input_file data/raw/epmc_2025-01-01_to_2025-01-07.json --output_file data/weekly_reports/epmc_2025-01-01_to_2025-01-07.csv
  python parse_data.py --input_dir data/raw  # Process all JSON files in directory
"""

import argparse
import csv
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_env_keywords():
    """Load target keywords and weights from environment variables."""
    try:
        target_keywords = json.loads(os.environ.get("EPMC_TARGET_KEYWORDS", "[]"))
        keyword_weights = json.loads(os.environ.get("EPMC_KEYWORD_WEIGHTS", "{}"))
        return target_keywords, keyword_weights
    except json.JSONDecodeError:
        return [], {}


def parse_article(article, target_keywords, keyword_weights):
    """Parse a single article and calculate its score."""
    # Extract basic metadata
    pmid = article.get("pmid", "")
    title = article.get("title", "")
    abstract = article.get("abstractText", "")

    # Extract authors and first author affiliation
    authors_list = article.get("authorList", {}).get("author", [])
    authors = "; ".join(author.get("fullName", "") for author in authors_list)
    first_author_affiliation = ""
    if authors_list:
        first_author = authors_list[0]
        affiliations = first_author.get("authorAffiliationDetailsList", {}).get(
            "authorAffiliation", []
        )
        if affiliations:
            first_author_affiliation = affiliations[0].get("affiliation", "")

    # Extract journal info and publication date
    journal_info = article.get("journalInfo", {})
    journal = journal_info.get("journal", {}).get("title", "")

    # Get electronic publication date (preferred) or journal publication date
    pub_date = article.get("electronicPublicationDate", "")
    if not pub_date:
        year = journal_info.get("yearOfPublication", "")
        month = journal_info.get("monthOfPublication", "")
        day = journal_info.get("dayOfPublication", "")
        if year and month:
            pub_date = f"{year}-{month:02d}"
            if day:
                pub_date += f"-{day:02d}"

    # Extract DOI
    doi = article.get("doi", "")

    # Extract keywords from API response
    api_keywords = article.get("keywordList", {}).get("keyword", [])
    api_keywords_str = "; ".join(kw for kw in api_keywords if kw is not None)

    # Calculate score and track matches
    score = 0
    matched_keywords = []

    # Convert text to lowercase for case-insensitive matching
    title_lower = title.lower()
    abstract_lower = abstract.lower()
    api_keywords_lower = [kw.lower() for kw in api_keywords if kw is not None]

    for keyword, weight in keyword_weights.items():
        keyword_lower = keyword.lower()
        matches = []

        # Check keywords (full weight)
        if any(kw for kw in api_keywords_lower if keyword_lower in kw):
            score += weight
            matches.append("kw")

        # Check title (0.8 weight)
        if keyword_lower in title_lower:
            score += weight * 0.8
            matches.append("title")

        # Check abstract (0.5 weight)
        if keyword_lower in abstract_lower:
            score += weight * 0.5
            matches.append("abstract")

        if matches:
            matched_keywords.append(f"{keyword}({','.join(matches)})")

    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "first_author_affiliation": first_author_affiliation,
        "journal": journal,
        "pub_date": pub_date,
        "doi": doi,
        "score": round(score, 2),
        "matched_keywords": "; ".join(matched_keywords),
        "api_keywords": api_keywords_str,
    }


def parse_json_file(json_path, target_keywords, keyword_weights):
    """Parse a single JSON file and return ranked articles."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = []
    for article in data.get("articles", []):
        parsed = parse_article(article, target_keywords, keyword_weights)
        if any(
            kw.lower() in parsed["matched_keywords"].lower() for kw in target_keywords
        ):
            articles.append(parsed)

    # Sort by score descending
    articles.sort(key=lambda x: x["score"], reverse=True)
    return articles


def process_json_file(input_file, output_file, target_keywords, keyword_weights):
    """Process a single JSON file and write results to a CSV file."""
    articles = parse_json_file(input_file, target_keywords, keyword_weights)

    if not articles:
        print(f"No matching articles found in {input_file}")
        return

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
        writer.writeheader()
        writer.writerows(articles)

    print(f"Processed {len(articles)} articles from {input_file}")
    print(f"Results saved to {output_file}")


def process_directory(input_dir, output_dir, target_keywords, keyword_weights):
    """Process all JSON files in a directory."""
    input_path = Path(input_dir)
    json_files = sorted(input_path.glob("epmc_*.json"))

    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    for json_file in json_files:
        output_file = Path(output_dir) / f"{json_file.stem}.csv"
        process_json_file(json_file, output_file, target_keywords, keyword_weights)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Europe PMC JSON files and rank articles based on keywords."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--input_file",
        help="Path to a single JSON file to process",
    )
    group.add_argument(
        "--input_dir",
        help="Directory containing JSON files to process",
    )
    parser.add_argument(
        "--output_file",
        help="Path to output CSV file (required with --input_file)",
    )
    parser.add_argument(
        "--output_dir",
        default="data/weekly_reports",
        help="Directory for output CSV files (used with --input_dir)",
    )
    args = parser.parse_args()

    # Load keywords and weights
    target_keywords, keyword_weights = load_env_keywords()
    if not target_keywords or not keyword_weights:
        raise ValueError(
            "Target keywords and weights must be set in environment variables"
        )

    if args.input_file:
        if not args.output_file:
            parser.error("--output_file is required when using --input_file")
        if not os.path.exists(args.input_file):
            raise FileNotFoundError(f"Input file not found: {args.input_file}")
        process_json_file(
            args.input_file, args.output_file, target_keywords, keyword_weights
        )
    else:
        if not os.path.exists(args.input_dir):
            raise FileNotFoundError(f"Input directory not found: {args.input_dir}")
        process_directory(
            args.input_dir, args.output_dir, target_keywords, keyword_weights
        )


if __name__ == "__main__":
    main()
