"""Test runner script for backend tests."""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type=None, verbose=False, coverage=False):
    """Run backend tests with pytest."""
    cmd = ["pytest"]
    
    # Add base options
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    
    # Add test type filter
    if test_type:
        if test_type == "unit":
            cmd.extend(["-m", "unit", "tests/unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration", "tests/integration"])
        elif test_type == "api":
            cmd.extend(["-m", "api"])
        elif test_type == "auth":
            cmd.extend(["-m", "auth"])
        elif test_type == "parser":
            cmd.extend(["-m", "parser"])
        elif test_type == "nlp":
            cmd.extend(["-m", "nlp"])
        else:
            print(f"Unknown test type: {test_type}")
            return 1
    else:
        # Run all tests
        cmd.append("tests/")
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run backend tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "api", "auth", "parser", "nlp"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()