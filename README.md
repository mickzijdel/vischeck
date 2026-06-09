# vischeck

A Claude Code plugin for visual verification of UI changes. Bundles a screenshot CLI, a smart PostToolUse hook, and two skills.

## What's included

| Component | Purpose |
|-----------|---------|
| `bin/screenshot` | Authenticated screenshot CLI via Playwright — auto-added to PATH |
| `bin/screenshots` | Multi-page batch CLI — captures a list of pages in one go and builds an `index.html` grid |
| `hooks/` | PostToolUse hook — reminds Claude to invoke `vischeck:verify` after view edits |
| `skills/verify/` | `vischeck:verify` — screenshot workflow + a strict review rubric (zoom into the component, compare against the house style, report findings by severity), dark/light mode guidance, playwright-cli testing |
| `skills/setup-auth/` | `vischeck:setup-auth` — sets up the dev auth bypass route (Rails, Django, Flask, FastAPI) |

## Install

```bash
/plugin install github:mickzijdel/vischeck
```

**Prerequisite:** [`uv`](https://docs.astral.sh/uv/). The `bin/` scripts use [PEP 723 inline script metadata](https://peps.python.org/pep-0723/), so `uv` installs their Python dependencies (`playwright`, `pyyaml`) automatically on first run — no `pip install` or virtualenv needed. Playwright's browser binary is a one-time download:

```bash
uvx playwright install chromium
```

## Usage

The `screenshot` command is available in any Claude Code session once the plugin is active:

```bash
screenshot /dashboard                           # authenticated screenshot
screenshot /dashboard --dark                    # dark color scheme
screenshot /dashboard --width 375 --height 812  # mobile viewport
screenshot /dashboard --full-page               # full scrollable page
screenshot /dashboard --selector ".user-card"   # capture just one element, for close inspection
screenshot /dashboard --port 8080               # non-default port
screenshot /dashboard --no-auth                 # public page, skip login
screenshot /dashboard --auth-url "/login?token={token}&next={path}"  # custom auth URL
```

Screenshots save to `tmp/screenshots/` in the current working directory. Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`).

### Multi-page screenshots

`screenshots` (plural) captures a whole list of pages in one batch — useful for re-screenshotting the same set while iterating, or grabbing several affected pages at once. It invokes the single `screenshot` tool per page (in parallel), so the same auto-auth, error handling, and dark-mode behaviour applies. All images plus an `index.html` grid land in `tmp/screenshots/batch_<timestamp>/`.

```bash
screenshots / /dashboard /news       # capture exactly these paths
screenshots                          # use ./screenshots.yml top-level `pages:`
screenshots --group smoke            # capture a named group
screenshots -g smoke,admin           # union of several groups (repeatable too)
screenshots --all                    # union of every group
screenshots --list                   # list the groups defined in the config
screenshots --config pages.yml       # explicit config file
screenshots --dark                   # dark scheme for all pages
screenshots --selector ".card"       # capture the same element on every page
screenshots --workers 8              # more parallelism
```

**Selection:** positional paths always win. Otherwise `--group` / `--all` / `--list` operate on the config's `groups:`, and with no selection the config's top-level `pages:` list is used. The config file is auto-discovered as `screenshots.yml`, `.screenshots.yml`, or `config/screenshots.yml` in the current directory. With nothing to capture it prints the available groups (or the format help) and exits non-zero — it never guesses a page list.

Create a `screenshots.yml` to keep a consistent set of pages. Each entry is a plain path string, or a mapping with per-entry overrides; top-level keys are global defaults:

```yaml
# optional global defaults
port: 3000
width: 1280
height: 720

pages:                    # default set, used when no group is selected
  - /                     # string form
  - path: /dashboard      # mapping form, per-entry overrides
    dark: true            #   capture this one in dark mode too
  - path: /mobile
    width: 375            #   override viewport for just this page
    height: 812
```

### Reusable groups

Define named `groups:` to re-screenshot a coherent slice without retyping paths — e.g. a `smoke` set for the public site, an `admin` set, a `users` set. A group is either a **list** of page entries, or a **mapping** with `pages:` plus group-level option defaults (e.g. the whole `admin` group in dark mode or behind a different auth URL):

```yaml
groups:
  smoke:                  # list form
    - /
    - /shows
    - /news
  admin:                  # mapping form with group-level defaults
    dark: true
    auth_url: "/admin_login?token={token}&redirect_to={path}"
    pages:
      - /admin
      - /admin/users
  users:
    - /users/sign_in
    - path: /users/profile
      dark: true
```

Select with `screenshots --group admin`, combine with `screenshots -g smoke,users` (or `--all`), and enumerate with `screenshots --list`. Overlapping paths across selected groups are captured once.

**Option precedence** (most specific wins): per-entry override → group-level default → CLI flag → top-level global → built-in default. Override keys: `dark`, `full_page`, `width`, `height`, `no_auth`, `auth_url`, `selector`. The dark variant of a path gets a `_dark` filename suffix so it doesn't collide with the light one. The command exits non-zero if any page fails to capture.

## Dev auth

The `screenshot` tool authenticates via a lightweight dev-only bypass route. To set it up in your project, ask Claude to invoke `vischeck:setup-auth` — it will ask for your permission and then implement the appropriate route for your framework (Rails, Django, Flask, or FastAPI).

## Hook behaviour

After every `Write` or `Edit` on a view/template file, Claude is reminded to invoke `vischeck:verify`. A file counts as a view if **either**:

- its extension is a known template/markup type (`.erb`, `.html`, `.jsx`, `.tsx`, `.vue`, `.svelte`, `.hbs`, `.ejs`, `.pug`, `.liquid`, `.blade.php`, `.twig`, …), **or**
- it lives in a `views/`, `components/`, `pages/`, `layouts/`, or `partials/` directory (or `app/javascript/controllers/`).

Files in a `templates/` directory are matched by **extension only** — a `templates/` folder routinely holds config/data files (Helm/CI YAML, Pkl config templates), so matching it by path alone misfired on `.yml`/`.pkl` and the like. Real HTML templates in there still fire via their extension.

The hook also:

- Checks `CLAUDE.md` for dark/light mode mentions — if found, suggests testing both; if absent, suggests documenting it
- Detects interactive elements (forms, buttons) and suggests playwright-cli testing

## Dark / light mode

Add a line to your project's `CLAUDE.md` so the hook gives the right advice:

```markdown
## UI: This app supports dark mode and light mode
```

## Development

Tooling is managed with [mise](https://mise.jdx.dev) and pre-commit hooks run via
[hk](https://hk.jdx.dev). The toolchain is spec'd `"latest"` in `mise.toml` and pinned
reproducibly (resolved versions + checksums) in the committed `mise.lock`.

```bash
mise install     # provision hk, gitleaks, shellcheck, shfmt, uv, ruff, node
hk install       # install the git pre-commit hook (lint + secret-scan + dead-code/duplication)
hk run check     # the same full suite under one name (what CI runs)
uv run pytest    # run the test suite for the bundled scripts
```

**Built with:** the `bin/` scripts are self-contained [PEP 723](https://peps.python.org/pep-0723/)
Python (`requires-python >= 3.11`) — `bin/screenshot` uses **Playwright**, `bin/screenshots`
uses **PyYAML** — installed on first run by `uv`, plus the bash hook `bin/vischeck-hook`. All
runtime deps are unpinned (resolved to latest by `uv`); the dev toolchain versions are pinned
in `mise.lock`. Linting: `shellcheck`/`shfmt` (shell), `ruff` (Python), `gitleaks` (secrets),
`vulture` + `jscpd` (audits, now on pre-commit too — `jscpd` skips gracefully when offline) —
see `hk.pkl` and `.github/workflows/ci.yml`.
