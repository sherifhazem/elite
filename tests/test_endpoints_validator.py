# -*- coding: utf-8 -*-
"""
Endpoint Validator — Ensures all Flask endpoints are registered, unique, and buildable.
"""

from flask import url_for
from app import app


def test_registered_endpoints():
    """Iterate all registered routes and check for conflicts or build issues."""

    seen = {}
    duplicates = []
    errors = []

    print("\n" + "=" * 80)
    print("🔍  Flask Endpoint Validation Report")
    print("=" * 80)

    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        blueprint = endpoint.split(".")[0] if "." in endpoint else "global"
        url = str(rule)

        # Track duplicates
        if endpoint in seen:
            duplicates.append((endpoint, url))
        else:
            seen[endpoint] = url

        # Try building the URL safely
        try:
            url_for(endpoint, **{arg: 1 for arg in rule.arguments})
        except Exception as exc:
            errors.append((endpoint, str(exc)))

        print(f"✅ {endpoint:40} | {url}")

    print("\n" + "-" * 80)
    if duplicates:
        print("⚠️  Duplicate endpoints detected:")
        for ep, path in duplicates:
            print(f"   - {ep:30} @ {path}")
    else:
        print("✅  No duplicate endpoints found.")

    if errors:
        print("\n❌  Build errors detected:")
        for ep, err in errors:
            print(f"   - {ep:30} → {err}")
    else:
        print("\n✅  All endpoints built successfully.")

    print("=" * 80 + "\n")

    # Ensure the test fails if there are duplicates or build errors
    assert not duplicates, "Duplicate endpoints found."
    assert not errors, "Some endpoints failed to build with url_for()."
