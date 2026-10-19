"""Import Bub contrib plugins while preserving curated catalog fields."""

import argparse
import copy
import io
import json
import re
import tomllib
from pathlib import Path

import yaml as pyyaml
from ruamel.yaml import YAML

REPOSITORY = "https://github.com/bubbuild/bub-contrib"


def package_name(value):
    return re.sub(r"[-_.]+", "-", value).lower()


def source_items(source):
    """Read metadata only; never import or install upstream packages."""
    items = {}
    for manifest in sorted((source / "packages").glob("*/pyproject.toml")):
        project = tomllib.loads(manifest.read_text(encoding="utf-8"))["project"]
        if not project.get("entry-points", {}).get("bub"):
            continue
        name = project["name"]
        key = package_name(name)
        if key in items:
            raise ValueError(f"Duplicate source package: {name}")
        description = project.get("description", "").strip()
        if not description or description == "Add your description here":
            description = f"Bub plugin: {name}."
        path = manifest.parent.relative_to(source).as_posix()
        item = {
            "name": name,
            "description": " ".join(description.split()),
            "kind": "plugin",
            "logo": "/plugin.svg",
            "homepage_url": f"{REPOSITORY}/tree/main/{path}",
            "repo_url": REPOSITORY,
            "install": f"bub install {name}@main",
            "builtin": False,
            "source_path": path,
        }
        authors = [
            author["name"]
            for author in project.get("authors", [])
            if author.get("name")
        ]
        if authors:
            item["author"] = ", ".join(authors)
        license_name = project.get("license")
        if isinstance(license_name, str):
            item["license"] = license_name
        items[key] = item
    if not items:
        raise ValueError("Source contains no Bub plugin packages")
    return items


def write_catalog(catalog, before, after, yaml):
    """Rewrite changed items only, retaining surrounding curated YAML verbatim."""
    text = catalog.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    root = pyyaml.compose(text)
    categories_node = next(
        value for key, value in root.value if key.value == "categories"
    )
    edits = []
    for old_category, category, category_node in zip(
        before["categories"], after["categories"], categories_node.value
    ):
        groups_node = next(
            value for key, value in category_node.value if key.value == "subcategories"
        )
        for old_group, group, group_node in zip(
            old_category["subcategories"], category["subcategories"], groups_node.value
        ):
            items_node = next(
                value for key, value in group_node.value if key.value == "items"
            )
            old_items = old_group.get("items", [])
            items = group.get("items", [])
            for index, (old_item, item) in enumerate(zip(old_items, items)):
                if old_item != item:
                    start = items_node.value[index].start_mark.line
                    end = (
                        items_node.value[index + 1].start_mark.line
                        if index + 1 < len(old_items)
                        else items_node.end_mark.line
                    )
                    output = io.StringIO()
                    yaml.dump([item], output)
                    edits.append((start, end, output.getvalue()))
            if len(items) > len(old_items):
                output = io.StringIO()
                yaml.dump(items[len(old_items) :], output)
                if not old_items:
                    edits.append(
                        (
                            items_node.start_mark.line,
                            items_node.end_mark.line + 1,
                            "items:\n" + output.getvalue(),
                        )
                    )
                else:
                    edits.append(
                        (
                            items_node.end_mark.line,
                            items_node.end_mark.line,
                            output.getvalue(),
                        )
                    )
    for start, end, replacement in sorted(edits, reverse=True):
        lines[start:end] = [
            "        " + line for line in replacement.splitlines(keepends=True)
        ]
    catalog.write_text("".join(lines), encoding="utf-8")


def sync(source, catalog, state_path):
    upstream = source_items(source)
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 1000
    yaml.indent(mapping=2, sequence=4, offset=2)
    data = yaml.load(catalog.read_text(encoding="utf-8"))
    state = (
        json.loads(state_path.read_text(encoding="utf-8"))
        if state_path.exists()
        else {}
    )
    previous_data = copy.deepcopy(data)
    previous_state = copy.deepcopy(state)
    categories = data["categories"]
    plugins = next(category for category in categories if category["name"] == "Plugins")
    by_name = {}
    by_path = {}
    for category in categories:
        for group in category.get("subcategories", []):
            for item in group.get("items", []):
                if item.get("kind") != "plugin":
                    continue
                by_name.setdefault(package_name(item["name"]), []).append(item)
                repository = (
                    item.get("repo_url", "").rstrip("/").removesuffix(".git").lower()
                )
                if repository == REPOSITORY.lower():
                    by_path.setdefault(item.get("source_path"), []).append(item)

    for key, generated in upstream.items():
        matches = by_name.get(key, []).copy()
        for item in by_path.get(generated["source_path"], []):
            if all(item is not match for match in matches):
                matches.append(item)
        if matches:
            # Never choose between existing duplicates or claim curated data.
            if len(matches) != 1 or key not in state:
                continue
            item = matches[0]
            baseline = state[key]
            if (
                item.get("repo_url") != REPOSITORY
                or item.get("source_path") != baseline["source_path"]
            ):
                continue
            for field, value in generated.items():
                if (
                    field in baseline
                    and item.get(field) == baseline[field]
                    or field not in baseline
                    and field not in item
                ):
                    item[field] = value
                    baseline[field] = value
        elif key not in state:
            # State also remembers deliberate catalog deletions; do not recreate them.
            group_name = (
                "Storage & Memory"
                if "tapestore" in key or "tape-dataset" in key
                else "Runtime & Workflow"
            )
            group = next(
                group
                for group in plugins["subcategories"]
                if group["name"] == group_name
            )
            group.setdefault("items", []).append(generated)
            state[key] = generated.copy()
    if data != previous_data:
        write_catalog(catalog, previous_data, data, yaml)
    if state != previous_state:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return data != previous_data or state != previous_state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Local bub-contrib checkout")
    parser.add_argument("--catalog", type=Path, default=Path("data.yml"))
    parser.add_argument(
        "--state", type=Path, default=Path(".github/bub-contrib-sync.json")
    )
    args = parser.parse_args()
    if sync(args.source, args.catalog, args.state):
        print("Updated Bub contrib catalog data.")


if __name__ == "__main__":
    main()
