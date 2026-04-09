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
