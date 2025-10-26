# -*- coding: utf-8 -*-
"""
Utility: Broken url_for() Detector for ELITE Project

Scans all HTML/Jinja templates in the project and detects
any url_for('endpoint') calls that reference endpoints not registered in Flask.
"""

import re
from pathlib import Path
from flask import Flask
from app import app

def extract_all_endpoints(flask_app: Flask):
    """Return a set of all registered Flask endpoints."""
    return {rule.endpoint for rule in flask_app.url_map.iter_rules()}

def find_url_for_calls(template_text: str):
    """Extract all endpoint names from url_for() calls inside a template."""
    pattern = re.compile(r"url_for\(['\"]([\w\.]+)['\"]")
    return pattern.findall(template_text)

def main():
    print("🔍 Scanning templates for broken url_for() references...\n")

    all_endpoints = extract_all_endpoints(app)
    templates_root = Path(__file__).resolve().parent.parent / "app" / "templates"

    broken_references = {}

    for html_file in templates_root.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        for endpoint in find_url_for_calls(text):
            if endpoint not in all_endpoints:
                broken_references.setdefault(html_file, []).append(endpoint)

    if not broken_references:
        print("✅ No broken url_for() references found.\n")
    else:
        print("⚠️ Broken url_for() references detected:\n")
        for file_path, endpoints in broken_references.items():
            print(f"File: {file_path.relative_to(templates_root.parent)}")
            for endpoint in sorted(set(endpoints)):
                print(f"   - {endpoint}")
            print()

    print("✅ Check completed.\n")


if __name__ == "__main__":
    main()
