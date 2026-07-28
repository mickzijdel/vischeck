---
name: verify
description: Visually verify UI changes by taking authenticated screenshots of the local dev server, with a measurement sweep for what shouldn't be eyeballed. Use after editing any view, template, component, or layout file. For non-trivial UI work spanning several screens, breakpoints, or states, use vischeck:review instead. If screenshot redirects to a login page, invoke vischeck:setup-auth first.
---

# vischeck:verify

Use the `screenshot` CLI to visually verify UI changes against a running dev server. Always Read the saved image after taking a screenshot — then **review it like a critical designer, not a rubber stamp.**

This is the fast pass for one edit. When the change touches several screens, crosses a breakpoint, or
lands in a shared component that renders in many places, invoke `Skill(vischeck:review)` instead — it
builds a proper coverage matrix and a ledger to prove it.

## When to use

After editing any view, template, component, or layout file:
1. Take a screenshot **with `--sweep`**, and Read the image
2. **Judge it against the rubric below — this is the point of the skill, not an afterthought**
3. For interactive elements (forms, buttons, inputs), also test the interaction with playwright-cli

## Measure first, then look

Half of what goes wrong is arithmetic, and arithmetic done by eye is where a 12px error survives a
confident "looks good". `--sweep` measures the rendered layout and hands you a short list of numbers,
so your attention goes to what code can't judge:

```bash
screenshot /signup --sweep                      # zero-config checks
screenshot /signup --sweep --sweep-rows ".user-list" --sweep-align ".label" \
                           --sweep-content ".signup-form"   # named intent → verdicts
```

It catches what a screenshot cannot show you: sub-44px tap targets, `overflow: hidden` swallowing
text, a row that indents because it lacks an icon, a bar stopping short of its container, a page
scrolling sideways, a form card sitting 90px too high in its space.

Findings are graded. A **defect** was measured against a selector you named, so the number is a
verdict. A **lead** was auto-detected or is ambiguous — confirm it in the image before reporting it.
Naming selectors is what turns leads into verdicts.

Anything fixed or sticky needs a real viewport at a real scroll position — `--full-page` cannot
reproduce a bar covering the last row:

```bash
screenshot /feed --width 390 --height 640 --scroll bottom --sweep
```

## How to judge the screenshot (do not skip)

A bare verdict of "looks good" is a **failure of this skill**. Your default instinct will be to
approve — resist it. UIs that are subtly wrong (inputs that don't match the house style, cluttered
cards, low-contrast text) look fine at a glance and are exactly what this step exists to catch.

Work in this order, and write down what you observe **before** giving any verdict:

**1. Zoom in.** A full-page shot is too small to judge detail — borders, contrast, and spacing get
lost, and a 12px gap disappears entirely once the image is downscaled to a thumbnail. Take a focused
shot of the component you just changed, at 2x, and Read that too:

```bash
screenshot /signup --selector ".signup-form" --dpr 2   # just the thing you changed
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
- **Spacing & alignment** — consistent padding/margins; edges line up; nothing crammed against a border. The sweep measures the edges; you judge the rhythm
- **Grouping** — related elements tight, generous space *between* groups. Squint at it: `screenshot /signup --squint` blurs the page, and related elements should merge into one blob while unrelated ones stay separate. A heading floating as its own blob above the cluster it belongs to is a grouping defect
- **Clutter & density** — is the card/section overcrowded? Is there a clear visual hierarchy, or does everything compete?
- **Typography** — font family / size / weight consistent with the rest of the app
- **Truncation / overflow** — no clipped text, broken wrapping, unexpected scrollbars, or elements spilling out (the sweep flags the measurable half as `content-clipped` / `horizontal-overflow`)
- **States** (where relevant) — focus, hover, disabled, error — exercise them with playwright-cli, don't assume
- **Responsive** — for layout changes, also take a mobile shot (`--width 375 --height 812`). If the change crosses a CSS breakpoint, shoot **both sides of it** (767 *and* 768) — layouts fail on the far side, not in the middle of a range

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

`--widths` and `--themes` cross the selected pages with those axes, so one command covers a whole
matrix and names each file after its cell:

```bash
screenshots --group smoke --widths 390,767,768,1280 --themes light,dark --sweep
```

Each cell gets a `<name>.sweep.json` next to its PNG, and the summary ranks the worst cells first.

## Dark / light mode

Check this project's CLAUDE.md for any mention of dark mode or light mode:
- If dark mode **is** mentioned: take one screenshot in each mode (`screenshot <path>` and `screenshot <path> --dark`)
- If dark/light mode is **not mentioned**: take a single screenshot, then note to the user that they may want to add a line to CLAUDE.md documenting whether this project supports dark/light mode (e.g. `## UI: This app supports dark mode and light mode`)

## CLI reference

```bash
screenshot /path                           # authenticated screenshot (port from $PORT, else 3000)
screenshot /path --dark                    # dark color scheme
screenshot /path --width 375 --height 812  # mobile viewport
screenshot /path --full-page               # full scrollable page
screenshot /path --selector ".card"        # just one element, for close inspection
screenshot /path --selector ".card" --dpr 2  # ...at 2x, where hairlines and small gaps resolve
screenshot /path --scroll bottom           # real viewport at the bottom of the scroll
screenshot /path --squint                  # blurred, for the grouping/rhythm test
screenshot /path --ready-selector ".loaded" # wait for a postcondition, not a fixed timeout
screenshot /path --port 8080               # custom port (overrides $PORT)
screenshot /path --no-auth                 # skip authentication (public pages)
screenshot /path --auth-url "/login?token={token}&next={path}"  # custom auth URL template

screenshot /path --sweep                   # measure the layout; report numeric violations
screenshot /path --sweep --sweep-rows ".list"          # ...name the list containers
screenshot /path --sweep --sweep-align ".label"        # ...the edge that should stay constant
screenshot /path --sweep --sweep-full-width ".bar"     # ...what should span its container
screenshot /path --sweep --sweep-fixed ".mini-player"  # ...which bars can cover content
screenshot /path --sweep --sweep-content ".login-card" # ...the block that should be centred
screenshot /path --sweep --sweep-pair ".breadcrumb,.artwork"  # ...two edges that should match
screenshot /path --sweep --sweep-json out.json         # ...also save the raw findings

screenshots / /dashboard /news             # batch: capture several paths at once
screenshots                                # batch: use ./screenshots.yml
screenshots --dark                         # batch: dark scheme for all pages
screenshots --group smoke                  # batch: capture a named group
screenshots -g smoke,admin                 # batch: union of several groups
screenshots / /login --selector ".form"    # batch: same element on each page
screenshots --widths 390,768,1280          # batch: cross every page with these widths
screenshots --themes light,dark            # batch: cross every page with both themes
screenshots --sweep                        # batch: measure every cell, rank the worst
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
