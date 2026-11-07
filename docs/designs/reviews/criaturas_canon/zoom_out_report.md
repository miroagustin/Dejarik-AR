# Zoom Out Review Report

**Target:** `C:/Users/miroa/OneDrive/Documentos/Repos/Dejarik-AR/docs/designs/criaturas_canon.md` (lines 1-673, full file)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-zoom-out` | completed |

**Severity breakdown:** 0 Blocker, 3 Major, 7 Nit

**Overall verdict:** The objective and context are clear, so the context check passes. The core design is sound and small: one victory clip, the `counter` fix, the stepped mixer, and a one-line CSS move for the roster. The main problems are the optional Commit 4, a `MOMENTS` map that is mostly a no-op, and a stop-motion plan that runs on two clocks that are not kept in sync.

## Prioritized Findings (Blockers -> Major -> Nits)

### 1. Commit 4 (Run / Weapon) is speculative scope and the most complex part of the doc - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Commit 4 (lines 602-654); SOURCES "run y weapon: pendientes" (line 504); Non-Goals (lines 84-86); LOOPING includes `run` (line 466)
* **Discrepancy Description**: The doc says that without Commit 4 "el diseño igual cumple todos los goals" (line 605). Neither Run nor Weapon is a canon moment, and moving and attacking already have clips. That goes against the doc's own rule that each canon moment gets its clip and the doc does not try to use all 14. Even so, Commit 4 brings in the most new machinery: the `KIND_MOMENTS` override table, a new `kind` constructor parameter, `RUN_SPEED`, a walk-or-run fallback for the capsule, and a midpoint search over `spec.adjacency` with its own fallback for a case that "no debería pasar". It also leaves Non-Goals inaccurate, because `run` and `weapon` are neither used nor listed there as unused.
* **Rationale & Recommendation**: Remove Commit 4 from this design. Move it to Future Improvements as one line next to the selection jump. List `run` and `weapon` under Non-Goals and in the SOURCES "sin usar a propósito" section, with the reason that they are not canon moments. Drop `run` from LOOPING in Commit 1.

### 2. The `MOMENTS` map has one real entry, and the doc contradicts itself on who uses it - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** A2 (lines 167-184); item 9 `MOMENTS` / `play(moment)` / `celebrate()` (lines 533-546); item 10 (lines 569-574)
* **Discrepancy Description**: Five of the six entries map a name to itself. Only `win` maps to a different clip. A2 says `events.js` calls `c.play("win")`, but items 9 and 10 have it call `celebrate()`, which reads `MOMENTS.win` directly. In practice, nothing goes through `play()`'s translation. That leaves the `?? moment` fallback, the exported map and the `play(moment)` rename serving an abstraction with one value.
* **Rationale & Recommendation**: Replace the map with one constant, `const WIN_CLIP = BASIC ? null : "wave"`. Have `celebrate()` use it and leave `play(name)` unchanged. Make A2 and item 10 agree that the entry point is `celebrate()`.

### 3. Stop-motion uses two independent quantizers and does not say how they stay in sync - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** A5 (lines 231-250); item 9 `walkTo` and `stepMixer` (lines 547-557)
* **Discrepancy Description**: The mixer advances through an accumulator fed by the render loop's `dt`. `walkTo` rounds its position from its own `performance.now()` clock (`tween` in `web/creatures.js:121-130`). The two step at different moments, so the legs can be out of phase with the body. A5 itself describes that artifact as looking like a bug. Line 554 admits the problem ("Hay que cuidar que el tween y el mixer usen el mismo reloj") but does not say how to solve it.
* **Rationale & Recommendation**: Use one clock. For example, have `Army.update` advance the root position in the same branch that calls `mixer.update(STEP)`, so the pose and the position change in the same frame. The alternative is to state that some mismatch is accepted. Either way, remove the open-ended caveat.

### 4. `?clips=basic` is a second rollback path that spreads into every feature - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** G7 (line 79); CUJ 4; item 9 `BASIC`; item 13
* **Discrepancy Description**: Each commit can already be reverted. The browser loads static files from a local server, so "sin redeploy" only saves editing a constant and refreshing the page. The flag is cheap today, but the doc tells every new feature to honor it, which multiplies the branches.
* **Rationale & Recommendation**: Limit the flag to the two values it controls (`WIN_CLIP = null`, `STEP = 0`). Say explicitly that later work does not have to honor it.

### 5. Collision dedup and its test cover a case the real assets cannot hit - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** A1 (lines 153-157); item 1 (lines 442-445); item 2 new test (lines 454-459)
* **Discrepancy Description**: All four source models carry the same 14 `CharacterArmature|` clips. None of the leftover names can collide with a contract name or with each other, so the `B|Idle / A|Attack` fixture tests a source that does not exist.
* **Rationale & Recommendation**: Keep the rule if it is one line (skip a name that is already present). Cut the test down to checking that extra clips are kept, with one assertion for `wave` and `yes`.

### 6. Part B is heavily documented for a one-line CSS change - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Parte B (lines 258-301); label alternatives (lines 360-393)
* **Discrepancy Description**: About 75 lines (an ASCII layout, three limits and three alternatives) support changing `top: 64px` to `bottom: 18px`, and much of it repeats the brief.
* **Rationale & Recommendation**: Reduce Part B to the change, the reason (the debug text overlaps the roster) and the one real limit (`#errors` can cover it). Give each rejected label option one sentence and link to section 7 of the brief.

### 7. Background sections largely copy the brief - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** The Problem, last two paragraphs (lines 50-59); Non-Goals (lines 82-95); Alternative A cons (lines 311-319)
* **Discrepancy Description**: These passages repeat `concepts_brief_personajes.md` almost word for word, so there are two copies to keep in sync.
* **Rationale & Recommendation**: Keep the decisions. Replace the detailed reasoning with a link to sections 1-2 of the brief.

### 8. The group celebration on `win` is not canon and restarts the killer's gesture - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** A3 diagram, `win` line (line 201); CUJ 3 (lines 126-132); item 10 `win(e)` (lines 573-574)
* **Discrepancy Description**: In the canon, the winner of a single fight raises its arms. The whole side does not celebrate at game end. The group celebration is also the only reason to store `owner`. On the final kill, the killer has already started the gesture in `death`, and `win` restarts it partway through.
* **Rationale & Recommendation**: Either keep it and label it as a UI choice, the way the doc labels the roster, or drop it and let the `GANA AZUL` banner mark the game end. Dropping it also removes the `this.owner` change.

### 9. The implementation plan spells out code in places - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Item 9 (warning `Set`, `??`, the rationale for the `while` loop); item 14 (adjacency pseudocode)
* **Discrepancy Description**: Some lines describe code rather than intent, and they will go stale once the code is written.
* **Rationale & Recommendation**: State the behavior instead: warn once per missing clip, catch up the step after a pause, and route a two-cell move through a free middle cell.

### 10. G6 has no way to pass or fail yet - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** G6 (lines 76-78); Open Questions (lines 103-105); Verification Plan "Demo (G6)" (line 667)
* **Discrepancy Description**: How G6 is verified is left to an open question, so the goal cannot currently pass or fail.
* **Rationale & Recommendation**: Commit to a cheap default, such as three people watching the replay at the rehearsal. Otherwise, move the "2 de 3" criterion to Open Questions and keep only the measurable part ("no animation stuck in 5 full games") in Goals.

## What to keep

These choices are well reasoned and minimal:
* Keeping all clips in adapt instead of Alternative D.
* Fixing `counter` outside the flag.
* Not awaiting the gesture.
* Moving the roster with CSS only.
