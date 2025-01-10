# Visual Analytics in Healthcare Research Papers Scraper

This project automates the retrieval, parsing, and ranking of research articles on **Visual Analytics in Healthcare**. It generates **interactive HTML pages** that allow users to dynamically customize rankings based on keywords and weights.

Additionally, a **directory page** is created for easy navigation, listing all generated pages with metadata (e.g., date ranges and article counts). The project is compatible with **GitHub Pages**, making the results publicly accessible.

---

## Features

1. **Automated Article Retrieval**:
   - Fetches articles from Europe PMC based on configurable keywords and date ranges.
2. **Keyword-based Ranking**:
   - Ranks articles by the occurrence and weights of specified keywords.
3. **Interactive HTML Pages**:
   - Users can customize keyword weights and recalculate rankings dynamically in the browser.
4. **Directory Page**:
   - Lists all HTML pages with metadata (e.g., date ranges, article counts).
5. **Customizable Configuration**:
   - Keywords, weights, and query parameters are defined in environment variables.
   - CLI arguments allow flexibility for custom date ranges and input/output directories.

---

## Workflow

1. **Fetch Data**:
   - Use `fetch_data.py` to retrieve articles from Europe PMC for a given date range.
   - Saves results as JSON files in `data/raw/`.

2. **Parse and Rank Data**:
   - Use `parse_data.py` to process the raw JSON files and rank articles based on keyword matches.
   - Saves ranked results as CSV files in `data/weekly_reports/`.

3. **Generate HTML Pages**:
   - Use `generate_html.py` to create interactive HTML pages from the ranked CSV files.
   - Saves the pages in the `docs/` directory.

4. **Create Directory Page**:
   - Use `generate_directory.py` to create a directory page (`index.html`) listing all HTML pages with metadata.
   - Updates the `docs/` directory to serve as the root for GitHub Pages.

