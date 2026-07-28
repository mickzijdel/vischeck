---
name: review
description: Full visual review of non-trivial UI work — a scoped breakpoint/state/theme matrix, a measurement sweep, a coverage ledger, and a defect report a fix agent can act on. Use after implementing or changing non-trivial product UI (a shared component, a layout, a new screen) before reporting it done, and whenever the user asks for a visual review, visual QA, screenshot review, or polish pass. For a single-file tweak use vischeck:verify instead.
---

# vischeck:review

Tests, typecheck and code review all pass green on a misaligned row, a bar that
stops 12px short, a card clipped behind a fixed player, a desktop screen nobody
ever screenshotted. Every one of those is obvious the moment a capture is in
front of you at full size. The failure mode is not an inability to notice —
it is not capturing, and not looking.

This skill is the review discipline: a matrix that guarantees coverage, a
measurement pass that computes what shouldn't be eyeballed, a ledger that proves
what was reviewed, and a report a fix agent can act on without asking questions.

`vischeck:verify` is the fast everyday pass after one edit. Use this skill when
the change is bigger than that, or when the user asks for a visual review.

## When to run

Run after implementing or changing non-trivial product UI, **before** reporting
it done. Also run whenever the user explicitly asks for a visual review — that
request overrides every exclusion below.

A change to a shared component (a card, a list row, a header) means reviewing
**every screen that renders it**, not just the one that motivated the change.
An implementation subagent that verified with tests has not done this.

Do **not** run the full workflow for a one-line tweak, or for throwaway
artefacts whose purpose is thinking rather than presentation — an architecture
diagram, an internal HTML explainer, a planning page. Those get a render
smoke-check: open one view, confirm it renders, check for catastrophic overflow,
hand it over. Don't call that a visual review.

## Step 1: Scope, then build the matrix

**Scope first — the full cross-product is the worst case, not the default.**
Identify which axis the change actually moves and fan out on that one, holding
the others at a single representative value:

| The change | Fan out on | Hold constant |
|---|---|---|
| Title wrapping in a row | 1-line / 2-line **state** | one screen, one width |
| A colour token | **theme** (light/dark) | one width |
| A grid or container query | **breakpoint** | one state, one theme |
| A global layout primitive or shared token | all three | — |

Scoping well turns screens × breakpoints × states into roughly screens +
breakpoints + states, at near-zero coverage cost — the dropped cells were
redundant. Then enumerate the scoped matrix:

1. **Every affected screen — derived from the diff, not from memory.** Start
   from `git diff --name-only`. For each changed component, grep its direct
   render sites, then trace indirect ones: shared layouts, slots, re-exports,
   route configs, and any global CSS or design token the diff touched (a token
   change affects *every* screen). Cross-check against the route inventory.
   List any surface you deliberately exclude, with the reason.
2. **Every breakpoint it renders at — boundaries, not representatives.** At
   minimum 390 (mobile) and ≥1280 (desktop). For each CSS breakpoint the change
   crosses, capture **just below and at** it (767 *and* 768) — failures live on
   the far side. Add a **short viewport** (390×640) when anything fixed, sticky,
   or `vh`-based changed.
3. **The states that actually break.** Empty vs populated; 1-line vs 2-line text
   in the same row; overlays open; loading; error; both themes. The states most
   likely to break are the hardest to reach, so capture those first, not just
   the easy populated one.

Write the matrix out as a checklist, one todo per cell, **before** capturing.
Missed defects cluster precisely on the cells assumed unchanged.

## Step 2: Capture the matrix

`screenshots` crosses pages with the width and theme axes in one run, names each
file after its cell, and runs the measurement sweep per cell:

```bash
# the scoped matrix — one command, one cell per file
screenshots /episodes /episodes/123 /settings \
  --widths 390,767,768,1280 --themes light,dark --sweep

# a named slice you re-shoot every iteration (see screenshots.yml groups)
screenshots --group smoke --widths 390,1280 --sweep
```

Two capture rules that decide whether the review finds anything:

- **A fixed or sticky bar needs a real viewport at a real scroll position.**
  `--full-page` stitches the whole document and cannot reproduce a bar covering
  the last row. Capture the bottom of the scroll explicitly:
  `screenshot /episodes --width 390 --height 640 --scroll bottom --sweep`
- **Never judge detail from a full-page thumbnail.** A 12px gap is plainly
  visible at native size and gone entirely once the image is downscaled. For
  anything fine, shoot the component itself at 2x:
  `screenshot /episodes --selector "[data-row]" --dpr 2`

## Step 3: Measure first, then look

Half the checklist is arithmetic, and arithmetic done by eye is exactly where a
12px error survives. Run the sweep first and let it hand you a short list of
numbers; spend your actual attention on what code can't judge.

