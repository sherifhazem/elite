# -*- coding: utf-8 -*-
"""
Utility: Endpoint Consistency Checker for ELITE Project

This script compares actual Flask endpoints with documented ones
in app/PROJECT_MAP.md to detect missing or duplicated routes.
"""

import re
from pathlib import Path

from flask import Flask

from app import create_app

def extract_documented_endpoints():
    """Read endpoints from PROJECT_MAP.md and return as a set."""
    map_path = Path(__file__).resolve().parent.parent / "app" / "PROJECT_MAP.md"
    documented = set()
    pattern = re.compile(r"^- ([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)")
    if map_path.exists():
        for line in map_path.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line.strip())
            if match:
                documented.add(match.group(1))
    return documented


def list_actual_endpoints(flask_app: Flask):
    """Return all registered endpoints from Flask app.url_map."""
    return {rule.endpoint for rule in flask_app.url_map.iter_rules()}


def main():
    app = create_app()
    documented = extract_documented_endpoints()
    actual = list_actual_endpoints(app)

    print("🔍 Checking Flask Endpoints Consistency...\n")

    missing = documented - actual
    extra = actual - documented
    duplicates = {e for e in actual if list(actual).count(e) > 1}

    if not missing and not extra:
        print("✅ All endpoints are consistent with PROJECT_MAP.md\n")
    else:
        if missing:
            print("⚠️ Missing endpoints (documented but not found):")
            for e in sorted(missing):
                print("   -", e)
        if extra:
            print("\n⚠️ Extra endpoints (exist in code but not documented):")
            for e in sorted(extra):
                print("   -", e)

    if duplicates:
        print("\n🚫 Duplicated endpoints found:")
        for e in sorted(duplicates):
            print("   -", e)

    print("\n✅ Check completed.\n")


if __name__ == "__main__":
    main()
