"""
Unit tests for the RollNumberProcessor class.
"""

import os
import unittest
from unittest.mock import patch, mock_open
from creiq.processor import RollNumberProcessor


class TestRollNumberProcessor(unittest.TestCase):
    """Test cases for the RollNumberProcessor class."""

    @patch('creiq.processor.load_dotenv')
    @patch.dict(os.environ, {"URL": "https://test-url.com/"})
    def test_get_complete_urls(self, mock_load_dotenv):
        """Test that URLs are correctly generated."""
        # Mock the CSV file content
        mock_csv_content = "123456\n789012\n"
        
        # Create a processor instance with the mocked CSV file
        with patch('builtins.open', mock_open(read_data=mock_csv_content)):
            processor = RollNumberProcessor('fake_path.csv')
            processor.load_roll_numbers()
            
            # Get the URLs
            urls = processor.get_complete_urls()
            
            # Check the results
            self.assertEqual(len(urls), 2)
            self.assertEqual(urls[0], "https://test-url.com/123456")
            self.assertEqual(urls[1], "https://test-url.com/789012")


if __name__ == '__main__':
    unittest.main()