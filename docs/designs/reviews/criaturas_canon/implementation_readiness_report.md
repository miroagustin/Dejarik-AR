# Implementation Readiness Report

**Target:** `docs/designs/criaturas_canon.md` (lines 429-673, the implementation plan; lines 1-428 read as context only)

**Verdict:** Not ready yet. Commits 1 and 3 can be built almost as written. Commit 2 leaves two decisions about the stepped animation unmade, and its manual check can't be reproduced. Commit 4 contradicts itself and leaves two gaps in how the run works. None of these block the work outright; each needs a sentence or a short piece of pseudocode.

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-implementation-readiness` | completed |
| `egm-codebase-details` | completed |
| `egm-style` | completed |

**Severity breakdown (after deduplication):** 0 Blocker, 13 Major, 14 Nit.

Severity note: `egm-codebase-details` rated two findings as Blockers: item 6 (originals already tracked) and the "find a counter in the replay" step. Neither one stops an engineer from writing the code. One is a step that does nothing, and the other is a check that can't be run as written. Both are listed below as Major.

## What already holds up

`egm-codebase-details` and `egm-implementation-readiness` checked these against the repo and found them correct:
- `adapt_glb.py:31-44` (`rename_clips`, `CLIP_NAMES`), and the assertion at `tests/test_check_glb.py:81`.
- `main.js:193` (the fixed button list), the `still` parameter (`main.js:206`) and the viewer's mixer call (`main.js:205`).
- `creatures.js`: `LOOPING` (:10), `Army.sync` (:151), `Army.update` (:174). `CLIPS` is used only in `creatures.js`, so deleting it is safe.
- `style.css:44` (`#roster`). `#roster` sits in `#hud`, outside `#stage` (`index.html:16-24`), so the mirror does not flip it.
- `assets_checklist.md` lines 25, 37, 85 and 104.
- The four originals exist as `assets_src/originals/<kind>_<Monstruo>.glb`. `soldado_Orc.glb` holds the 14 clips the plan lists.
- `game.py:61-67` (BFS that skips occupied cells). `board_spec.json` adjacency uses string keys. `win.result.winner` and `Piece.owner` are both ints.
- The plan doesn't rebuild any helper that already exists in the repo. Commit 3 is complete and testable as written.

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. `stepMixer` signature conflicts with "one shared accumulator" - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Lines 550-557, 579
* **Discrepancy Description:** `stepMixer(mixer, dt, acc)` adds `dt` to the accumulator, steps one mixer and returns the new value. `Army` is supposed to keep one accumulator and use it with every mixer. The obvious code, `this.acc = stepMixer(c.mixer, dt, this.acc)` inside the loop over creatures, adds `dt` up to 8 times per frame. The first mixer also uses up the pending steps before the others see them, so the creatures fall out of sync. The viewer (item 11) needs its own accumulator, and the plan doesn't mention it.
* **Rationale & Recommendation:** Split the work. Compute `n = Math.floor((acc + dt) / STEP)` once per frame, call `mixer.update(n * STEP)` on every mixer, and keep the remainder. This also replaces the `while` loop and avoids hundreds of updates after a long tab pause. Write the 4-line pseudocode for `Army.update`, and say that `runViewer` keeps its own accumulator.

### 2. "The tween and the mixer must use the same clock" is a warning, not a step - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Lines 547-549, 554-555
* **Discrepancy Description:** `tween()` runs on `performance.now()` with its own `requestAnimationFrame` loop (`creatures.js:121-130`). The mixer runs on the main loop's `dt` (`main.js:146-150`). Rounding `t` from each walk's own `t0` won't line up with the global pose ticks, so the legs and the position jump on different frames. Spec line 238 warns about exactly this. The sentence also sits in the `stepMixer` bullet, although it is about `walkTo`.
* **Rationale & Recommendation:** Choose a mechanism and move it into the `walkTo` bullet. One option: a tick counter at module level that `Army.update` advances, and `walkTo` updates the position only when the tick changes. The other option is to accept the phase offset and delete the sentence.

