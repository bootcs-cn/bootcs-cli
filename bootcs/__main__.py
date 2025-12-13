"""
BootCS CLI - Main entry point

Usage:
    bootcs check <slug>
    bootcs submit <slug>
"""

import argparse
import json
import os
import sys
from pathlib import Path

import termcolor

from . import __version__
from .check import internal
from .check.runner import CheckRunner
from . import lib50


def main():
    """Main entry point for bootcs CLI."""
    parser = argparse.ArgumentParser(
        prog="bootcs",
        description="BootCS CLI - Check and submit your code"
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check your code against tests")
    check_parser.add_argument("slug", help="The check slug (e.g., course-cs50/mario-less)")
    check_parser.add_argument("-o", "--output", choices=["ansi", "json"], default="ansi",
                              help="Output format (default: ansi)")
    check_parser.add_argument("--log", action="store_true", help="Show detailed log")
    check_parser.add_argument("--target", action="append", metavar="check",
                              help="Run only the specified check(s)")
    check_parser.add_argument("--local", metavar="PATH", help="Path to local checks directory")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit your code")
    submit_parser.add_argument("slug", help="The submission slug")
    
    args = parser.parse_args()
    
    if args.command == "check":
        return run_check(args)
    elif args.command == "submit":
        return run_submit(args)
    else:
        parser.print_help()
        return 1


def run_check(args):
    """Run the check command."""
    slug = args.slug
    
    # Determine check directory
    if args.local:
        check_dir = Path(args.local).resolve()
    else:
        # For now, look for checks in a local directory structure
        # Future: download from remote like check50 does
        check_dir = find_check_dir(slug)
    
    if not check_dir or not check_dir.exists():
        termcolor.cprint(f"Error: Could not find checks for '{slug}'", "red", file=sys.stderr)
        return 1
    
    # Set internal state
    internal.check_dir = check_dir
    internal.slug = slug
    
    # Load config
    try:
        config = internal.load_config(check_dir)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1
    
    checks_file = check_dir / config["checks"]
    if not checks_file.exists():
        termcolor.cprint(f"Error: Checks file '{config['checks']}' not found in {check_dir}", "red", file=sys.stderr)
        return 1
    
    # Get list of files to include
    cwd = Path.cwd()
    try:
        included, excluded = lib50.files(config.get("files", []), root=cwd)
    except lib50.Error as e:
        termcolor.cprint(f"Error: {e}", "red", file=sys.stderr)
        return 1
    
    if not included:
        termcolor.cprint("Warning: No files found to check", "yellow", file=sys.stderr)
    
    # Print header
    print()
    termcolor.cprint(f"🔍 Running checks for {slug}...", "cyan", attrs=["bold"])
    print()
    
    # Run checks
    targets = args.target if hasattr(args, 'target') and args.target else None
    
    try:
        with CheckRunner(checks_file, list(included)) as runner:
            results = runner.run(targets=targets)
    except Exception as e:
        termcolor.cprint(f"Error running checks: {e}", "red", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Output results
    if args.output == "json":
        output_json(results, args.log)
    else:
        output_ansi(results, args.log)
    
    # Return 0 if all checks passed, 1 otherwise
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    if passed == total:
        return 0
    else:
        return 1


def output_ansi(results, show_log=False):
    """Output results in ANSI format (colored terminal output)."""
    for result in results:
        if result.passed is True:
            emoji = "✅"
            color = "green"
        elif result.passed is False:
            emoji = "❌"
            color = "red"
        else:
            emoji = "⏭️"
            color = "yellow"
        
        termcolor.cprint(f"{emoji} {result.description}", color)
        
        if result.cause and result.passed is False:
            rationale = result.cause.get("rationale", "")
            if rationale:
                print(f"   └─ {rationale}")
            help_msg = result.cause.get("help")
            if help_msg:
                termcolor.cprint(f"   💡 {help_msg}", "cyan")
        
        if show_log and result.log:
            print("   Log:")
            for line in result.log:
                print(f"      {line}")
    
    print()
    
    # Summary
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if r.passed is False)
    skipped = sum(1 for r in results if r.passed is None)
    
    summary = f"Results: {passed} passed"
    if failed:
        summary += f", {failed} failed"
    if skipped:
        summary += f", {skipped} skipped"
    
    if failed == 0:
        termcolor.cprint(f"🎉 {summary}", "green", attrs=["bold"])
    else:
        termcolor.cprint(summary, "yellow")


def output_json(results, show_log=False):
    """Output results in JSON format."""
    output = {
        "slug": internal.slug,
        "version": __version__,
        "results": []
    }
    
    for result in results:
        r = {
            "name": result.name,
            "description": result.description,
            "passed": result.passed,
        }
        if result.cause:
            r["cause"] = result.cause
        if show_log:
            r["log"] = result.log
        if result.data:
            r["data"] = result.data
        if result.dependency:
            r["dependency"] = result.dependency
        output["results"].append(r)
    
    print(json.dumps(output, indent=2))


def find_check_dir(slug):
    """Find the check directory for a given slug."""
    # Common locations to search
    search_paths = [
        Path.cwd() / "checks" / slug,
        Path.cwd().parent / "checks" / slug,
        Path.home() / ".local" / "share" / "bootcs" / slug,
    ]
    
    # Also check environment variable
    if "BOOTCS_CHECKS_PATH" in os.environ:
        search_paths.insert(0, Path(os.environ["BOOTCS_CHECKS_PATH"]) / slug)
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None


def run_submit(args):
    """Run the submit command."""
    termcolor.cprint("Submit command not yet implemented", "yellow")
    return 1


if __name__ == "__main__":
    sys.exit(main())
