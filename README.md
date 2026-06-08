# vischeck

A Claude Code plugin for visual verification of UI changes. Bundles a screenshot CLI, a smart PostToolUse hook, and two skills.

## What's included

| Component | Purpose |
|-----------|---------|
| `bin/screenshot` | Authenticated screenshot CLI via Playwright — auto-added to PATH |
| `bin/screenshots` | Multi-page batch CLI — captures a list of pages in one go and builds an `index.html` grid |
| `hooks/` | PostToolUse hook — reminds Claude to invoke `vischeck:verify` after view edits |
| `skills/verify/` | `vischeck:verify` — screenshot workflow, dark/light mode guidance, playwright-cli testing |
| `skills/setup-auth/` | `vischeck:setup-auth` — sets up the dev auth bypass route (Rails, Django, Flask, FastAPI) |

## Install

```bash
/plugin install github:mickzijdel/vischeck
```

**Prerequisite:** `pip install playwright && playwright install chromium`
(`pip install pyyaml` too if you want to drive the multi-page tool from a `screenshots.yml`)

## Usage

The `screenshot` command is available in any Claude Code session once the plugin is active:

```bash
screenshot /dashboard                           # authenticated screenshot
screenshot /dashboard --dark                    # dark color scheme
screenshot /dashboard --width 375 --height 812  # mobile viewport
screenshot /dashboard --full-page               # full scrollable page
screenshot /dashboard --port 8080               # non-default port
screenshot /dashboard --no-auth                 # public page, skip login
screenshot /dashboard --auth-url "/login?token={token}&next={path}"  # custom auth URL
```

Screenshots save to `tmp/screenshots/` in the current working directory. Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`).

### Multi-page screenshots

`screenshots` (plural) captures a whole list of pages in one batch — useful for re-screenshotting the same set while iterating, or grabbing several affected pages at once. It invokes the single `screenshot` tool per page (in parallel), so the same auto-auth, error handling, and dark-mode behaviour applies. All images plus an `index.html` grid land in `tmp/screenshots/batch_<timestamp>/`.

```bash
screenshots / /dashboard /news       # capture exactly these paths
screenshots                          # use ./screenshots.yml (auto-discovered)
screenshots --config pages.yml       # explicit config file
screenshots --dark                   # dark scheme for all pages
screenshots --workers 8              # more parallelism
```

**Path resolution:** positional paths always win. With no paths, it auto-discovers `screenshots.yml`, `.screenshots.yml`, or `config/screenshots.yml` in the current directory. With neither, it prints the expected format and exits non-zero (it never guesses a page list).

Create a `screenshots.yml` to keep a consistent set of pages. Each entry is a plain path string, or a mapping with per-entry overrides; top-level keys are global defaults (CLI flags override them for all pages):

```yaml
# optional global defaults
port: 3000
width: 1280
height: 720
pages:
  - /                     # string form
  - /dashboard
  - path: /dashboard      # mapping form, per-entry overrides
    dark: true            #   capture this one in dark mode too
  - path: /mobile
    width: 375            #   override viewport for just this page
    height: 812
    full_page: true
    no_auth: true
```

Per-entry override keys: `dark`, `full_page`, `width`, `height`, `no_auth`, `auth_url`. The dark variant of a path gets a `_dark` filename suffix so it doesn't collide with the light one. The command exits non-zero if any page fails to capture.

## Dev auth

The `screenshot` tool authenticates via a lightweight dev-only bypass route. To set it up in your project, ask Claude to invoke `vischeck:setup-auth` — it will ask for your permission and then implement the appropriate route for your framework (Rails, Django, Flask, or FastAPI).

## Hook behaviour

After every `Write` or `Edit` on a view/template file, Claude is reminded to invoke `vischeck:verify`. The hook also:

- Checks `CLAUDE.md` for dark/light mode mentions — if found, suggests testing both; if absent, suggests documenting it
- Detects interactive elements (forms, buttons) and suggests playwright-cli testing

## Dark / light mode

Add a line to your project's `CLAUDE.md` so the hook gives the right advice:

```markdown
## UI: This app supports dark mode and light mode
```