```bash
screenshot /episodes --width 390 --sweep \
  --sweep-rows "[data-list]" \
  --sweep-align ".label" \
  --sweep-full-width ".progress-wrap" \
  --sweep-content ".auth-card" \
  --sweep-pair ".breadcrumb,.artwork"
```

The sweep grades its own output. A **defect** was measured against a selector
you named, so the intended layout is known and the number is a verdict. A
**lead** was auto-detected or is inherently ambiguous — a gap may be a
deliberate optical adjustment — so confirm it in the image before it goes in the
report. Naming selectors is what promotes leads into verdicts.

**Measured by the sweep (⚙) — don't re-derive these by eye:**

| Check | What it catches |
|---|---|
| `sibling-edge-misalign` | a row that indents because it lacks an icon; a control nudged out of the right-hand column |
| `height-variance` | a row that grows with a 2-line title while its neighbours don't |
| `gap-outlier` | a stray doubled margin between two rows |
| `not-full-width` | a bar or divider stopping short of its container's content edge |
| `pair-edge-misalign` | two regions that should share a left edge (reports box *and* content edges) |
| `fixed-bar-overlap` | a fixed/sticky bar covering content |
| `horizontal-overflow` | the page scrolling sideways, with the culprit element |
| `content-clipped` | `overflow: hidden` swallowing text with no ellipsis |
| `small-tap-target` | an interactive element under 44×44 — invisible in any screenshot |
| `vertical-imbalance` | a login card or empty state sitting too high in its space |

**Verify centring by the number, never by eyeballing "looks centred"** — a block
at 40vh reads as roughly centred in a thumbnail while sitting ~90px too high on
a 900px screen.

**Judged by eye (👁) — the sweep can't do these:**

- **Vertical rhythm and grouping.** Related elements tight, generous space
  *between* groups. Use the squint test: `screenshot /episodes --squint` blurs
  the page, and related elements should merge into one blob while unrelated ones
  stay separate. A heading that reads as its own blob when it belongs to the
  cluster below is a grouping defect.
- **Text wrapping.** Orphan words, mid-word breaks, truncation that hides
  meaning.
- **Both themes.** Review light and dark; don't assume the second inherits
  correctly. Contrast, borders and images routinely break in exactly one.
- **House-style conformance.** Screenshot an existing known-good component of
  the same kind and compare — divergence in border, radius, padding or type is a
  finding.

**Cross-cell comparison.** Some defects only exist *between* captures: the same
row rendered 4px differently on two routes, a height that drifts between
screens. After the per-cell pass, group the same component across cells and
compare them side by side. The batch `index.html` is laid out for this.

## Step 4: Report

Two required parts. Both, every time.

### Coverage ledger — mandatory, defects or not

One row per matrix cell:

`cell | route | viewport W×H @ DPR | state verified | evidence path | defect IDs (or "unreviewed: <reason>")`

The closure rule: **planned cells = reviewed cells + explicitly-unreviewed
cells**, and every reviewed cell points at a file that exists. This is what
catches the skipped desktop pass, the missing page, the state variant that never
got opened. Finding one defect does not excuse leaving other cells unproven. A
cell you couldn't capture is listed `unreviewed: <reason>` — never silently
passed.

A cell can be discharged cheaply: one whose sweep came back clean closes as
`reviewed: sweep-clean`. Real attention goes to the handful that flagged.

### Defect list — numbered, most severe first

Written so a fix agent can reproduce it and know when it's fixed. Keep the
observed fact separate from the suspected cause, and don't hand over a
prescribed fix as though it were established (a blind `min-height` clips longer
content).

- **ID + severity** — blocker (broken/clipped/unusable), should-fix (visible
  inconsistency), nit (polish).
- **Expected** — the intended state: "bar reaches the 16px container padding".
- **Observed, with the number** — "right edge x=366, container content edge
  x=378, 22px short".
- **Reproduction** — the exact cell: route, viewport, DPR, theme, fixture,
  overlay, scroll position.
- **Evidence** — path to the capture that shows it.
- **Scope** — other cells affected, and a passing counterexample if one exists.
  Consolidate one root cause across cells into one defect.
- **Cause hypothesis** — the file, *labelled as a hypothesis*: "likely the row
  height keying off the title in EpisodeRow — not verified".
- **Acceptance check** — "all rows equal height with 1- and 2-line titles at 390px".

A bare "looks good" is a failure of this skill. If you found nothing, say which
cells you reviewed and which checks you ran to get there.

## If a capture fails

`screenshot` exits non-zero and explains itself on stderr. If it reports that
the page needs auth but the auth route 404s, invoke `Skill(vischeck:setup-auth)`
to add the dev auth route, then retry. A cell you still can't capture goes in
the ledger as `unreviewed`, with the reason — an environment failure is never
reported as an app defect.
