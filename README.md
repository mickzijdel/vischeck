# vischeck

A Claude Code plugin for visual verification of UI changes. Bundles a screenshot CLI, a smart PostToolUse hook, and two skills.

## What's included

| Component | Purpose |
|-----------|---------|
| `bin/screenshot` | Authenticated screenshot CLI via Playwright — auto-added to PATH |
| `hooks/` | PostToolUse hook — reminds Claude to invoke `vischeck:verify` after view edits |
| `skills/verify/` | `vischeck:verify` — screenshot workflow, dark/light mode guidance, playwright-cli testing |
| `skills/setup-auth/` | `vischeck:setup-auth` — sets up the dev auth bypass route (Rails, Django, Flask, FastAPI) |

## Install

```bash
/plugin install github:mickzijdel/vischeck
```

**Prerequisite:** `pip install playwright && playwright install chromium`

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
