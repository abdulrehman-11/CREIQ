import csv
import os
from dotenv import load_dotenv


class RollNumberProcessor:
    def __init__(self, csv_file, env_file='.env'):
        """
        Initialize the RollNumberProcessor with a CSV file and environment file.
        
        Args:
            csv_file (str): Path to the CSV file containing roll numbers
            env_file (str): Path to the environment file (default: '.env')
        """
        self.csv_file = csv_file
        # Load environment variables
        load_dotenv(env_file)
        self.base_url = os.getenv('URL')
        self.roll_numbers = []
        
    def load_roll_numbers(self):
        """
        Load roll numbers from the CSV file.
        """
        try:
            with open(self.csv_file, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row:  # Check if row is not empty
                        # Clean the roll number (remove quotes and whitespace)
                        roll_number = row[0].strip().strip('"').strip(',')
                        if roll_number:  # Check if roll_number is not empty
                            self.roll_numbers.append(roll_number)
            return True
        except Exception as e:
            print(f"Error loading roll numbers: {e}")
            return False
    
    def get_complete_urls(self):
        """
        Return a list of complete URLs by appending roll numbers to the base URL.
        
        Returns:
            list: List of complete URLs
        """
        if not self.roll_numbers:
            self.load_roll_numbers()
            
        if not self.base_url:
            print("Warning: Base URL not found in environment variables.")
            return []
            
        return [f"{self.base_url}{roll_number}" for roll_number in self.roll_numbers]
    
    def print_urls(self):
        """
        Print the base URL and all complete URLs.
        """
        urls = self.get_complete_urls()
        
        print(f"Base URL: {self.base_url}")
        print("\nComplete URLs:")
        for url in urls:
            print(url)


def main():
    """
    Main function to demonstrate the usage of RollNumberProcessor.
    """
    processor = RollNumberProcessor('roll-number.csv')
    processor.load_roll_numbers()
    processor.print_urls()
    
    # Example of how to get the URLs as a return value
    urls = processor.get_complete_urls()
    return urls


if __name__ == "__main__":
    main()