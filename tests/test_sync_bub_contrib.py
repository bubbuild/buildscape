import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.sync_bub_contrib import REPOSITORY, sync

ROOT = Path(__file__).resolve().parents[1]


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source"
        self.catalog = self.root / "data.yml"
        self.state = self.root / "state.json"
        self.catalog.write_text(
            "# Curated catalog\ncategories:\n"
            "  - name: Plugins\n    subcategories:\n"
            "      - name: Runtime & Workflow\n        items: []\n"
            "      - name: Storage & Memory\n        items: []\n",
            encoding="utf-8",
        )
        self.package()

    def package(
        self, description="Example plugin", name="bub-example", entry_point=True
    ):
        package = self.source / "packages" / name
        package.mkdir(parents=True, exist_ok=True)
        manifest = (
            f'[project]\nname = "{name}"\ndescription = "{description}"\n'
            'authors = [{name = "A contributor"}]\nlicense = "MIT"\n'
        )
        if entry_point:
            manifest += '[project.entry-points.bub]\nexample = "example.plugin"\n'
        (package / "pyproject.toml").write_text(manifest, encoding="utf-8")

    def run_sync(self):
        return sync(self.source, self.catalog, self.state)

    def items(self):
        data = yaml.safe_load(self.catalog.read_text(encoding="utf-8"))
        return [
            item
            for category in data["categories"]
            for group in category["subcategories"]
            for item in group["items"]
        ]

    def test_initial_import_and_quiet_byte_identical_repeat(self):
        self.assertTrue(self.run_sync())
        item = self.items()[0]
        self.assertEqual(item["source_path"], "packages/bub-example")
        self.assertEqual(item["repo_url"], REPOSITORY)
        self.assertEqual(item["install"], "bub install bub-example@main")
        self.assertEqual(item["author"], "A contributor")
        self.assertEqual(item["license"], "MIT")
        self.assertTrue((ROOT / "logos" / item["logo"].lstrip("/")).is_file())
        before = self.catalog.read_bytes(), self.state.read_bytes()
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/sync_bub_contrib.py"),
                str(self.source),
                "--catalog",
                str(self.catalog),
                "--state",
                str(self.state),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(before, (self.catalog.read_bytes(), self.state.read_bytes()))

    def test_updates_generated_fields_and_preserves_overrides(self):
        self.run_sync()
        text = self.catalog.read_text(encoding="utf-8")
        self.catalog.write_text(
            text.replace("/plugin.svg", "/mcp.svg # Maintainer-selected logo"),
            encoding="utf-8",
        )
        self.package("Changed upstream summary")
        self.assertTrue(self.run_sync())
        item = self.items()[0]
        self.assertEqual(item["description"], "Changed upstream summary")
        self.assertEqual(item["logo"], "/mcp.svg")
        self.assertIn("# Maintainer-selected logo", self.catalog.read_text())
        text = self.catalog.read_text(encoding="utf-8")
        self.catalog.write_text(
            text.replace("Changed upstream summary", "Curated summary"),
            encoding="utf-8",
        )
        self.package("Another upstream summary")
        self.assertFalse(self.run_sync())
        self.assertEqual(self.items()[0]["description"], "Curated summary")

    def test_curated_entries_and_comments_remain_verbatim(self):
        curated = (
            "          # Keep this comment and formatting\n"
            "          - name: BUB_Example\n            description: 'Curated summary'\n"
            "            kind: plugin\n            logo: /mcp.svg\n"
        )
        self.catalog.write_text(
            self.catalog.read_text().replace(
                "        items: []", "        items:\n" + curated, 1
            )
        )
        before = self.catalog.read_bytes()
        self.assertFalse(self.run_sync())
        self.assertEqual(self.catalog.read_bytes(), before)
        self.package(name="bub-other")
        self.assertTrue(self.run_sync())
        self.assertIn(curated, self.catalog.read_text())
        self.assertEqual(len(self.items()), 2)
        self.assertNotIn("bub-example", json.loads(self.state.read_text()))

    def test_source_path_deduplicates_renamed_curated_entry(self):
        self.run_sync()
        self.catalog.write_text(
            self.catalog.read_text().replace("name: bub-example", "name: Friendly name")
        )
        self.state.unlink()
        self.assertFalse(self.run_sync())
        self.assertEqual(len(self.items()), 1)

    def test_removed_package_is_retained_and_manual_deletion_is_respected(self):
        self.run_sync()
        self.package(name="bub-other")
        self.run_sync()
        (self.source / "packages/bub-example/pyproject.toml").unlink()
        self.assertFalse(self.run_sync())
        self.assertEqual(len(self.items()), 2)
        # Restore source, then deliberately remove the corresponding catalog item.
        self.package()
        text = self.catalog.read_text()
        start = text.index("          - name: bub-example")
        end = text.index("          - name: bub-other")
        self.catalog.write_text(text[:start] + text[end:])
        self.assertFalse(self.run_sync())
        self.assertEqual([item["name"] for item in self.items()], ["bub-other"])

    def test_ignores_non_plugins_and_groups_storage(self):
        self.package(name="utility", entry_point=False)
        self.package(name="bub-tapestore-example")
        self.run_sync()
        groups = yaml.safe_load(self.catalog.read_text())["categories"][0][
            "subcategories"
        ]
        self.assertEqual(
            [item["name"] for item in groups[1]["items"]], ["bub-tapestore-example"]
        )
        self.assertEqual(len(self.items()), 2)

    def test_invalid_or_duplicate_source_fails_before_writing(self):
        self.package(name="BUB_Example")
        before = self.catalog.read_bytes()
        with self.assertRaisesRegex(ValueError, "Duplicate source package"):
            self.run_sync()
        self.assertEqual(self.catalog.read_bytes(), before)
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
