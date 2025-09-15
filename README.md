# CREIQ

CREIQ is a Python package for processing roll numbers, generating URLs, and fetching web content.

## Installation

```bash
pip install -e .
```

## Usage

### As a Python module

```python
from creiq.processor import RollNumberProcessor
from creiq.fetcher import URLFetcher

# Initialize the processor with CSV file path
processor = RollNumberProcessor('data/roll-number.csv')

# Load roll numbers
processor.load_roll_numbers()

# Get complete URLs
urls = processor.get_complete_urls()

# Print URLs
processor.print_urls()

# Fetch content from the URLs
with URLFetcher() as fetcher:
    results = fetcher.fetch_multiple_urls(urls)
    
    # Process the results
    for url, (success, content_or_error) in results.items():
        if success:
            print(f"Successfully fetched {url}, content length: {len(content_or_error)}")
        else:
            print(f"Failed to fetch {url}: {content_or_error}")
```

### Command Line Interface

```bash
# Print URLs to the console
creiq --print

# Fetch content from URLs
creiq --fetch

# Fetch content and save to a file
creiq --fetch --output results.json

# Specify a different CSV file and custom timeout
creiq --csv path/to/csv/file.csv --fetch --timeout 60

# Specify a different .env file and custom retry attempts
creiq --env path/to/.env --fetch --retries 5
```

### Interactive Script

```bash
# Run the interactive script
python main.py
```

## Environment Variables

The application requires a `.env` file with the following variables:

```
URL=https://example.com/
```

## Project Structure

```
CREIQ/
│
├── data/              # Data files
│   └── roll-number.csv
│
├── docs/              # Documentation
│
├── src/               # Source code
│   └── creiq/
│       ├── __init__.py
│       ├── cli.py     # Command line interface
│       ├── processor.py # Core processor logic
│       └── fetcher.py # URL fetching functionality
│
├── tests/             # Test files
│   └── test_processor.py
│
├── .env               # Environment variables
├── main.py            # Main script
├── README.md          # This file
├── requirements.txt   # Project dependencies
└── setup.py           # Package configuration
```