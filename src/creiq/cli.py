"""
Command Line Interface module for the CREIQ package.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, List

from creiq.processor import RollNumberProcessor
from creiq.fetcher import URLFetcher
from creiq.parser import ARBParser
from creiq.db import DatabaseManager


def parse_json_file(file_path: str) -> Dict[str, Any]:
    """Parse a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Parsed JSON content as a dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: File '{file_path}' contains invalid JSON: {str(e)}")
        sys.exit(1)


def format_appeal_output(appeal, include_details=False) -> str:
    """Format appeal information for display.
    
    Args:
        appeal: Appeal object.
        include_details: Whether to include detailed information.
        
    Returns:
        Formatted string representation of the appeal.
    """
    output = [
        f"Appeal Number: {appeal.appeal_number}",
        f"Appellant: {appeal.appellant}",
        f"Status: {appeal.status}",
        f"Tax Date: {appeal.tax_date.strftime('%Y-%m-%d') if appeal.tax_date else 'N/A'}",
        f"Section: {appeal.section}"
    ]
    
    if appeal.board_order_no:
        output.append(f"Board Order No: {appeal.board_order_no}")
    
    if include_details and appeal.details:
        output.append("\nAppeal Details:")
        if appeal.details.filing_date:
            output.append(f"Filing Date: {appeal.details.filing_date.strftime('%Y-%m-%d')}")
        if appeal.details.reason_for_appeal:
            output.append(f"Reason: {appeal.details.reason_for_appeal}")
        if appeal.details.decision_text:
            output.append(f"Decision: {appeal.details.decision_text}")
    
    return "\n".join(output)


def handle_db_command(args):
    """Handle database-related commands.
    
    Args:
        args: Command-line arguments.
    """
    db_manager = DatabaseManager()
    
    if args.db_command == 'init':
        db_manager.create_tables()
        print("Database initialized successfully.")
    
    elif args.db_command == 'store':
        if not args.input:
            print("Error: --input is required for 'store' command.")
            sys.exit(1)
        
        parsed_data = parse_json_file(args.input)
        db_manager.store_data(parsed_data)
        print(f"Data from {args.input} stored in the database.")
    
    elif args.db_command == 'query':
        if args.roll_number:
            property_obj = db_manager.get_property_by_roll_number(args.roll_number)
            if not property_obj:
                print(f"No property found with roll number: {args.roll_number}")
                return
            
            print(f"\nProperty: {property_obj.roll_number}")
            print(f"Description: {property_obj.property_description}")
            if property_obj.municipality:
                print(f"Municipality: {property_obj.municipality}")
            if property_obj.property_classification:
                print(f"Classification: {property_obj.property_classification}")
            
            appeals = db_manager.get_appeals_by_property(args.roll_number)
            if appeals:
                print(f"\nAppeals ({len(appeals)}):")
                for i, appeal in enumerate(appeals, 1):
                    print(f"\n--- Appeal {i} ---")
                    print(format_appeal_output(appeal, args.detailed))
            else:
                print("\nNo appeals found for this property.")
        
        elif args.appeal_number:
            appeal = db_manager.get_appeal_by_number(args.appeal_number)
            if appeal:
                print(format_appeal_output(appeal, args.detailed))
            else:
                print(f"No appeal found with number: {args.appeal_number}")
        
        elif args.status:
            appeals = db_manager.get_appeals_by_status(args.status)
            if appeals:
                print(f"Found {len(appeals)} appeals with status '{args.status}':")
                for i, appeal in enumerate(appeals, 1):
                    print(f"\n--- Appeal {i} ---")
                    print(format_appeal_output(appeal, args.detailed))
            else:
                print(f"No appeals found with status: {args.status}")
    
    elif args.db_command == 'export':
        if not args.output:
            print("Error: --output is required for 'export' command.")
            sys.exit(1)
        
        if args.roll_number:
            property_obj = db_manager.get_property_by_roll_number(args.roll_number)
            if not property_obj:
                print(f"No property found with roll number: {args.roll_number}")
                return
            
            appeals = db_manager.get_appeals_by_property(args.roll_number)
            
            # Create serializable data structure
            export_data = {
                'property_info': {
                    'roll_number': property_obj.roll_number,
                    'property_description': property_obj.property_description,
                    'municipality': property_obj.municipality,
                    'property_classification': property_obj.property_classification,
                    'neighborhood': property_obj.neighborhood
                },
                'appeals': []
            }
            
            for appeal in appeals:
                appeal_data = {
                    'appeal_number': appeal.appeal_number,
                    'appellant': appeal.appellant,
                    'section': appeal.section,
                    'tax_date': appeal.tax_date.isoformat() if appeal.tax_date else None,
                    'status': appeal.status,
                    'board_order_no': appeal.board_order_no
                }
                
                if appeal.details:
                    appeal_data['details'] = {
                        'filing_date': appeal.details.filing_date.isoformat() if appeal.details.filing_date else None,
                        'reason_for_appeal': appeal.details.reason_for_appeal,
                        'decision_mailing_date': appeal.details.decision_mailing_date.isoformat() if appeal.details.decision_mailing_date else None,
                        'decision_text': appeal.details.decision_text,
                        'decision_details': appeal.details.decision_details
                    }
                
                export_data['appeals'].append(appeal_data)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Exported property {args.roll_number} data to {args.output}")


