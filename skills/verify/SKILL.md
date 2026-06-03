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

If `screenshot` redirects to a login page, invoke `Skill(vischeck:setup-auth)` first.

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
