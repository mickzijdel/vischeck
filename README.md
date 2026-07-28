# vischeck

A Claude Code plugin for visual verification of UI changes. Bundles a screenshot CLI, a layout **measurement sweep**, a smart PostToolUse hook, and three skills.

Screenshots catch what you look at. The sweep catches what you don't: a 12px gap survives a confident "looks good" every time, and a sub-44px tap target is invisible in any image. vischeck does both, and keeps them honest about which is which.

## What's included

| Component | Purpose |
|-----------|---------|
| `bin/screenshot` | Authenticated screenshot CLI via Playwright, plus `--sweep` layout measurement — auto-added to PATH |
| `bin/screenshots` | Multi-page batch CLI — crosses pages with width/theme axes into a review matrix and builds an `index.html` grid |
| `hooks/` | PostToolUse hook — reminds Claude to invoke `vischeck:verify` after view edits |
| `skills/verify/` | `vischeck:verify` — the fast per-edit pass: measure, zoom in, compare against the house style, report findings by severity |
| `skills/review/` | `vischeck:review` — the full pass for non-trivial UI: a scoped breakpoint/state/theme matrix, a coverage ledger, and a defect report a fix agent can act on |
| `skills/setup-auth/` | `vischeck:setup-auth` — sets up the dev auth bypass route (Rails, Django, Flask, FastAPI) |

## Contents