### 3. The commit 2 CUJ check can't be reproduced - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details` (rated Blocker), `egm-style`
* **Affected Scope:** Lines 582-589
* **Discrepancy Description:** "Buscar uno [counter] en el replay" can't work. A `.dj` file stores only frames, never game state or events (`dejarik_ar.md:969`, `:1086`). `--replay` runs the game live, with dice drawn from the seed (`game.py:113-116`). CUJs 1-3 need specific setups (a soldier at 2 HP next to a beast at 1 HP, a `counter` result, the last piece at 1 HP), and "jugar hasta que salga" is not a step anyone can repeat.
* **Rationale & Recommendation:** Add a fixture: a hand-written `save/state.json` loaded with `--resume`, or a `[game] seed` in `config.toml` plus a click sequence known to produce `hit` and `counter`. Add the fixture file to commit 2's file list.

### 4. The Wave/Yes choice is written to SOURCES.md, but no commit lists that edit - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Lines 498-505, 521-523
* **Discrepancy Description:** Item 7 (commit 1) asks SOURCES.md to name the clip that loses between `wave` and `yes`. That choice is only made in the viewer after commit 1. Line 523 says the result also goes into SOURCES.md, but commit 2's file list (items 9-11) doesn't include `assets_src/SOURCES.md`.
* **Rationale & Recommendation:** In commit 1, write a placeholder ("pending: chosen in the viewer") or drop the bullet. Add `assets_src/SOURCES.md (Modify)` to commit 2 with the exact line to fill in.

### 5. `KIND_MOMENTS` may not exist, but `play()` always reads it - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`
* **Affected Scope:** Lines 615-623
* **Discrepancy Description:** The plan says that if Weapon isn't adopted, "el objeto no se crea". The next bullet has `play()` read `KIND_MOMENTS[this.kind]?.[moment]` unconditionally. If the object was never declared, that line throws a ReferenceError. Adopting Weapon also needs a second manual viewer step (Weapon vs Punch), and commit 4 doesn't list one the way commit 1 lists the Wave/Yes step.
* **Rationale & Recommendation:** "`KIND_MOMENTS` always exists. It is `{}` when BASIC is true or Weapon is not adopted. Only the `soldado` entry is conditional." Add the viewer step to commit 4's sequence.

### 6. The two-leg run stalls at the middle cell - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 624-627, 632-642
* **Discrepancy Description:** `walkTo` calls `face()` at the start and ends with `await this.play("idle")` (`creatures.js:102-105`). Two `walkTo(..., "run")` calls in a row give run, then about 0.2 s of crossfade to idle, then run again, which is a visible stutter. "Después vuelve a `idle` como hoy" puts that idle in the `move` handler, but it actually happens inside `walkTo`. `events.js:11-17` never plays idle.
* **Rationale & Recommendation:** Give `walkTo` an option to skip the final idle (for example `rest = false` on the first leg). Play idle once, after the last leg.

### 7. Run speed follows the requested moment, not the clip that actually plays - Severity: Major
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** Lines 612-614, 624-627, 651-654
* **Discrepancy Description:** `RUN_SPEED` applies "cuando `moment === "run"`". With `?clips=basic` (`MOMENTS.run = "walk"`), or on the capsule where `walkTo` falls back to `walk`, the piece plays the walk cycle at run speed and slides across the board. The commit 4 check doesn't say what speed to expect in that mode.
* **Rationale & Recommendation:** State that `RUN_SPEED` applies only when the `run` action is actually played. Add the expected speed to the `?clips=basic` check.

### 8. Moment names, our clip names and source clip names are mixed together - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-codebase-details`
* **Affected Scope:** Lines 466, 538-539, 615-622, 651-654
* **Discrepancy Description:** `play()` accepts both moments and clip names, and they share strings (`attack`, `walk`, `run`). After commit 4, the viewer's "attack" button for the soldado goes through `KIND_MOMENTS` and plays `weapon`. The viewer can then no longer show the original Punch clip, which defeats the side-by-side comparison it exists for. The text also mixes source names (Punch, Run, Weapon) with ours: line 654 says "vuelven walk y Punch", but our clip is called `attack`. Line 466 doesn't say whether `LOOPING` holds moment names or clip names.
* **Rationale & Recommendation:** Have the viewer play actions directly, without translation (for example a `playClip(name)`). Say once that source names are capitalized and ours are lowercase, then use them consistently. Say that `LOOPING` holds clip names.

