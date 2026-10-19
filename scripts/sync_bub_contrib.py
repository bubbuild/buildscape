"""Sync contrib metadata; preserve catalog placement, links, logos, and install choices."""

import argparse
import re
import tomllib
from pathlib import Path

import yaml

REPO = "https://github.com/bubbuild/bub-contrib"
LOGOS = {"bub-docker-env": "/docker.svg", "bub-tapestore-otel": "/opentelemetry.svg"}
GROUPS = {
    "Channels": {
        "bub-discord",
        "bub-dingtalk",
        "bub-feishu",
        "bub-qq",
        "bub-wechat",
        "bub-wecom",
        "bub-slack",
        "bub-acp-server",
        "bub-mcp-server",
    },
    "Tools": {"bub-mcp", "bub-schedule", "bub-web-search"},
}
OVERRIDES = {}  # Package name -> explicitly curated field values, applied after source metadata.


class CatalogDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def sync(source, catalog):
    original = catalog.read_text(encoding="utf-8")
    data = yaml.safe_load(original)
    groups = next(c for c in data["categories"] if c["name"] == "Plugins")[
        "subcategories"
    ]
    existing = [
        item
        for c in data["categories"]
        for g in c["subcategories"]
        for item in g["items"]
        if item["kind"] == "plugin"
    ]
    changed = False
    for manifest in sorted((source / "packages").glob("*/pyproject.toml")):
        project = tomllib.loads(manifest.read_text(encoding="utf-8"))["project"]
        if not project.get("entry-points", {}).get("bub"):
            continue
        name, path = project["name"], manifest.parent.relative_to(source).as_posix()
        key = normalized(name)
        matches = [
            item
            for item in existing
            if normalized(item["name"]) == key
            or (
                item.get("repo_url", "").rstrip("/").removesuffix(".git").lower()
                == REPO.lower()
                and item.get("source_path") == path
            )
        ]
        if len(matches) > 1:
            continue
        if matches:
            item = matches[0]
            if (
                item.get("repo_url", "").rstrip("/").removesuffix(".git").lower()
                != REPO.lower()
            ):
                continue
        else:
            group = next(
                (g for g in GROUPS if key in GROUPS[g]),
                "Storage & Memory"
                if "tapestore" in key or "tape-dataset" in key
                else "Runtime & Workflow",
            )
            item = {
                "name": name,
                "kind": "plugin",
                "logo": LOGOS.get(key, "/plugin.svg"),
                "homepage_url": f"{REPO}/tree/main/{path}",
                "repo_url": REPO,
                "source_path": path,
                "install": f"bub install {name}@main",
                "builtin": False,
            }
            next(g for g in groups if g["name"] == group)["items"].append(item)
            existing.append(item)
            changed = True
        metadata = {}
        description = project.get("description", "").strip()
        if description and description != "Add your description here":
            metadata["description"] = " ".join(description.split())
        elif "description" not in item:
            metadata["description"] = f"Bub plugin: {name}."
        authors = [
            author["name"]
            for author in project.get("authors", [])
            if author.get("name")
        ]
        if authors:
            metadata["author"] = ", ".join(authors)
        if isinstance(project.get("license"), str):
            metadata["license"] = project["license"]
        metadata.update(OVERRIDES.get(key, {}))
        changed |= any(item.get(field) != value for field, value in metadata.items())
        item.update(metadata)
    if changed:
        catalog.write_text(
            yaml.dump(
                data,
                Dumper=CatalogDumper,
                sort_keys=False,
                allow_unicode=True,
                width=88,
            ),
            encoding="utf-8",
        )
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--catalog", type=Path, default=Path("data.yml"))
    args = parser.parse_args()
    if sync(args.source, args.catalog):
        print("Updated contrib catalog.")
