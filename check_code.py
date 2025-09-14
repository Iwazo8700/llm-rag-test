#!/usr/bin/env python3
"""
Development script to run code quality checks manually.
This script runs the same checks that pre-commit would run.
"""

from pathlib import Path
import subprocess
import sys


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Run all code quality checks."""
    print("🚀 Running code quality checks for RAG system")

    # Ensure we're in the project root
    project_root = Path(__file__).parent
    if not (project_root / "app").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)

    checks = [
        # Ruff linting
        ([".venv/bin/ruff", "check", "app/", "--fix"], "Ruff linting with auto-fix"),
        # Ruff formatting
        ([".venv/bin/ruff", "format", "app/"], "Ruff code formatting"),
        # Check for common issues
        (
            [".venv/bin/python", "-m", "py_compile"]
            + [str(p) for p in Path("app").glob("*.py")],
            "Python syntax check",
        ),
        # Import check
        (
            [
                ".venv/bin/python",
                "-c",
                "from app.main import app; print('✅ All imports successful')",
            ],
            "Import validation",
        ),
    ]

    passed = 0
    failed = 0

    for command, description in checks:
        if run_command(command, description):
            passed += 1
        else:
            failed += 1

    print("\n📊 Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print("\n💡 To fix issues automatically, run:")
        print("   ruff check app/ --fix")
        print("   ruff format app/")
        sys.exit(1)
    else:
        print("\n🎉 All checks passed! Your code is ready for commit.")


if __name__ == "__main__":
    main()
