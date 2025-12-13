"""
Context managers for check50.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import contextlib


@contextlib.contextmanager
def nullcontext(entry_result=None):
    """This is just contextlib.nullcontext but that function is only available in 3.7+."""
    yield entry_result
