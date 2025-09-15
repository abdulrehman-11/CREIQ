"""
URL Fetcher module.

This module provides functionality for fetching web pages from URLs.
"""

import requests
import time
from typing import List, Dict, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class URLFetcher:
    """
    A class for fetching content from URLs.
    """
    
    def __init__(self, timeout: int = 30, retries: int = 3, delay: int = 1, 
                 user_agent: str = 'CREIQ-URLFetcher/1.0'):
        """
        Initialize the URLFetcher.
        
        Args:
            timeout (int): Request timeout in seconds
            retries (int): Number of retry attempts
            delay (int): Delay between retries in seconds
            user_agent (str): User agent string to use for requests
        """
        self.timeout = timeout
        self.retries = retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })
    
    def fetch_url(self, url: str) -> Tuple[bool, Union[str, Exception]]:
        """
        Fetch content from a single URL with retry logic.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            Tuple[bool, Union[str, Exception]]: A tuple containing success status and 
                                               either content or exception
        """
        for attempt in range(self.retries):
            try:
                logger.info(f"Fetching URL: {url} (Attempt {attempt + 1}/{self.retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                return True, response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching {url}: {str(e)}")
                if attempt < self.retries - 1:
                    time.sleep(self.delay)
                else:
                    return False, e
        
        # This should never be reached due to the return in the except block
        # but added for completeness
        return False, Exception("Failed to fetch URL after all retries")
    
    def fetch_multiple_urls(self, urls: List[str]) -> Dict[str, Tuple[bool, Union[str, Exception]]]:
        """
        Fetch content from multiple URLs.
        
        Args:
            urls (List[str]): List of URLs to fetch
            
        Returns:
            Dict[str, Tuple[bool, Union[str, Exception]]]: Dictionary mapping URLs to 
                                                          fetch results
        """
        results = {}
        for url in urls:
            results[url] = self.fetch_url(url)
            # Small delay to be nice to the server
            time.sleep(0.5)
        return results
    
    def close(self):
        """
        Close the requests session.
        """
        self.session.close()
        
    def __enter__(self):
        """
        Context manager entry.
        """
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        self.close()