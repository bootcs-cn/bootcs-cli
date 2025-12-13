"""
Regex utilities for check50.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import re


def decimal(number):
    """
    Create a regular expression to match the number exactly.
    """
    negative_lookbehind = fr"(?<![\d\-])" if number >= 0 else ""
    return fr"{negative_lookbehind}{re.escape(str(number))}(?!(\.?\d))"