### 9. Duplicate-name rules, output order and test coverage are unspecified - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 439-446, 452-459
* **Discrepancy Description:** Item 1 doesn't say which clip wins a name clash, or in what order the output list comes. Today `by_short` is a dict (`adapt_glb.py:35`), which silently keeps the last duplicate, so `B|Idle` would become the contract `idle`. The modified assertion `CLIPS + ["dance"]` only passes if contract clips come first in `CLIP_NAMES` order and kept extras follow in source order. The new test covers only extra-vs-contract clashes (`B|Idle`, `A|Attack`). It never exercises the extra-vs-extra rule ("o con otro ya conservado"), and it doesn't name the expected survivors.
* **Rationale & Recommendation:** Specify: "contract clips first, in CLIP_NAMES order. Then walk `gltf["animations"]` in source order, skip the objects already used for the contract (compare objects, not names), and keep the first occurrence of each lowercase short name." Add an `A|Wave` + `B|Wave` case. Name the survivors in the test (for example "`idle` comes from `A|Idle`").

### 10. The verification command fails in PowerShell - Severity: Major
* **Reviewer Lens:** `egm-codebase-details`, `egm-implementation-readiness`, `egm-style`
* **Affected Scope:** Line 663
* **Discrepancy Description:** PowerShell doesn't expand `web/assets/creatures/*.glb` for native programs, and `check_glb.main` (`check_glb.py:173-181`) doesn't expand the pattern itself. The command reports "No se pudo leer el archivo" and fails.
* **Rationale & Recommendation:** List the four files explicitly, or use `(Get-ChildItem web/assets/creatures/*.glb).FullName`.

### 11. Item 6 commits files that are already tracked - Severity: Major
* **Reviewer Lens:** `egm-codebase-details` (rated Blocker), `egm-implementation-readiness`
* **Affected Scope:** Lines 486-490
* **Discrepancy Description:** `.git/index` already lists all four `assets_src/originals/*.glb` files, most likely from commit 72200f3. `.gitignore` doesn't exclude them, and git status doesn't show them as untracked. The claim comes from a stale line in the brief (`concepts_brief_personajes.md:77`; spec line 164).
* **Rationale & Recommendation:** Delete item 6 or change it to "already tracked, nothing to do". Drop the "unos 2 MB" reasoning about commit size.

### 12. `celebrate()` replaces the spec's `play("win")` without saying so - Severity: Major
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 538-546, 563, 573-574
* **Discrepancy Description:** The spec says `events.js` calls `c.play("win")` (line 178) and stores `lastFight = { atacante, defensor }` (line 196). The plan uses `celebrate()` and `fight = { atk, def }`. With BASIC on, `MOMENTS.win` is `null`, so `null ?? "win"` makes `play("win")` look for an action called "win", log a misleading missing-clip warning, and resolve. The plan avoids this only because nothing calls `play("win")` any more. An engineer who follows the spec would hit it.
* **Rationale & Recommendation:** Add: "`celebrate()` replaces `play("win")`; `win` is never passed to `play()`." Use one variable name in both the spec and the plan. Say that `LOOPING` and the missing-clip warning use the resolved clip name.

### 13. The commit 3 check goes further than the limits the spec accepts - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 599-600
* **Discrepancy Description:** "el roster no se pisa con ningún texto" conflicts with spec lines 284-289. Those lines accept that `#errors`, the debug markers and the hand box may overlap the roster. A tester could fail the commit for an overlap the spec already allows.
* **Rationale & Recommendation:** Narrow the check to "the roster doesn't overlap the debug status lines (fps/pose/ms/hand) or `#role`".

### 14. SOURCES.md table change is unclear, and the regeneration command is stale - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 480-482, 496-497
* **Discrepancy Description:** "se agrega la ruta del original" doesn't say whether the path goes in a new column or in "Origen". The current header describes a mapping, not a list of 14 clips. The regeneration command at `SOURCES.md:17` still uses `<descarga>.glb`.
* **Rationale & Recommendation:** Give the new header and column layout. Add the update to line 17 (`assets_src/originals/<kind>_<Monstruo>.glb`) to item 7.

### 15. The revert claim needs narrowing - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`
* **Affected Scope:** Lines 431-432
* **Discrepancy Description:** "se puede revertir solo" can be read as "automatically". Commit 4 depends on commit 1's `LOOPING` entry for `run`, and on commit 2's `MOMENTS`, `BASIC` and translation inside `play()`.
* **Rationale & Recommendation:** "Each commit can be reverted separately, in reverse order. Commit 3 is independent."

### 16. The wrong docstring is named - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 445-446
* **Discrepancy Description:** "descarta el resto" is in the `rename_clips` function docstring (`adapt_glb.py:34`), not in the module docstring. The module docstring (`:6`) says "renombra los clips a idle/walk/attack/hit/die".
* **Rationale & Recommendation:** Update both docstrings.

