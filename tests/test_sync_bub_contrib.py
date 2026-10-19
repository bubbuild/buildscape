import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.sync_bub_contrib import REPO, sync


class SyncTests(unittest.TestCase):
    def test_update_add_deduplicate_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data.yml"
            curated = {
                "name": "BUB_Example",
                "kind": "plugin",
                "description": "Old",
                "repo_url": REPO,
                "source_path": "packages/bub-example",
                "logo": "/mcp.svg",
                "install": "curated install",
            }
            unrelated = {"name": "friend", "kind": "friend", "description": "Keep me"}
            groups = [
                {"name": name, "items": [curated, unrelated] if name == "Tools" else []}
                for name in (
                    "Channels",
                    "Tools",
                    "Runtime & Workflow",
                    "Storage & Memory",
                )
            ]
            catalog.write_text(
                yaml.safe_dump(
                    {"categories": [{"name": "Plugins", "subcategories": groups}]}
                )
            )
            for name in (
                "bub-example",
                "bub-docker-env",
                "bub-tapestore-otel",
                "bub-slack",
            ):
                package = root / "packages" / name
                package.mkdir(parents=True)
                (package / "pyproject.toml").write_text(
                    f'[project]\nname = "{name}"\ndescription = "Updated summary"\nauthors = [{{name = "Author"}}]\n[project.entry-points.bub]\nplugin = "plugin"\n'
                )
            self.assertTrue(sync(root, catalog))
            groups = yaml.safe_load(catalog.read_text())["categories"][0][
                "subcategories"
            ]
            items = {item["name"]: item for group in groups for item in group["items"]}
            self.assertEqual(len(items), 5)
            self.assertEqual(items["BUB_Example"]["description"], "Updated summary")
            self.assertEqual(items["BUB_Example"]["author"], "Author")
            self.assertEqual(items["BUB_Example"]["logo"], "/mcp.svg")
            self.assertEqual(items["BUB_Example"]["install"], "curated install")
            self.assertEqual(items["friend"], unrelated)
            self.assertEqual(items["bub-docker-env"]["logo"], "/docker.svg")
            self.assertEqual(items["bub-tapestore-otel"]["logo"], "/opentelemetry.svg")
            self.assertEqual(groups[0]["items"][0]["name"], "bub-slack")
            before = catalog.read_bytes()
            self.assertFalse(sync(root, catalog))
            self.assertEqual(catalog.read_bytes(), before)
            catalog.write_text(
                catalog.read_text().replace("BUB_Example", "Display name")
            )
            self.assertFalse(sync(root, catalog))

    def test_no_plugins_is_quiet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "data.yml"
            catalog.write_text(
                "categories:\n  - name: Plugins\n    subcategories: []\n"
            )
            before = catalog.read_bytes()
            self.assertFalse(sync(root, catalog))
            self.assertEqual(catalog.read_bytes(), before)