---

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- [Hatch](https://hatch.pypa.io/latest/) for environment management

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/visual-analytics-healthcare.git
   cd visual-analytics-healthcare
   ```

2. Install Hatch:
   ```bash
   pip install hatch
   ```

3. Create and activate the environment:
   ```bash
   hatch env create
   hatch shell
   ```

4. Verify setup:
   ```bash
   hatch run python --version
   ```

---

## CLI Arguments for Scripts

### **1. `fetch_data.py`**
Fetches articles from Europe PMC based on keywords and date ranges.

#### CLI Arguments:
- `--end_date`: End date for the query (format: `YYYY-MM-DD`). Defaults to today.
- `--days_back`: Number of days before the end date to include in the query. Defaults to `7`.

#### Usage:
```bash
hatch run python scripts/fetch_data.py
hatch run python scripts/fetch_data.py --days_back 14 --end_date 2025-01-20
```

---

### **2. `parse_data.py`**
Parses raw JSON files, ranks articles based on keywords, and outputs a ranked CSV file.

#### CLI Arguments:
- `--input_dir`: Directory containing raw JSON files. Defaults to `data/raw/`.
- `--output_dir`: Directory to save ranked CSV files. Defaults to `data/weekly_reports/`.

#### Usage:
```bash
hatch run python scripts/parse_data.py
hatch run python scripts/parse_data.py --input_dir data/raw --output_dir data/custom_reports
```

---

### **3. `generate_html.py`**
Generates an interactive HTML page from a ranked CSV file.

#### CLI Arguments:
- `--input_csv`: Path to the input CSV file (from `parse_data.py`).
- `--output_html`: Path to the output HTML file. Defaults to `docs/<filename>.html`.

#### Usage:
```bash
hatch run python scripts/generate_html.py --input_csv data/weekly_reports/parsed_articles.csv --output_html docs/epmc_2025-01-01_to_2025-01-07.html
```

---

### **4. `generate_directory.py`**
Generates a directory page (`index.html`) listing all HTML files in a given directory.

#### CLI Arguments:
- `--input_dir`: Directory containing HTML files. Defaults to `docs/`.
- `--output_html`: Path to the output `index.html` file. Defaults to `docs/index.html`.

#### Usage:
```bash
hatch run python scripts/generate_directory.py --input_dir docs/ --output_html docs/index.html
```

---

## Example Workflow

1. Fetch data:
   ```bash
   hatch run python scripts/fetch_data.py --days_back 14 --end_date 2025-01-20
   ```

2. Parse and rank articles:
   ```bash
   hatch run python scripts/parse_data.py --input_dir data/raw --output_dir data/weekly_reports
   ```

3. Generate an HTML page for ranked articles:
   ```bash
   hatch run python scripts/generate_html.py --input_csv data/weekly_reports/parsed_articles.csv --output_html docs/epmc_2025-01-01_to_2025-01-07.html
   ```

4. Create a directory page listing all HTML files:
   ```bash
   hatch run python scripts/generate_directory.py --input_dir docs/ --output_html docs/index.html
   ```

---

## GitHub Pages Setup

1. Push the `docs/` directory to the repository.
2. Enable GitHub Pages in the repository settings:
   - Go to **Settings** > **Pages**.
   - Set the source to the `main` branch and the `docs/` folder.
3. Access the hosted pages at:
   ```
   https://your-username.github.io/visual-analytics-healthcare/
   ```

---

## Limitations

1. **Keyword Matching**:
   - Relies on exact matches for keywords; may miss synonyms or variations.
2. **Static Metadata Extraction**:
   - Metadata is inferred from filenames or simple patterns, which may not handle complex cases.
3. **Manual Execution**:
   - Steps must currently be run manually or integrated into automation pipelines.

---

## Future Work

1. **Automated Pipeline**:
   - Automate the entire workflow with GitHub Actions.
2. **Improved Ranking**:
   - Incorporate NLP techniques for more advanced ranking.
3. **Dynamic Keyword Customization**:
   - Allow users to dynamically add/remove keywords in the browser.
4. **Visualization**:
   - Add charts and visual analytics to HTML pages.

---

## Running the Complete Pipeline

### Weekly Update Process

The pipeline is designed to run weekly updates automatically. Here's how to run it:

```bash
# 1. Activate Hatch environment
hatch shell

# 2. Run the entire pipeline
hatch run fetch-parse-generate


### Manual Processing Options

For manual processing or custom date ranges:

```bash
# 1. Activate Hatch environment
hatch shell

# 2. Fetch articles for a specific date range
hatch run python scripts/fetch_data.py --days_back 14 --end_date 2025-01-20

# 3. Process all unprocessed JSON files
for json_file in data/raw/epmc_*.json; do
    # Skip if corresponding CSV already exists
    csv_file="data/weekly_reports/$(basename "$json_file" .json).csv"
    if [ ! -f "$csv_file" ]; then
        hatch run python scripts/parse_data.py \
            --input_file "$json_file" \
            --output_file "$csv_file"
    fi
done

# 4. Generate HTML pages for new CSV files
for csv_file in data/weekly_reports/epmc_*.csv; do
    # Skip if corresponding HTML already exists
    html_file="docs/$(basename "$csv_file" .csv).html"
    if [ ! -f "$html_file" ]; then
        hatch run python scripts/generate_html.py \
            --input_csv "$csv_file" \
            --output_html "$html_file"
    fi
done

# 5. Update directory index
hatch run python scripts/generate_directory.py \
    --input_dir docs/ \
    --output_html docs/index.html \
    --group_by month  # Group pages by month
```


### Error Handling

The pipeline includes error handling for common issues:

1. **Duplicate Prevention**:
   - Skips processing of already processed files
   - Uses file naming conventions to track processed data

2. **Data Integrity**:
   - Validates JSON files before processing
   - Ensures required fields exist in CSV files
   - Verifies HTML file generation

3. **Resource Management**:
   - Manages API rate limits
   - Handles large file processing efficiently
   - Cleans up temporary files

4. **Recovery**:
   - Can resume from any point in the pipeline
   - Maintains data consistency across updates

---

## Troubleshooting

### Common Issues

1. **Environment Variables Not Found**:
   ```bash
   # Check if environment variables are set
   hatch run python -c "import os; print(os.environ.get('EPMC_QUERY_KEYWORDS'))"
   ```

2. **No Articles Found**:
   ```bash
   # Check the query parameters
   hatch run python scripts/fetch_data.py --days_back 14  # Try a larger date range
   ```

3. **Test Failures**:
   ```bash
   # Run tests with detailed output
   hatch run python -m unittest -v
   ```

4. **Missing Dependencies**:
   ```bash
   # Verify Hatch environment
   hatch env show
   ```

For more detailed troubleshooting, check the logs in:
- `data/raw/` for raw API responses
- `data/weekly_reports/` for parsed data
- Browser console for JavaScript issues in generated HTML pages
