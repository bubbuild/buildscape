# Bub Hub

Ecosystem directory for [Bub](https://bub.build) plugins, skills, distributions, and friends.

**Live at** [hub.bub.build](https://hub.bub.build)

## Structure

```
hub/
├── build.py                # Static site generator (Jinja2)
├── data.yml                # All ecosystem items (add new entries here)
├── logos/                   # Logo assets (copied to dist/logos/ on build)
├── templates/
│   ├── base.html            # Base layout
│   ├── index.html           # Main page template
│   ├── style.css            # Terminal-style CSS (dark theme)
│   ├── hub.js               # Client-side filtering & search
│   └── partials/
│       └── card.html        # Card component
├── dist/                    # Generated output
├── pyproject.toml           # Project metadata & dependencies
└── uv.lock
```

## Usage

```bash
# Install dependencies
uv sync

# Build the site
uv run python build.py
```

## Adding items

Edit `data.yml`. All items share a unified schema:

```yaml
categories:
  - name: Plugins             # or Skills, Distributions, Friends
    subcategories:
      - name: Channels        # grouping within the category
        items:
          - name: my-plugin
            description: What it does.
            kind: plugin      # plugin | skill | distribution | friend
            logo: my-plugin.svg
            homepage_url: https://...
            repo_url: https://github.com/...
            install: "uv add my-plugin --git https://github.com/..."
```

### Field reference

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | str | ✅ | Display name |
| `description` | str | ✅ | One-line summary |
| `kind` | enum | ✅ | `plugin` \| `skill` \| `distribution` \| `friend` |
| `logo` | str | | Filename in `logos/` |
| `homepage_url` | str | | Primary link |
| `repo_url` | str | | Source repository |
| `docs_url` | str | | Documentation URL |
| `author` | str | | Author or organization |
| `license` | str | | SPDX identifier |
| `install` | str | | Install command |
| `builtin` | bool | | Shipped with Bub core |
| `source_path` | str | | Path within a monorepo (repo link renders as `repo_url/tree/main/{source_path}`) |
| `skill_file` | str | | URL to SKILL.md |
| `bundled_plugins` | list | | `[{name, url}]` for distributions (max 3 shown) |

Build validates required fields, `kind` enum, and rejects unknown fields.

## Bub contrib updates

[Sync Bub contrib](.github/workflows/sync-bub-contrib.yml) reads `packages/*/pyproject.toml` from `bubbuild/bub-contrib` main each Monday at 03:41 UTC, or on manual dispatch. It imports packages declaring a `bub` entry point into the existing Plugins groups. It reads metadata without executing upstream code. Package descriptions, authors, SPDX license strings, source links, and `bub install NAME@main` commands supply new entries; missing descriptions get a package-name fallback. New entries use the existing `logos/plugin.svg` until a maintainer selects a project logo. Skills, third-party entries, existing logos, and existing curated package entries stay under manual maintenance.

The sync deduplicates package names (including case, hyphen, underscore, and dot variants) and contrib source paths across groups. It records only newly imported entries in `.github/bub-contrib-sync.json`. Later runs update fields that still match their last generated values; manual overrides and deleted entries stay untouched. Missing upstream packages remain in the catalog for manual retirement. Keep the state file when editing or moving generated entries.

Changed data passes sync tests and the site build before the workflow opens a draft PR on `catalog/bub-contrib`. An open sync PR pauses further updates so reviewer edits survive. Unchanged runs create no commit, PR, or comment. Maintainers merge updates manually. The repository must allow GitHub Actions to create pull requests in **Settings > Actions > General > Workflow permissions**; the workflow uses `LANDING_GITHUB_TOKEN` when configured, otherwise `github.token`, with contents and pull request write permissions. This matches Landing and Republic publishing conventions. PRs created with `github.token` do not trigger ordinary PR workflows, so the sync runs validation before publication. Schedules become active after this workflow reaches the default branch.

To reproduce locally with a separate contrib checkout:

```bash
uv sync --frozen
uv run --frozen python scripts/sync_bub_contrib.py ../bub-contrib
uv run --frozen python -m unittest discover -s tests
uv run --frozen python build.py
```

For a workflow dry run, manually dispatch **Sync Bub contrib** with `publish` disabled. Publication also requires running on `main`.

The deterministic sync requires no model or admission credentials. If a Landing runtime is added, reuse secret `LANDING_API_KEY` and variables `LANDING_MODEL`, `LANDING_API_BASE`, and `LANDING_COMPLETION_ARGS`, plus optional secret `LANDING_ADMISSION_TOKEN` for separate admission credentials. Keep these names consistent with Landing and Republic; GitHub secret metadata cannot supply secret values for copying between repositories.
