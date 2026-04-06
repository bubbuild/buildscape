# Bub Landscape

Landscape project for the Bub ecosystem, generated from the official `landscape2` CLI and then customized for Bub.

## Requirements

- `landscape2` in `PATH`

Install the CLI with the upstream installer:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/cncf/landscape2/releases/download/v1.1.0/landscape2-installer.sh | sh
```

## Local workflow

Validate the source files:

```bash
cd landscape
landscape2 validate data --data-file data.yml
landscape2 validate settings --settings-file settings.yml
landscape2 validate guide --guide-file guide.yml
landscape2 validate games --games-file games.yml
```

Build the static site:

```bash
landscape2 build \
  --data-file data.yml \
  --settings-file settings.yml \
  --guide-file guide.yml \
  --games-file games.yml \
  --logos-path logos \
  --output-dir build

./scripts/postbuild.sh
```

Serve it locally:

```bash
landscape2 serve --landscape-dir build
```

## Data conventions

- The landscape is a curated index, not a complete registry of every plugin package or skill payload.
- `Plugins` should contain the full official Bub plugin surface: all plugin packages from `bubbuild/bub-contrib` plus standalone Bub-hosted plugin repositories such as `bub-xiaoai` and `bub-folotoy`.
- Built-in Bub skills belong in `Built-in Skills / Core Operations` and should stay on the official first page.
- External or curated skills should use remote sources only and belong in `Selected Skills / Python Craft`.
- `Selected Skills` is list-only metadata: keep links to the upstream reading and installation surfaces, but do not mirror or maintain skill contents in this repo.
- Downstream-only plugin packages should usually be linked from their parent distribution or project item instead of becoming first-class plugin entries.
- Prefer a minimal metadata contract for selected entries:

```yaml
repo_url: https://github.com/example/project
extra:
  documentation_url: https://example.com/docs
  other_links:
    - name: source
      url: https://github.com/example/project/tree/main/path
  annotations:
    "bubbuild.io/hosted": "true"
    "bubbuild.io/kind": "plugin"
```
- For machine-readable ownership, set:

```yaml
extra:
  annotations:
    "bubbuild.io/hosted": "true"
```

Use `"false"` for plugins or skills hosted outside the Bub umbrella.

For selected remote skills, prefer:

- `homepage_url`: the public remote reading surface
- `repo_url`: the upstream repository
- `extra.documentation_url`: the docs index or library homepage

## Visual tiers

- Keep content classification and visual emphasis separate.
- Use featured items without labels so larger cards indicate Bub-hosted or Bub-selected items only through size.
- Third-party general items stay as normal-sized cards.
- Keep logos mostly icon-shaped instead of text-shaped so the card title can carry recognition.
- `theme/custom.css` and `theme/custom.js` add item names back to grid cards after each build.

## Deployment note

The default `settings.yml` uses `http://127.0.0.1:8000` so the site builds and serves locally without extra edits. Change `url` before deploying to a real domain.

This repository also includes [`.github/workflows/deploy-pages.yml`](./.github/workflows/deploy-pages.yml), which builds and publishes the site to GitHub Pages on every push to `main`.

For Pages deployment, the workflow treats the repository-root [`CNAME`](./CNAME) file as the single source of truth. It reads the domain from that file, rewrites `settings.yml` at build time with the corresponding `https://...` URL, and copies the same `CNAME` file into the published artifact.

The current configured Pages domain is `hub.bub.build`.
