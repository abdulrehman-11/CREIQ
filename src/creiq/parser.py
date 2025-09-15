"""
HTML Parser module.

This module provides functionality for parsing HTML content from the Assessment Review Board website.
"""

import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import re
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ARBParser:
    """
    A class for parsing HTML content from the Assessment Review Board website.
    """
    
    def __init__(self, fetcher=None, base_url=None):
        """
        Initialize the ARBParser.
        
        Args:
            fetcher: An instance of URLFetcher to fetch appeal details (optional)
            base_url (str): The base URL for the ARB website (optional)
        """
        self.fetcher = fetcher
        self.base_url = base_url
    
    def parse_appeal_listing(self, html_content: str, fetch_appeal_details: bool = False) -> Dict[str, Any]:
        """
        Parse the HTML content of an appeal listing page.
        
        Args:
            html_content (str): The HTML content of the page
            fetch_appeal_details (bool): Whether to fetch and parse appeal details
            
        Returns:
            Dict[str, Any]: Parsed data including property information and appeals list
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            property_info = self._extract_property_info(soup)
            appeals = self._extract_appeals_list(soup)
            
            # If fetcher and base_url are provided and fetch_appeal_details is True,
            # fetch details for each appeal
            if fetch_appeal_details and self.fetcher and self.base_url:
                logger.info(f"Fetching appeal details for {len(appeals)} appeals")
                for appeal in appeals:
                    if 'AppealNo' in appeal and isinstance(appeal['AppealNo'], dict) and 'url' in appeal['AppealNo']:
                        appeal_url = appeal['AppealNo']['url']
                        full_url = urllib.parse.urljoin(self.base_url, appeal_url)
                        
                        logger.info(f"Fetching appeal detail from URL: {full_url}")
                        
                        # Fetch appeal detail page
                        success, content = self.fetcher.fetch_url(full_url)
                        if success:
                            logger.info(f"Successfully fetched appeal detail, parsing content...")
                            appeal_details = self.parse_appeal_detail(content)
                            # Add details to the appeal
                            appeal['AppealNo']['details'] = appeal_details
                            logger.info(f"Added details with {len(appeal_details)} fields to appeal {appeal['AppealNo']['text']}")
                        else:
                            logger.error(f"Failed to fetch appeal details for {appeal_url}: {content}")
                            appeal['AppealNo']['details'] = {"error": str(content)}
            
            result = {
                'property_info': property_info,
                'appeals': appeals
            }
            return result
        except Exception as e:
            logger.error(f"Error parsing appeal listing: {str(e)}")
            return {'error': str(e)}
    
    def parse_appeal_detail(self, html_content: str) -> Dict[str, Any]:
        """
        Parse the HTML content of an appeal detail page.
        
        Args:
            html_content (str): The HTML content of the page
            
        Returns:
            Dict[str, Any]: Parsed appeal detail data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return self._extract_appeal_details(soup)
        except Exception as e:
            logger.error(f"Error parsing appeal detail: {str(e)}")
            return {'error': str(e)}
    
    def _extract_property_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract property information from the soup object.
        
        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page
            
        Returns:
            Dict[str, str]: Property information
        """
        property_info = {}
        
        # Extract roll number
        roll_number_div = soup.select_one('.col-md-3 + .col-md-3')
        if roll_number_div:
            property_info['roll_number'] = roll_number_div.text.strip()
        
        # Extract property description
        property_desc_div = soup.select('.row .col-md-3 + .col-md-3')
        if len(property_desc_div) > 1:
            property_info['property_description'] = property_desc_div[1].text.strip()
        
        return property_info
    
    def _extract_appeals_list(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract the list of appeals from the soup object.
        
        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page
            
        Returns:
            List[Dict[str, str]]: List of appeals
        """
        appeals = []
        
        # Find the appeals table
        table = soup.select_one('#MainContent_GridView1')
        if not table:
            return appeals
        
        # Extract headers
        headers = []
        header_row = table.select('tr:first-child th')
        for th in header_row:
            headers.append(th.text.strip())
        
        # Extract appeal rows
        appeal_rows = table.select('tr:not(:first-child)')
        for row in appeal_rows:
            appeal = {}
            cells = row.select('td')
            
            for idx, cell in enumerate(cells):
                if idx < len(headers):
                    # Handle links within cells
                    if cell.select_one('a'):
                        appeal[headers[idx]] = {
                            'text': cell.text.strip(),
                            'url': cell.select_one('a').get('href', '')
                        }
                    else:
                        appeal[headers[idx]] = cell.text.strip()
            
            appeals.append(appeal)
        
        return appeals
    
    def _extract_appeal_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract appeal details from the soup object.
        
        Args:
            soup (BeautifulSoup): The BeautifulSoup object of the page
            
        Returns:
            Dict[str, Any]: Appeal details
        """
        # Initialize the structure with separate sections
        details = {
            'property_information': {},
            'appellant_information': {}
        }
        
        # Find the main content area
        main_content = soup.find(id='MainContent_LinkButton1')
        if main_content:
            # Extract roll number from the link text
            details['property_information']['roll_number'] = main_content.text.strip()
        
        # Extract all rows with information
        rows = soup.select('.row')
        
        # Process each row to extract label-value pairs
        for row in rows:
            # Find all col-md-4 divs in this row
            cols = row.select('.col-md-4')
            
            # Need at least two columns (label and value)
            if len(cols) >= 2:
                # First column contains the label (might be wrapped in a strong tag)
                label_col = cols[0]
                value_col = cols[1]
                
                # Extract the label text
                strong_tag = label_col.find('strong')
                if strong_tag:
                    label = strong_tag.text.strip()
                else:
                    label = label_col.text.strip()
                
                # Remove trailing colon from label if present
                label = label.rstrip(':')
                
                # Extract the value text
                value = value_col.text.strip()
                
                # Skip empty values and notes
                if value and not label.lower().startswith('note'):
                    # Normalize the label to a valid key
                    key = self._normalize_key(label)
                    
                    # Categorize fields into property or appellant information
                    if key in ['property_roll_number', 'appeal_number', 'location_property_description', 
                              'municipality', 'property_classification', 'nbhd']:
                        details['property_information'][key] = value
                    elif key in ['name1', 'name_of_representative', 'filing_date', 'tax_date', 
                                'section', 'reason_for_appeal', 'status']:
                        details['appellant_information'][key] = value
                    else:
                        # For any fields not explicitly categorized, put in property information
                        details['property_information'][key] = value
        
        # Extract hearing information if available
        hearing_table = soup.select_one('#MainContent_GVHearing')
        if hearing_table:
            details['hearings'] = self._extract_hearings(hearing_table)
        
        # Extract decisions/board orders if available
        decisions_table = soup.select_one('#MainContent_GVDecision')
        if decisions_table:
            details['decisions'] = self._extract_decisions(decisions_table)
            
        return details
    
    def _extract_hearings(self, table: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract hearing information from a table.
        
        Args:
            table (BeautifulSoup): The table containing hearing information
            
        Returns:
            List[Dict[str, str]]: List of hearings
        """
        hearings = []
        
        # Extract headers
        headers = []
        header_row = table.select('tr:first-child th')
        for th in header_row:
            headers.append(th.text.strip())
        
        # Extract hearing rows
        hearing_rows = table.select('tr:not(:first-child)')
        for row in hearing_rows:
            hearing = {}
            cells = row.select('td')
            
            for idx, cell in enumerate(cells):
                if idx < len(headers):
                    hearing[self._normalize_key(headers[idx])] = cell.text.strip()
            
            hearings.append(hearing)
        
        return hearings
    
    def _extract_decisions(self, table: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract decision information from a table.
        
        Args:
            table (BeautifulSoup): The table containing decision information
            
        Returns:
            List[Dict[str, str]]: List of decisions
        """
        decisions = []
        
        # Extract headers
        headers = []
        header_row = table.select('tr:first-child th')
        for th in header_row:
            headers.append(th.text.strip())
        
        # Extract decision rows
        decision_rows = table.select('tr:not(:first-child)')
        for row in decision_rows:
            decision = {}
            cells = row.select('td')
            
            for idx, cell in enumerate(cells):
                if idx < len(headers):
                    decision[self._normalize_key(headers[idx])] = cell.text.strip()
            
            decisions.append(decision)
        
        return decisions
    
    def _normalize_key(self, key: str) -> str:
        """
        Normalize a key by converting it to snake_case.
        
        Args:
            key (str): The key to normalize
            
        Returns:
            str: Normalized key
        """
        # Replace non-alphanumeric characters with underscores
        key = re.sub(r'[^a-zA-Z0-9]', '_', key)
        # Convert to lowercase
        key = key.lower()
        # Replace multiple underscores with a single one
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        
        return key