def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(description='Process roll numbers and generate URLs.')
    parser.add_argument('--csv', default='data/roll-number.csv',
                        help='Path to the CSV file containing roll numbers')
    parser.add_argument('--env', default='.env',
                        help='Path to the .env file containing environment variables')
    parser.add_argument('--print', action='store_true',
                        help='Print the URLs to the console')
    parser.add_argument('--fetch', action='store_true',
                        help='Fetch content from the URLs')
    parser.add_argument('--output', default='',
                        help='Path to save the fetched content (JSON format)')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Timeout for HTTP requests in seconds')
    parser.add_argument('--retries', type=int, default=3,
                        help='Number of retry attempts for failed requests')
    parser.add_argument('--parse', action='store_true',
                        help='Parse fetched HTML content using ARBParser')
    parser.add_argument('--fetch-details', action='store_true',
                        help='When parsing, fetch appeal details from detail pages')
    parser.add_argument('--input', default='',
                        help='Path to read input data from (JSON format)')
    
    # Add database subcommands
    subparsers = parser.add_subparsers(dest='command')
    
    # Database commands subparser
    db_parser = subparsers.add_parser('db', help='Database operations')
    db_subparsers = db_parser.add_subparsers(dest='db_command')
    
    # Initialize database
    init_parser = db_subparsers.add_parser('init', help='Initialize the database')
    
    # Store data in database
    store_parser = db_subparsers.add_parser('store', help='Store data in database')
    store_parser.add_argument('--input', required=True, help='Input JSON file with parsed data')
    
    # Query data
    query_parser = db_subparsers.add_parser('query', help='Query database')
    query_parser.add_argument('--roll-number', help='Query by roll number')
    query_parser.add_argument('--appeal-number', help='Query by appeal number')
    query_parser.add_argument('--status', help='Query by status')
    query_parser.add_argument('--detailed', action='store_true', help='Include detailed information')
    
    # Export data
    export_parser = db_subparsers.add_parser('export', help='Export data from database')
    export_parser.add_argument('--roll-number', help='Roll number to export')
    export_parser.add_argument('--output', required=True, help='Output JSON file')
    
    args = parser.parse_args()
    
    # Handle database commands
    if args.command == 'db':
        handle_db_command(args)
        return
    
    # Initialize and load the roll numbers
    processor = RollNumberProcessor(args.csv, args.env)
    processor.load_roll_numbers()
    
    # Get the complete URLs
    urls = processor.get_complete_urls()
    
    # Print URLs if requested
    if args.print:
        processor.print_urls()
    
    # Fetch content if requested
    if args.fetch:
        print(f"\nFetching content from {len(urls)} URLs...")
        
        with URLFetcher(timeout=args.timeout, retries=args.retries) as fetcher:
            results = fetcher.fetch_multiple_urls(urls)
        
        # Count successes and failures
        success_count = sum(1 for result in results.values() if result[0])
        failure_count = len(results) - success_count
        
        print(f"Fetch completed: {success_count} successful, {failure_count} failed")
        
        # Save results to file if output path is provided
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # Convert results to a serializable format
            serializable_results = {}
            for url, (success, content_or_error) in results.items():
                if success:
                    serializable_results[url] = {
                        'success': True,
                        'content': content_or_error
                    }
                else:
                    serializable_results[url] = {
                        'success': False,
                        'error': str(content_or_error)
                    }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2)
            
            print(f"Results saved to {args.output}")
    
    # Parse content if requested
    if args.parse:
        # Check if we have input data
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                results = json.load(f)
        elif args.fetch:
            # Use the results from the fetch operation
            print("Using results from fetch operation for parsing.")
            # Convert from the serializable format back to the expected format
            raw_results = {}
            for url, data in serializable_results.items():
                if data['success']:
                    raw_results[url] = (True, data['content'])
                else:
                    raw_results[url] = (False, data['error'])
            results = raw_results
        else:
            print("Error: No data to parse. Use --fetch or --input to provide data.")
            return
        
        print("\nParsing fetched content...")
        
        # Initialize parser
        parser = ARBParser()
        
        # Parse each successful result
        parsed_results = {}
        for url, (success, content_or_error) in results.items():
            if success:
                try:
                    parsed_results[url] = parser.parse_appeal_listing(content_or_error, args.fetch_details)
                    print(f"Successfully parsed content from {url}")
                except Exception as e:
                    print(f"Error parsing content from {url}: {str(e)}")
            else:
                print(f"Skipping parsing for {url} due to fetch failure: {content_or_error}")
        
        # Save parsed results to file if output path is provided
        if args.output:
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(parsed_results, f, indent=2)
            
            print(f"Parsed results saved to {args.output}")
            
            # Store in database if requested
            if args.command == 'db' and args.db_command == 'store':
                db_manager = DatabaseManager()
                db_manager.create_tables()
                db_manager.store_data(parsed_results)
                print(f"Parsed results stored in database.")
    
    return urls


if __name__ == "__main__":
    main()