- [Install](#install)
- [Usage](#usage) — [measurement sweep](#measurement-sweep), [multi-page](#multi-page-screenshots), [review matrix](#review-matrix), [groups](#reusable-groups)
- [Dev auth](#dev-auth)
- [Hook behaviour](#hook-behaviour)
- [Dark / light mode](#dark--light-mode)
- [Development](#development)
- [License](#license)

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
screenshot /dashboard --selector ".user-card" --dpr 2   # ...at 2x, where hairlines resolve
screenshot /dashboard --scroll bottom           # real viewport at the bottom of the scroll
screenshot /dashboard --squint                  # blurred, for the grouping/rhythm test
screenshot /dashboard --ready-selector ".loaded" # wait for a postcondition, not a timeout
screenshot /dashboard --port 8080               # override the port ($PORT is the default, else 3000)
screenshot /dashboard --no-auth                 # public page, skip login
screenshot /dashboard --auth-url "/login?token={token}&next={path}"  # custom auth URL
```

Screenshots save to `tmp/screenshots/` in the current working directory. Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`).

`--scroll` exists because a fixed or sticky bar only covers content once the page has scrolled, and `--full-page` stitches the whole document rather than reproducing any real scroll position — so a bar eating the last row is invisible until you capture a real viewport at the bottom.

### Measurement sweep

Half of a visual review is arithmetic, and arithmetic done by eye is where a 12px error survives. `--sweep` measures the rendered layout in the DOM and prints the violations:

```bash
screenshot /episodes --width 390 --sweep
```

```
SWEEP 4 finding(s) at 390x640 — 2 defect(s), 2 lead(s) to confirm visually.
  [defect] not-full-width — element stops short of its container's content edge
      node=div.progwrap, container=div.dock, shortPx=22, elementRight=368, contentRight=390
  [defect] sibling-edge-misalign — one row breaks the edge column its siblings form
      edge=left, container=div.card, within=.label, min=31, max=73, delta=42
  [lead] gap-outlier — one gap in a list is roughly double its neighbours
      container=div.list, gapPx=28, typicalPx=12, afterRow=3
  [lead] small-tap-target — interactive element under 44x44 CSS px
      viewportWidth=390, count=5
      · button.play 30x30 (x5)
```

| Check | What it catches |
|-------|-----------------|
| `sibling-edge-misalign` | a row that indents because it lacks an icon; a control nudged out of the right-hand column |
| `height-variance` | a row that grows with a 2-line title while its neighbours don't |
| `gap-outlier` | a stray doubled margin between two rows |
| `not-full-width` | a bar or divider stopping short of its container's content edge |
| `pair-edge-misalign` | two regions that should share a left edge (reports box *and* content edges) |
| `fixed-bar-overlap` | a fixed/sticky bar covering content |
| `horizontal-overflow` | the page scrolling sideways, naming the culprit element |
| `content-clipped` | `overflow: hidden` swallowing text with no ellipsis |
| `small-tap-target` | an interactive element under 44×44 — invisible in any screenshot |
| `vertical-imbalance` | a login card or empty state sitting too high in its space |

Findings are graded. A **defect** was measured against a selector you named, so the intended layout is known and the number is a verdict. A **lead** was auto-detected or is inherently ambiguous — a gap may be a deliberate optical adjustment — so it needs confirming by eye. Naming selectors is what promotes leads into verdicts:

```bash
screenshot /episodes --sweep \
  --sweep-rows "[data-list]" \
  --sweep-align ".label" \
  --sweep-full-width ".progress-wrap" \
  --sweep-content ".auth-card" \
  --sweep-pair ".breadcrumb,.artwork" \
  --sweep-json findings.json
```

The zero-config checks (overflow, clipped content, tap targets, fixed-bar overlap, and drift in auto-detected lists) run on `--sweep` alone.

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

### Review matrix

`--widths` and `--themes` cross every selected page with those axes, so one command covers screen × breakpoint × theme instead of a hand-typed grid that quietly skips cells:

```bash
screenshots --group smoke --widths 390,767,768,1280 --themes light,dark --sweep
```

Prefer breakpoint **boundaries** over representatives — capture 767 *and* 768, because a layout fails on the far side of a breakpoint, not in the middle of a range. Every varying axis reaches the filename (`shows_w390_dark.png`), so no cell can silently overwrite another and report coverage it doesn't have.

With `--sweep`, each cell's findings are written next to its image as `<name>.sweep.json`, badged in the `index.html` grid, and ranked worst-first in the summary:

```
Measurement sweep, worst cells first:
  episodes_w390.png: 2 defect(s), 3 lead(s)
  episodes_w1280.png: 0 defect(s), 1 lead(s)
  settings_w390.png: clean
```

Scope the matrix before running it: fan out on the axis the change actually affects and hold the others at one representative value. The full cross-product is the worst case, not the default — `vischeck:review` walks through how to scope it.

**Selection:** positional paths always win. Otherwise `--group` / `--all` / `--list` operate on the config's `groups:`, and with no selection the config's top-level `pages:` list is used. The config file is auto-discovered as `screenshots.yml`, `.screenshots.yml`, or `config/screenshots.yml` in the current directory. With nothing to capture it prints the available groups (or the format help) and exits non-zero — it never guesses a page list.

Create a `screenshots.yml` to keep a consistent set of pages. Each entry is a plain path string, or a mapping with per-entry overrides; top-level keys are global defaults:

```yaml
port: 3000                # top-level keys are global defaults
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

**Option precedence** (most specific wins): per-entry override → group-level default → CLI flag → top-level global → built-in default. Override keys: `dark`, `full_page`, `width`, `height`, `no_auth`, `auth_url`, `selector`, `dpr`, `scroll`, `ready_selector`, `squint`. The dark variant of a path gets a `_dark` filename suffix so it doesn't collide with the light one. The command exits non-zero if any page fails to capture.

## Dev auth

The `screenshot` tool authenticates via a lightweight dev-only bypass route. To set it up in your project, ask Claude to invoke `vischeck:setup-auth` — it will ask for your permission and then implement the appropriate route for your framework (Rails, Django, Flask, or FastAPI).

## Hook behaviour

After every `Write` or `Edit` on a view/template file, Claude is reminded to invoke `vischeck:verify` with `--sweep` — and to escalate to `vischeck:review` when the change spans several screens, crosses a breakpoint, or touches a shared component. A file counts as a view if **either**:

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

## Credits

The measurement sweep, the breakpoint/state/theme matrix, the coverage ledger, and the squint
test are adapted from Peter Hartree's
[skill--visual-review](https://github.com/HartreeWorks/skill--visual-review), which those ideas
come from. The sweep is verified against that project's fixtures: it catches all ten of their
planted defects.

## License

MIT — see [LICENSE](LICENSE).
