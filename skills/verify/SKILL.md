---
name: verify
description: Visually verify UI changes by taking authenticated screenshots of the local dev server. Use after editing any view, template, component, or layout file. If screenshot redirects to a login page, invoke vischeck:setup-auth first.
---

# vischeck:verify

Use the `screenshot` CLI to visually verify UI changes against a running dev server. Always Read the saved image after taking a screenshot.

## When to use

After editing any view, template, component, or layout file:
1. Take a screenshot and Read the image to check it visually
2. For interactive elements (forms, buttons, inputs), also test the interaction with playwright-cli

`screenshot` auto-detects whether the page needs auth — no flag required for public pages.
It exits non-zero (while still saving the image) when the capture is an HTTP error or an
unresolved auth wall, and prints what happened to stderr. If it reports that the page requires
auth but the auth route returned 404, invoke `Skill(vischeck:setup-auth)` to add the dev auth
route, then retry.

## Multiple pages at once

When a change touches several pages (or you want to re-screenshot the same set while iterating),
use the `screenshots` (plural) batch tool instead of calling `screenshot` repeatedly. It captures
every page in parallel — reusing the exact same auth/error behaviour — and writes them plus an
`index.html` grid to `tmp/screenshots/batch_<timestamp>/`:

```bash
screenshots / /dashboard /news   # capture exactly these paths
screenshots                      # use ./screenshots.yml (a consistent saved list)
```

Positional paths always win; with no paths it reads `screenshots.yml` (auto-discovered in cwd).
Keep a `screenshots.yml` in the project to re-verify the same page set every iteration (entries are
path strings or mappings with per-entry overrides like `dark`/`width`/`height`). After a batch, Read
the individual PNGs in the batch dir to inspect each page; the run exits non-zero if any page failed.

Define reusable **groups** in `screenshots.yml` (e.g. `smoke`, `admin`, `users`) and capture one with
`screenshots --group smoke`, several with `screenshots -g smoke,admin`, all with `--all`, or list them
with `screenshots --list`. A group can carry group-level defaults (e.g. a whole `admin` group `dark:
true`). This lets you keep coherent, named slices to re-screenshot while iterating on a section.

## Dark / light mode

Check this project's CLAUDE.md for any mention of dark mode or light mode:
- If dark mode **is** mentioned: take one screenshot in each mode (`screenshot <path>` and `screenshot <path> --dark`)
- If dark/light mode is **not mentioned**: take a single screenshot, then note to the user that they may want to add a line to CLAUDE.md documenting whether this project supports dark/light mode (e.g. `## UI: This app supports dark mode and light mode`)

## CLI reference

```bash
screenshot /path                           # authenticated screenshot (default port 3000)
screenshot /path --dark                    # dark color scheme
screenshot /path --width 375 --height 812  # mobile viewport
screenshot /path --full-page               # full scrollable page
screenshot /path --port 8080               # custom port
screenshot /path --no-auth                 # skip authentication (public pages)
screenshot /path --auth-url "/login?token={token}&next={path}"  # custom auth URL template

screenshots / /dashboard /news             # batch: capture several paths at once
screenshots                                # batch: use ./screenshots.yml
screenshots --dark                         # batch: dark scheme for all pages
screenshots --group smoke                  # batch: capture a named group
screenshots -g smoke,admin                 # batch: union of several groups
screenshots --list                         # batch: list defined groups
```

Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`). Screenshots save to `tmp/screenshots/` in the current working directory.

## Desktop + mobile

For significant layout changes, take both desktop (default 1280×720) and mobile (`--width 375 --height 812`) screenshots.

## Interactive testing with playwright-cli

For forms, buttons, and Stimulus controllers — don't just screenshot, actually use the feature:

```bash
# Authenticate and navigate
playwright-cli open "http://localhost:3000/dev_auth/login?token=claude-screenshot-token&redirect_to=/path"
playwright-cli state-save dev-auth.json

# Restore auth and use the page
playwright-cli state-load dev-auth.json
playwright-cli goto http://localhost:3000/path
playwright-cli snapshot          # see element refs
playwright-cli fill e5 "value"   # fill an input
playwright-cli click e3          # click a button
playwright-cli screenshot        # capture result
playwright-cli close
```
