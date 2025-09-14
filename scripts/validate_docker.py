#!/usr/bin/env python3
"""
Script to validate the Docker setup and configuration files.
"""

import os
from pathlib import Path
import sys

import yaml


def check_file(file_path, description):
    """Check if a file exists and return status."""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    print(f"❌ Missing {description}: {file_path}")
    return False


def validate_dockerfile():
    """Validate Dockerfile content."""
    print("\n🔍 Validating Dockerfile...")

    if not check_file("Dockerfile", "Dockerfile"):
        return False

    with Path("Dockerfile").open() as f:
        content = f.read()

    required_elements = [
        "FROM python",
        "WORKDIR /app",
        "COPY requirements.txt",
        "RUN pip install",
        "EXPOSE 8000",
        "CMD",
    ]

    for element in required_elements:
        if element in content:
            print(f"✅ Found: {element}")
        else:
            print(f"❌ Missing: {element}")
            return False

    return True


def validate_docker_compose():
    """Validate docker-compose.yml content."""
    print("\n🔍 Validating docker-compose.yml...")

    if not check_file("docker-compose.yml", "Docker Compose file"):
        return False

    try:
        with Path("docker-compose.yml").open() as f:
            compose_data = yaml.safe_load(f)

        # Check required sections
        if "services" not in compose_data:
            print("❌ Missing 'services' section")
            return False

        if "rag-app" not in compose_data["services"]:
            print("❌ Missing 'rag-app' service")
            return False

        service = compose_data["services"]["rag-app"]

        # Check required service configuration
        required_keys = ["build", "ports", "environment", "volumes"]
        for key in required_keys:
            if key in service:
                print(f"✅ Service has {key} configuration")
            else:
                print(f"❌ Service missing {key} configuration")

        return True

    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in docker-compose.yml: {e}")
        return False


def validate_environment():
    """Validate environment configuration."""
    print("\n🔍 Validating environment configuration...")

    check_file(".env.example", "Environment template")

    if check_file(".env", "Environment file"):
        print("✅ Environment file exists")
    else:
        print("⚠️  No .env file found. Copy from .env.example")

    return True


def validate_supporting_files():
    """Validate supporting Docker files."""
    print("\n🔍 Validating supporting files...")

    files_to_check = [
        (".dockerignore", "Docker ignore file"),
        ("docker/nginx.conf", "Nginx configuration"),
        ("docker/manage.sh", "Management script"),
        ("DOCKER_DEPLOYMENT.md", "Deployment documentation"),
    ]

    all_present = True
    for file_path, description in files_to_check:
        if not check_file(file_path, description):
            all_present = False

    # Check if management script is executable
    if Path("docker/manage.sh").exists():
        if os.access("docker/manage.sh", os.X_OK):
            print("✅ Management script is executable")
        else:
            print(
                "⚠️  Management script is not executable. Run: chmod +x docker/manage.sh"
            )

    return all_present


def validate_application_structure():
    """Validate application structure for Docker."""
    print("\n🔍 Validating application structure...")

    required_dirs = ["app", "scripts"]
    required_files = [
        "requirements.txt",
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/embeddings.py",
        "app/rag.py",
        "app/models.py",
    ]

    all_present = True

    # Check directories
    for dir_name in required_dirs:
        if Path(dir_name).is_dir():
            print(f"✅ Directory: {dir_name}/")
        else:
            print(f"❌ Missing directory: {dir_name}/")
            all_present = False

    # Check files
    for file_path in required_files:
        if not check_file(file_path, "Application file"):
            all_present = False

    return all_present


def check_docker_daemon():
    """Check if Docker daemon is running."""
    print("\n🔍 Checking Docker daemon...")

    try:
        import subprocess

        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            print("✅ Docker daemon is running")
            return True
        print("❌ Docker daemon is not responding")
        print(f"Error: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
        return False
    except FileNotFoundError:
        print("❌ Docker command not found. Is Docker installed?")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def main():
    """Run all validation checks."""
    print("🐳 Docker Setup Validation")
    print("=" * 50)

    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    print(f"📍 Working directory: {Path.cwd()}")

    # Run all validation checks
    checks = [
        ("Docker Daemon", check_docker_daemon),
        ("Application Structure", validate_application_structure),
        ("Dockerfile", validate_dockerfile),
        ("Docker Compose", validate_docker_compose),
        ("Environment", validate_environment),
        ("Supporting Files", validate_supporting_files),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error during {check_name} check: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📋 Validation Summary")
    print("=" * 50)

    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1

    total = len(results)
    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Your Docker setup is ready.")
        print("\nNext steps:")
        print("1. ./docker/manage.sh build")
        print("2. ./docker/manage.sh start")
        print("3. Visit http://localhost:8000")
    else:
        print(f"\n⚠️  Please fix the {total - passed} failed checks before proceeding.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