### 17. The test edit refers to a line number and leaves a stale comment - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 452-453
* **Discrepancy Description:** "la línea 81" will move once the file is edited. The comment `# Dance se descarta` on that line becomes false.
* **Rationale & Recommendation:** Name the assertion instead of the line number, and update the comment.

### 18. `MOMENTS` is exported, but nothing imports it - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 533-535
* **Rationale & Recommendation:** Drop the export. `stepMixer` does need its export, because the viewer uses it.

### 19. `BASIC` parses the URL again - Severity: Nit
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** Lines 531-532
* **Discrepancy Description:** `main.js:11` already builds `params`. Parsing again in `creatures.js` is acceptable, since that module doesn't import `main.js`.
* **Rationale & Recommendation:** Say that this is deliberate, or pass the flag in.

### 20. The survivor celebrates twice in CUJ 3 - Severity: Nit
* **Reviewer Lens:** `egm-codebase-details`
* **Affected Scope:** Lines 573-574
* **Discrepancy Description:** The survivor gets `celebrate()` once from `death` and again from `win`. The second call restarts the gesture through `reset().play()`.
* **Rationale & Recommendation:** Say whether to skip a creature whose current action is already the win clip.

### 21. `dejarik_ar.md` still says there are exactly 5 clips - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`, `egm-codebase-details`
* **Affected Scope:** Lines 507-515
* **Discrepancy Description:** `dejarik_ar.md` (:476, :926, :933, :1168, :1232) still describes exactly five clips, with the rest discarded. It isn't in the update list.
* **Rationale & Recommendation:** Add it to the list, or state that the base design is historical.

### 22. The lint step is vague - Severity: Nit
* **Reviewer Lens:** `egm-codebase-details`, `egm-style`
* **Affected Scope:** Line 662
* **Rationale & Recommendation:** The repo has no linter (`dejarik_ar.md:1339`). Write "Not applicable".

### 23. The `LOOPING` literal is ambiguous, and `jump_idle` doesn't loop - Severity: Nit
* **Reviewer Lens:** `egm-style`, `egm-codebase-details`
* **Affected Scope:** Line 466
* **Discrepancy Description:** In JS, `{idle, walk, run}` reads as an object literal, not a set. `jump_idle` is also a looping clip, so in the viewer it will play once and freeze.
* **Rationale & Recommendation:** Write `new Set(["idle", "walk", "run"])`. Decide whether `jump_idle` belongs in the set.

### 24. `run` and `weapon` stay "pending" if commit 4 is skipped - Severity: Nit
* **Reviewer Lens:** `egm-implementation-readiness`
* **Affected Scope:** Lines 496-497
* **Discrepancy Description:** Non-Goals line 85 requires a canon reason for every kept clip. If commit 4 is skipped, these two never get one.
* **Rationale & Recommendation:** Give a final reason now, or add a fallback line.

### 25. The mirror key "F" isn't confirmed - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Line 599
* **Discrepancy Description:** The key lists in the baseline docs show D, L, R, P and M. Nobody checked the code for the mirror key.
* **Rationale & Recommendation:** Confirm the key in the code, or point to where it is bound.

### 26. Wording cleanups - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 533-535, 553-554, 612-614, 626-627, 637, 584
* **Discrepancy Description and Recommendation:**
  * 533-535: "`win→<clip>`, o `null` si BASIC" can be read as the whole `MOMENTS` being null. Write "`win` vale el clip elegido, o `null`...".
  * 553-554: with an `if` instead of `while`, the animation wouldn't freeze. The backlog would drain one step per frame, so it would run fast instead. Fix the stated reason (finding 1 removes the loop anyway).
  * 612-614: "resuelve vacío" is jargon. Write "the capsule has no `run` action; `walkTo` uses `walk` then".
  * 626-627: "Si no" means "sin RUN_SPEED"; say that. Line 637: "que no ocupe ninguna criatura" has subject and object reversed; write "que no esté ocupada por ninguna criatura".
  * 584: "click" here, "clic" everywhere else. Pick one.

### 27. Line 431 is much longer than the surrounding wrapped text - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Line 431
* **Rationale & Recommendation:** Purely cosmetic. Wrap it like the rest of the plan.

Dropped during deduplication: the style reviewer flagged `&still` (line 521) as undefined. `egm-codebase-details` confirmed it exists at `main.js:206`.
