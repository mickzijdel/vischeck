---
name: verify
description: Visually verify UI changes by taking authenticated screenshots of the local dev server. Use after editing any view, template, component, or layout file. If screenshot redirects to a login page, invoke vischeck:setup-auth first.
---

# vischeck:verify

Use the `screenshot` CLI to visually verify UI changes against a running dev server. Always Read the saved image after taking a screenshot — then **review it like a critical designer, not a rubber stamp.**

## When to use

After editing any view, template, component, or layout file:
1. Take a screenshot and Read the image
2. **Judge it against the rubric below — this is the point of the skill, not an afterthought**
3. For interactive elements (forms, buttons, inputs), also test the interaction with playwright-cli

## How to judge the screenshot (do not skip)

A bare verdict of "looks good" is a **failure of this skill**. Your default instinct will be to
approve — resist it. UIs that are subtly wrong (inputs that don't match the house style, cluttered
cards, low-contrast text) look fine at a glance and are exactly what this step exists to catch.

Work in this order, and write down what you observe **before** giving any verdict:

**1. Zoom in.** A full-page shot is too small to judge detail — borders, contrast, and spacing get
lost. Take a focused shot of the component you just changed and Read that too:

```bash
screenshot /signup --selector ".signup-form"   # just the thing you changed
```

**2. Compare against the house style.** You cannot know what "correct" looks like from one screenshot
in isolation. Screenshot an **existing, known-good** page or component of the same kind (another form,
another card, another table) and compare side by side:

```bash
screenshot /login --selector ".login-form"      # a form that's already done right
```

Then ask: do the inputs, buttons, and cards in *your* change use the **same** border, corner radius,
padding, font, size, and color as the established pattern? Any divergence is a finding.

**3. Walk the checklist** explicitly — name what you checked, don't just assert "looks fine":

- **House-style conformance** — inputs / buttons / cards match the existing components (step 2)
- **Contrast & legibility** — text reads clearly against its background; flag grey-on-grey, low-contrast placeholder/label text, text over busy backgrounds
- **Spacing & alignment** — consistent padding/margins; edges line up; nothing crammed against a border
- **Clutter & density** — is the card/section overcrowded? Is there a clear visual hierarchy, or does everything compete?
- **Typography** — font family / size / weight consistent with the rest of the app
- **Truncation / overflow** — no clipped text, broken wrapping, unexpected scrollbars, or elements spilling out
- **States** (where relevant) — focus, hover, disabled, error — exercise them with playwright-cli, don't assume
- **Responsive** — for layout changes, also take a mobile shot (`--width 375 --height 812`)

**4. Report findings, then verdict.** List each problem tagged **blocker** (broken/unusable),
**should-fix** (clearly off-style or sloppy), or **nit** (minor polish). Only after you have walked the
checklist above may you conclude there are no findings — and say which checks you ran to get there.

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
screenshot /path --selector ".card"        # just one element, for close inspection
screenshot /path --port 8080               # custom port
screenshot /path --no-auth                 # skip authentication (public pages)
screenshot /path --auth-url "/login?token={token}&next={path}"  # custom auth URL template

screenshots / /dashboard /news             # batch: capture several paths at once
screenshots                                # batch: use ./screenshots.yml
screenshots --dark                         # batch: dark scheme for all pages
screenshots --group smoke                  # batch: capture a named group
screenshots -g smoke,admin                 # batch: union of several groups
screenshots / /login --selector ".form"    # batch: same element on each page
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
