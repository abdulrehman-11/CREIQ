"""
Example script showing how to use the CREIQ package components together.

This example demonstrates:
1. Processing roll numbers
2. Generating URLs
3. Fetching content
4. Parsing the content with detailed appeal information
"""

import json
import os
import logging
from creiq import RollNumberProcessor, URLFetcher, ARBParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    # Step 1: Process roll numbers and generate URLs
    csv_file = 'data/roll-number.csv'
    processor = RollNumberProcessor(csv_file)
    urls = processor.get_complete_urls()
    
    if not urls:
        logger.error("No URLs generated. Check the CSV file and environment variables.")
        return
    
    logger.info(f"Generated {len(urls)} URLs from roll numbers")
    
    # Extract the base URL from the first complete URL
    # The base URL is everything up to the last '/'
    base_url = None
    if urls:
        base_url_parts = urls[0].rsplit('/', 1)
        if len(base_url_parts) > 1:
            base_url = base_url_parts[0] + '/'
    
    if not base_url:
        logger.warning("Could not determine base URL. Appeal detail fetching may not work correctly.")
    
    # Step 2: Fetch content from the generated URLs
    results = {}
    with URLFetcher() as fetcher:
        # Fetch only a subset for demo purposes
        demo_urls = urls  # Fetch all URLs
        
        for url in demo_urls:
            logger.info(f"Fetching content from: {url}")
            success, content = fetcher.fetch_url(url)
            
            # Store the results
            results[url] = {
                'success': success,
                'content': content if success else str(content)
            }
    
        # Step 3: Parse the fetched content with detail fetching
        parser = ARBParser(fetcher=fetcher, base_url=base_url)
        parsed_results = {}
        
        # Set to True to fetch detailed appeal information
        fetch_appeal_details = True
        max_details_to_fetch = 2  # Limit to first 2 appeals to avoid long processing time
        
        for url, result in results.items():
            if result['success']:
                logger.info(f"Parsing content from: {url}")
                
                # Determine the type of page (listing or detail)
                if '/Default?' in url:
                    # This is an appeal listing page
                    parsed_data = parser.parse_appeal_listing(result['content'], fetch_appeal_details)
                    
                    # Limit the number of appeals for which details are fetched
                    if fetch_appeal_details and 'appeals' in parsed_data and len(parsed_data['appeals']) > max_details_to_fetch:
                        logger.info(f"Limiting appeal detail fetching to first {max_details_to_fetch} appeals")
                        for i in range(max_details_to_fetch, len(parsed_data['appeals'])):
                            if 'AppealNo' in parsed_data['appeals'][i] and isinstance(parsed_data['appeals'][i]['AppealNo'], dict):
                                # Remove any details already fetched
                                parsed_data['appeals'][i]['AppealNo'].pop('details', None)
                elif '/ComplaintDetail?' in url:
                    # This is an appeal detail page
                    parsed_data = parser.parse_appeal_detail(result['content'])
                else:
                    # Unknown page type
                    parsed_data = {'error': 'Unknown page type'}
                
                parsed_results[url] = parsed_data
            else:
                logger.error(f"Failed to fetch content from {url}: {result['content']}")
    
    # Step 4: Save the parsed results to a file
    output_file = 'parsed_results.json'
    with open(output_file, 'w') as f:
        json.dump(parsed_results, f, indent=2)
    
    logger.info(f"Parsed results saved to {output_file}")
    
    # Display a sample of the parsed data
    if parsed_results:
        sample_url = next(iter(parsed_results))
        logger.info(f"Sample parsed data from {sample_url}:")
        
        # Print a sample of the data structure (first few items only)
        sample_data = parsed_results[sample_url]
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
    

if __name__ == '__main__':
    main()