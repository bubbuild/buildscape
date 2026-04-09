#!/usr/bin/env python3
"""Build script for hub.bub.build — generates a static page from data.yml + Jinja2 templates."""

import json
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
LOGOS_DIR = ROOT / "logos"
DIST_DIR = ROOT / "dist"

VALID_KINDS = {"plugin", "skill", "distribution", "friend"}

KNOWN_FIELDS = {
    "name", "description", "kind", "logo",
    "homepage_url", "repo_url", "docs_url",
    "author", "license", "install",
    "builtin", "source_path", "skill_file",
    "bundled_plugins",
}


def load_data():
    with open(ROOT / "data.yml") as f:
        return yaml.safe_load(f)


def validate(categories):
    errors = []
    for cat in categories:
        for sub in cat.get("subcategories", []):
            for item in sub.get("items", []):
                loc = f"{cat['name']}/{sub['name']}/{item.get('name', '?')}"
                if not item.get("name"):
                    errors.append(f"{loc}: missing 'name'")
                if not item.get("description"):
                    errors.append(f"{loc}: missing 'description'")
                kind = item.get("kind")
                if kind not in VALID_KINDS:
                    errors.append(f"{loc}: invalid kind '{kind}', expected one of {VALID_KINDS}")
                unknown = set(item.keys()) - KNOWN_FIELDS
                if unknown:
                    errors.append(f"{loc}: unknown fields {unknown}")
    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


def build():
    data = load_data()
    categories = data.get("categories", [])

    validate(categories)

    total_items = sum(
        len(sub.get("items", []))
        for cat in categories
        for sub in cat.get("subcategories", [])
    )

    cat_counts = {}
    for cat in categories:
        cat_counts[cat.get("name", "")] = sum(
            len(sub.get("items", []))
            for sub in cat.get("subcategories", [])
        )

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    template = env.get_template("index.html")
    html = template.render(
        title="Bub Hub — Ecosystem Directory",
        description="Ecosystem directory for Bub plugins, skills, distributions, and friends.",
        categories=categories,
        total_items=total_items,
        cat_counts_json=json.dumps(cat_counts),
    )

    DIST_DIR.mkdir(exist_ok=True)
    (DIST_DIR / "index.html").write_text(html)

    # Copy logos
    dist_logos = DIST_DIR / "logos"
    if LOGOS_DIR.is_dir():
        if dist_logos.exists():
            shutil.rmtree(dist_logos)
        shutil.copytree(LOGOS_DIR, dist_logos)

    print(f"Built hub → {DIST_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
