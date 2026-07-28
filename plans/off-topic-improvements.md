# Off-topic improvements

Out-of-scope observations noted while working on something else. Triage with the
`dev-hooks:off-topic-improvements` skill.

## Baseline diff-gating for the review matrix

Deliberately left out of the sweep/matrix work (2026-07-28). The idea, from
[skill--visual-review](https://github.com/HartreeWorks/skill--visual-review): capture every
matrix cell before the change as well as after, perceptually diff the pairs, and record any
cell with a sub-threshold diff as `reviewed: unchanged from baseline`. Model attention then
goes only to the cells that actually moved, which is what makes a large matrix affordable.
The inverse signal is worth as much: a cell you *expected* the change to affect that diffs
to zero is itself a defect.

Why it was skipped rather than built:

- Producing the baseline normally means `git stash` / branch-switching mid-review, and
  mutating the working tree just to take a screenshot is a bad trade.
- A naive `-metric AE` pixel diff counts antialiasing and subpixel shifts as changes, so an
  unchanged cell reads as changed. A noisy baseline is worse than none — it erodes trust in
  the "unchanged" closure, which is the whole point. It needs a perceptual threshold
  (`-fuzz`, or `pixelmatch` with `includeAA:false`) and a pixel-count floor.
- It would add an external dependency (ImageMagick) or a new image lib to what are currently
  self-contained PEP 723 scripts.

The tree-mutation problem has a clean answer in this repo's normal workflow: worktrees. The
main checkout already holds the unchanged code while the feature worktree holds the change,
so a `screenshots --baseline ../..` could shoot both without touching either tree. Worth
revisiting if the matrix grows large enough that re-reviewing unchanged cells actually hurts.

## README structure

The README passed its audit only after a Contents list and a License section were added
(2026-07-28); both had been missing for a while. At ~2000 words it is close to the point
where the reference material (full flag tables, the `screenshots.yml` format) would be better
in a `docs/` page with the README keeping the tour.
