"""
C language support for check50.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import re
import tempfile
from pathlib import Path
import xml.etree.cElementTree as ET

from ._api import run, log, Failure
from . import internal


def _(s):
    """Translation function - returns string as-is for now."""
    return s


#: Default compiler for compile()
CC = "clang"

#: Default CFLAGS for compile()
CFLAGS = {"std": "c11", "ggdb": True, "lm": True}


def compile(*files, exe_name=None, cc=CC, max_log_lines=50, **cflags):
    """
    Compile C source files.

    :param files: filenames to be compiled
    :param exe_name: name of resulting executable
    :param cc: compiler to use (CC by default)
    :param cflags: additional flags to pass to the compiler
    :raises check50.Failure: if compilation failed
    :raises RuntimeError: if no filenames are specified
    """

    if not files:
        raise RuntimeError(_("compile requires at least one file"))

    if exe_name is None and files[0].endswith(".c"):
        exe_name = Path(files[0]).stem

    files_str = " ".join(files)

    flags = CFLAGS.copy()
    flags.update(cflags)
    flags = " ".join((f"-{flag}" + (f"={value}" if value is not True else "")).replace("_", "-")
                     for flag, value in flags.items() if value)

    out_flag = f" -o {exe_name} " if exe_name is not None else " "

    process = run(f"{cc} {files_str}{out_flag}{flags}")

    # Strip out ANSI codes
    stdout = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "",  process.stdout())

    # Log max_log_lines lines of output in case compilation fails
    if process.exitcode != 0:
        lines = stdout.splitlines()

        if len(lines) > max_log_lines:
            lines = lines[:max_log_lines // 2] + lines[-(max_log_lines // 2):]

        for line in lines:
            log(line)

        raise Failure("code failed to compile")


def valgrind(command, env={}):
    """
    Run a command with valgrind.

    :param command: command to be run
    :type command: str
    :param env: environment in which to run command
    :type env: str
    :raises check50.Failure: if valgrind reports any errors
    """
    xml_file = tempfile.NamedTemporaryFile()
    internal.register.after_check(lambda: _check_valgrind(xml_file))

    return run(f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}", env=env)


def _check_valgrind(xml_file):
    """Log and report any errors encountered by valgrind."""
    log(_("checking for valgrind errors..."))

    xml = ET.ElementTree(file=xml_file)

    reported = set()
    for error in xml.iterfind("error"):
        kind = error.find("kind").text
        what = error.find("xwhat/text" if kind.startswith("Leak_") else "what").text

        msg = ["\t", what]

        for frame in error.iterfind("stack/frame"):
            obj = frame.find("obj")
            if obj is not None and internal.run_dir in Path(obj.text).parents:
                file, line = frame.find("file"), frame.find("line")
                if file is not None and line is not None:
                    msg.append(f": ({_('file')}: {file.text}, {_('line')}: {line.text})")
                break

        msg = "".join(msg)
        if msg not in reported:
            log(msg)
            reported.add(msg)

    if reported:
        raise Failure(_("valgrind tests failed; see log for more information."))
