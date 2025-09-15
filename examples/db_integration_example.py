"""
Example script demonstrating the database integration workflow.

This script shows how to:
1. Parse the JSON results from ARBParser
2. Initialize the database
3. Store the parsed data in the database
4. Query the database for properties and appeals
"""

import json
import os
import sys
from creiq.db import DatabaseManager


def main():
    """Main function demonstrating database integration."""
    # Check if parsed results file exists
    parsed_results_path = "parsed_results.json"
    if not os.path.exists(parsed_results_path):
        print(f"Error: {parsed_results_path} not found.")
        print("Please run the parser first to generate the parsed results.")
        return
    
    # Load parsed results
    print(f"Loading parsed results from {parsed_results_path}...")
    with open(parsed_results_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)
    
    # Create database manager
    print("Initializing database...")
    db_manager = DatabaseManager()
    
    # Create tables if they don't exist
    db_manager.create_tables()
    
    # Store parsed data in the database
    print("Storing parsed data in the database...")
    db_manager.store_data(parsed_data)
    
    # Get property roll numbers for querying
    roll_numbers = []
    for url, data in parsed_data.items():
        if "property_info" in data and "roll_number" in data["property_info"]:
            roll_numbers.append(data["property_info"]["roll_number"])
    
    if not roll_numbers:
        print("No valid property roll numbers found in the parsed data.")
        return
    
    # Query and display property information
    print("\nQuerying database for property information...")
    
    sample_roll_number = roll_numbers[0]
    property_info = db_manager.get_property_by_roll_number(sample_roll_number)
    
    if property_info:
        print(f"\nProperty: {property_info.roll_number}")
        print(f"Description: {property_info.property_description}")
        if property_info.municipality:
            print(f"Municipality: {property_info.municipality}")
        if property_info.property_classification:
            print(f"Classification: {property_info.property_classification}")
        
        # Query appeals for this property
        appeals = db_manager.get_appeals_by_property(sample_roll_number)
        
        if appeals:
            print(f"\nFound {len(appeals)} appeals for this property:")
            
            # Display first 3 appeals (if available)
            for i, appeal in enumerate(appeals[:3], 1):
                print(f"\n--- Appeal {i} ---")
                print(f"Appeal Number: {appeal.appeal_number}")
                print(f"Appellant: {appeal.appellant}")
                print(f"Status: {appeal.status}")
                print(f"Tax Date: {appeal.tax_date.strftime('%Y-%m-%d') if appeal.tax_date else 'N/A'}")
                
                # Display appeal details if available
                if appeal.details:
                    print("\nAppeal Details:")
                    if appeal.details.filing_date:
                        print(f"Filing Date: {appeal.details.filing_date.strftime('%Y-%m-%d')}")
                    if appeal.details.reason_for_appeal:
                        print(f"Reason: {appeal.details.reason_for_appeal}")
            
            if len(appeals) > 3:
                print(f"\n...and {len(appeals) - 3} more appeals.")
    else:
        print(f"No property found with roll number: {sample_roll_number}")
    
    print("\nDatabase integration demonstration completed.")


if __name__ == "__main__":
    main()