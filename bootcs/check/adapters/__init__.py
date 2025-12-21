"""
Language adapters for bootcs check system.

This module provides language-agnostic adapters that abstract away
language-specific details for compilation, execution, and testing.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

from .base import LanguageAdapter
from .factory import create_adapter

__all__ = [
    "LanguageAdapter",
    "create_adapter",
]
