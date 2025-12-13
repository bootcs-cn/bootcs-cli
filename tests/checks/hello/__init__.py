"""
Hello World Check - Test check for bootcs-cli-v2
"""

from bootcs.check import check, exists as check_exists, run
from bootcs.check import c


@check()
def exists():
    """hello.c exists"""
    check_exists("hello.c")


@check(exists)
def compiles():
    """hello.c compiles"""
    c.compile("hello.c")


@check(compiles)
def prints_hello():
    """prints 'Hello, World!'"""
    run("./hello").stdout("Hello").exit(0)
