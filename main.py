import sys
import json
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).resolve().parent / 'src'
sys.path.append(str(src_path))

from creiq.processor import RollNumberProcessor
from creiq.fetcher import URLFetcher
from creiq.parser import ARBParser
from creiq.db import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the CREIQ application.
    
    Performs the complete workflow:
    1. Process roll numbers from CSV
    2. Generate URLs
    3. Fetch content
    4. Parse HTML content
    5. Initialize database
    6. Store parsed data in the database
    7. Display a summary of stored data
    """
    # Step 1: Initialize the processor and get URLs
    logger.info("Step 1: Processing roll numbers and generating URLs...")
    csv_file = 'data/roll-number.csv'
    processor = RollNumberProcessor(csv_file)
    urls = processor.get_complete_urls()
    
    if not urls:
        logger.error("No URLs generated. Check the CSV file and environment variables.")
        return
        
    logger.info(f"Generated {len(urls)} URLs from roll numbers.")
    
    # Extract the base URL from the first complete URL
    # The base URL is everything up to the last '/'
    base_url = None
    if urls:
        base_url_parts = urls[0].rsplit('/', 1)
        if len(base_url_parts) > 1:
            base_url = base_url_parts[0] + '/'
    
    if not base_url:
        logger.warning("Could not determine base URL. Appeal detail fetching may not work correctly.")
    
    # Step 2: Fetch content from the URLs
    logger.info("\nStep 2: Fetching content from URLs...")
    results_file = 'results.json'
    parsed_results_file = 'parsed_results.json'
    
    # Check if results already exist
    if os.path.exists(results_file):
        fetch_again = input(f"\nResults file '{results_file}' already exists. Fetch again? (y/n): ").lower() == 'y'
    else:
        fetch_again = True
    
    serializable_results = {}
    
    if fetch_again:
        with URLFetcher() as fetcher:
            logger.info(f"Fetching content from {len(urls)} URLs...")
            results = {}
            
            for url in urls:
                logger.info(f"Fetching content from: {url}")
                success, content = fetcher.fetch_url(url)
                
                # Store the results
                results[url] = {
                    'success': success,
                    'content': content if success else str(content)
                }
            
            # Count successes and failures
            success_count = sum(1 for result in results.values() if result['success'])
            failure_count = len(results) - success_count
            
            logger.info(f"Fetch completed: {success_count} successful, {failure_count} failed")
            
            # Save to file
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {results_file}")
            serializable_results = results
    else:
        logger.info(f"Using existing results from {results_file}")
        with open(results_file, 'r', encoding='utf-8') as f:
            serializable_results = json.load(f)
    
    # Step 3: Parse the HTML content
    logger.info("\nStep 3: Parsing HTML content...")
    
    # Check if parsed results already exist
    if os.path.exists(parsed_results_file):
        parse_again = input(f"\nParsed results file '{parsed_results_file}' already exists. Parse again? (y/n): ").lower() == 'y'
    else:
        parse_again = True
    
    if parse_again:
        # Set to True to fetch detailed appeal information
        fetch_appeal_details = True
        max_details_to_fetch = 2  # Limit to first 2 appeals to avoid long processing time
        
        # Initialize parser with fetcher for detail fetching
        with URLFetcher() as fetcher:
            parser = ARBParser(fetcher=fetcher, base_url=base_url)
            
            # Parse each successful result
            parsed_results = {}
            for url, data in serializable_results.items():
                if data.get('success', False):
                    try:
                        logger.info(f"Parsing content from: {url}")
                        
                        # Determine the type of page (listing or detail)
                        if '/Default?' in url:
                            # This is an appeal listing page
                            parsed_data = parser.parse_appeal_listing(data['content'], fetch_appeal_details)
                            
                            # Limit the number of appeals for which details are fetched
                            if fetch_appeal_details and 'appeals' in parsed_data and len(parsed_data['appeals']) > max_details_to_fetch:
                                logger.info(f"Limiting appeal detail fetching to first {max_details_to_fetch} appeals")
                                for i in range(max_details_to_fetch, len(parsed_data['appeals'])):
                                    if 'AppealNo' in parsed_data['appeals'][i] and isinstance(parsed_data['appeals'][i]['AppealNo'], dict):
                                        # Remove any details already fetched
                                        parsed_data['appeals'][i]['AppealNo'].pop('details', None)
                        elif '/ComplaintDetail?' in url:
                            # This is an appeal detail page
                            parsed_data = parser.parse_appeal_detail(data['content'])
                        else:
                            # Unknown page type
                            parsed_data = {'error': 'Unknown page type'}
                        
                        parsed_results[url] = parsed_data
                        logger.info(f"Successfully parsed content from {url}")
                    except Exception as e:
                        logger.error(f"Error parsing content from {url}: {str(e)}")
                else:
                    logger.error(f"Skipping parsing for {url} due to fetch failure: {data.get('error', 'Unknown error')}")
            
            # Save parsed results to file
            with open(parsed_results_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_results, f, indent=2)
            
            logger.info(f"Parsed results saved to {parsed_results_file}")
    else:
        logger.info(f"Using existing parsed results from {parsed_results_file}")
        with open(parsed_results_file, 'r', encoding='utf-8') as f:
            parsed_results = json.load(f)
    
    # Step 4: Initialize database and store data
    logger.info("\nStep 4: Initializing database and storing data...")
    
    # Create database manager
    db_manager = DatabaseManager()
    
    # Create tables if they don't exist
    db_manager.create_tables()
    logger.info("Database tables initialized.")
    
    # Store parsed data in the database
    db_manager.store_data(parsed_results)
    logger.info("Data stored in the database.")
    
    # Step 5: Display a summary of stored data
    logger.info("\nStep 5: Summary of database contents:")
    
    # Get a sample roll number from the first URL
    if parsed_results:
        sample_url = list(parsed_results.keys())[0]
        sample_data = parsed_results[sample_url]
        sample_roll_number = sample_data.get('property_info', {}).get('roll_number')
        
        if sample_roll_number:
            property_info = db_manager.get_property_by_roll_number(sample_roll_number)
            appeals = db_manager.get_appeals_by_property(sample_roll_number)
            
            if property_info:
                logger.info(f"\nSample Property: {property_info.roll_number}")
                logger.info(f"Description: {property_info.property_description}")
                
                if appeals:
                    logger.info(f"\nFound {len(appeals)} appeals for this property.")
                    
                    # Display statuses
                    statuses = {}
                    for appeal in appeals:
                        status = appeal.status
                        statuses[status] = statuses.get(status, 0) + 1
                    
                    logger.info("\nAppeal statuses:")
                    for status, count in statuses.items():
                        logger.info(f"  - {status}: {count}")
                    
                    # Display a few appeal numbers as examples
                    logger.info("\nSample appeal numbers:")
                    for i, appeal in enumerate(appeals[:5], 1):
                        logger.info(f"  {i}. {appeal.appeal_number} ({appeal.status})")
                    
                    if len(appeals) > 5:
                        logger.info(f"  ...and {len(appeals) - 5} more")
        
        # Display a sample of the parsed data structure
        logger.info(f"\nSample parsed data from {sample_url}:")
        
        # Print a sample of the data structure (first few items only)
        if 'property_info' in sample_data:
            logger.info(f"Property Info: {sample_data['property_info']}")
            
            if 'appeals' in sample_data and sample_data['appeals']:
                first_appeal = sample_data['appeals'][0]
                logger.info(f"First Appeal: {first_appeal['AppealNo']['text']}")
                
                # Show a preview of appeal details if available
                if 'AppealNo' in first_appeal and 'details' in first_appeal['AppealNo']:
                    details = first_appeal['AppealNo']['details']
                    logger.info(f"Appeal Details: {list(details.keys())[:5]}...")
        else:
            logger.info(f"Appeal Details: {list(sample_data.keys())}")
    
    logger.info("\nOperation completed successfully. All data is now stored in the database.")
    logger.info("To query the database, use the CLI commands:")
    logger.info("  python -m creiq.cli db query --roll-number <roll_number> --detailed")
    logger.info("  python -m creiq.cli db query --appeal-number <appeal_number>")
    logger.info("  python -m creiq.cli db query --status <status>")
    
    return parsed_results


if __name__ == "__main__":
    main()