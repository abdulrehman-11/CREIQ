"""
CREIQ package initialization.
"""

__version__ = '0.1.0'

from .fetcher import URLFetcher
from .processor import RollNumberProcessor
from .parser import ARBParser

__all__ = ['URLFetcher', 'RollNumberProcessor', 'ARBParser']