# Goldfish Review Report

**Target:** `C:/Users/miroa/OneDrive/Documentos/Repos/Dejarik-AR/docs/designs/criaturas_canon.md` (FeatureRange, lines 1-428; the Detailed Implementation Plan from line 429 on was not reviewed)

**Stage:** 7, Critic Review (design, structure, writing)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-design` | completed |
| `egm-structural` | completed |
| `egm-style` | completed |

**Severity breakdown (after merging duplicates):** 2 Blocker, 14 Major, 19 Nit.

Before merging, each reviewer reported: design 0 Blocker / 9 Major / 6 Nit, structural 2 / 5 / 5, style 0 / 7 / 12. Where reviewers rated the same issue differently, this report keeps the higher rating and notes the disagreement.

**Overall verdict:** the core design holds up. The reviewers agreed on these points:

- The asset pipeline keeps the extra clips.
- One moment-to-clip map lives in the client.
- The victory gesture is not awaited.
- The `counter` fix works whether or not the flag is set.
- Part B changes only CSS.

The spec still needs revision before implementation. It has no Risks section, it credits rejections to "the author" without links, and its rollback path is unreachable and partly broken. Several scope statements also contradict each other: G1 vs G6, Run/Weapon, and the Part B name.

Note: egm-design did not open source code. The spec's code citations (events.js, creatures.js, game.py, debug.js, style.css line numbers) were taken as written and not checked.

## Prioritized Findings (Blockers -> Major -> Nits)

### No "Risks & Mitigations" section - Severity: Blocker
* **Reviewer Lens:** `egm-structural` (Blocker), `egm-design` (Major)
* **Affected Scope:** The whole document. The section is missing between Alternatives (303-394) and Non-Functional Requirements (397). Part of the content exists at 279-289 ("Límites conocidos") and in the NFR (397-407).
* **Discrepancy Description**: The standard requires a section listing failure modes, limits and mitigations, and the baseline `dejarik_ar.md` has one. Here, risks appear only as scattered asides (182-184, 186-190, 208-210, 237-242) and in the Cons of Alternative E (354-356). Part A has no list of its own risks. These risks are not mentioned anywhere:
  - Clip names in `MOMENTS` drifting away from the names in the .glb files.
  - `lastFight` going stale or arriving out of order.
  - A 15-30 fps Teams capture beating against the 12 fps step, so poses hold for uneven lengths (judder) for the very audience G6 measures.
  - `army.sync` interrupting a gesture on reconnect.
  - A survivor stuck on the gesture's last frame if the return-to-idle guard misfires.
  - The design defects listed below (rollback NaN, clock mismatch, double gesture).
* **Rationale & Recommendation**: Add `## Risks & Mitigations` between Alternatives and NFR. Write one row per risk with columns for risk, impact, mitigation, and rehearsal check or flag. Cover both parts, and include rehearsal checks such as "STEP tuned while watching the Teams share from another account". Have 279-289 point to the new section instead of holding risks inline.

### Rejections are credited to "the author" without links, and one has no technical reason - Severity: Blocker
* **Reviewer Lens:** `egm-structural` (Blocker), `egm-design` (Major), `egm-style` (Nit)
* **Affected Scope:** Lines 320-322, 335-336, 346-348, 357-358, 370-371, 383-384, 392-393
* **Discrepancy Description**: All seven rejections begin "Rejected by author". The standard forbids crediting a rejection to a maintainer without linking the issue, discussion or PR. "(brief, etapa 1)" and "(brief, decisión 2)" are plain-text citations with no link. Alternative C's rejection ("queda fuera de este diseño") states a scope decision, not a trade-off.
* **Rationale & Recommendation**: Start each rejection with its concrete technical trade-off. Where the author's decision matters, link the brief inline, e.g. `[brief, decisión 2](../../../briefs/concepts_brief_personajes.md#...)`. For C, state the trade-off in the rejection itself: it duplicates the existing highlight and needs a stance layer.

### The `?clips=basic` rollback can't be reached from the host window - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 79-80 (G7), 134-140 (CUJ 4), 403-406 (NFR)
* **Discrepancy Description**: CUJ 4 has the operator "abrir la página con `?clips=basic`". In `dejarik_ar.md`, the host runs in a Chrome `--app` window, which has no address bar. Its URL carries `k=<host_token>`, which is never printed. During a demo the operator has no practical way to add the flag. The flag would also apply only to the host, so the remote client would keep the new behavior. That is harmless, but it isn't documented.
* **Rationale & Recommendation**: Give the flag a real entry point. Options: a CLI flag (e.g. `python -m dejarik --clips basic`) that adds the parameter to the `--app` URL, a host key toggle, or written step-by-step instructions. Also confirm the server ignores the extra query parameter, since `location.search` is forwarded to the WebSocket URL.

### `STEP = 0` under the rollback flag breaks walking - Severity: Major
* **Reviewer Lens:** `egm-design` (Major), `egm-style` (Nit)
* **Affected Scope:** Lines 237-241, 246-247
* **Discrepancy Description**: With `?clips=basic`, `STEP = 0`, and `walkTo` rounds `t` to multiples of `STEP / secs`. Rounding to a multiple of zero gives NaN, so the piece's position is lost. The rollback would break the most common animation. Calling STEP a "constante" is also misleading when a flag changes it.
* **Rationale & Recommendation**: State that both the mixer accumulator and the `walkTo` quantization are skipped when `STEP <= 0`. Add a step to CUJ 4: "a move still works with the flag on".

### Pose steps and slide steps run on different clocks - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 233-242
* **Discrepancy Description**: The mixer steps on an accumulator in `Army.update`. `walkTo` quantizes its tween from the tween's own start time. The two 12 fps grids are out of phase, so the body slide and the leg poses change at different moments, up to 83 ms apart. That produces the "se ve como un error" effect the section is trying to avoid. Turning to face a target is another tween the spec does not address, so it would stay smooth.
* **Rationale & Recommendation**: Drive every tween that moves a piece from the same global step tick. List explicitly which motions are stepped (position, facing) and which stay smooth (flash, opacity fades, camera shake).

### The victory gesture plays twice at game end - Severity: Major
* **Reviewer Lens:** `egm-design` (Major), `egm-style` (Nit)
* **Affected Scope:** Lines 126-132 (CUJ 3), 194-202 (A3 diagram)
* **Discrepancy Description**: On the final kill, the `death` handler starts the gesture on the survivor. Right after, the `win` handler starts it again on every living winner, including that survivor. Because `play` resets the clip, the gesture restarts partway through, at the most visible moment of the match. CUJ 3 also says "el atacante" where the rest of the document says "sobreviviente".
* **Rationale & Recommendation**: In the `win` handler, skip creatures already playing the win action. Alternatively, skip the gesture in `death` when a `win` will follow. State the chosen behavior in CUJ 3 and use "sobreviviente" there.

### G1 limits the gesture to lethal fights, but the canon and G6 cover every exchange - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-style`
* **Affected Scope:** Lines 29-31, 36-41, 63-65 (G1), 76-78 (G6), 192
* **Discrepancy Description**: The Overview and the brief describe the winner raising its arms after every won fight. G1 and the A3 heading narrow this to fights that end in a death, without saying why. G6 then asks first-time viewers to say who won any exchange. Most exchanges are non-lethal (damage is 1, HP is 2-3), so those viewers get no winner signal.
* **Rationale & Recommendation**: Choose one. Either extend the non-awaited gesture to every `hit`/`counter` outcome (timing stays safe), or keep G1, write down the reason, and narrow G6 to lethal exchanges.

### No candidate clip delivers G1's arms-up gesture, and the clip choice has no exit criterion or fallback - Severity: Major
* **Reviewer Lens:** `egm-design`, `egm-style`
* **Affected Scope:** Lines 29-31, 39, 63-65, 97-102, 174-176
* **Discrepancy Description**: G1 promises "levantando los brazos". The Open Questions admit that neither Wave nor Yes is arms-up, and that Wave may read as "no" to an Argentine audience. As written, the goal can't be met. The question also has no decision rule or fallback. A single global `MOMENTS.win` assumes one clip reads well on four different skeletons.
* **Rationale & Recommendation**:
  - Rephrase G1 as "un gesto de victoria (Wave o Yes, ver Open Questions)".
  - Add a decision rule: who decides, judged at real scale through Teams.
  - Add a fallback: `win: null`, or have the Blender AI author an arms-up clip (assets_checklist Fuente 2, item 1).
  - Allow an optional override per creature kind in `MOMENTS`.

### Run/Weapon status is undefined, and the commit plan doesn't match Parts A/B - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`, `egm-design`
* **Affected Scope:** Lines 12-26, 79-86, 153-156, 344, 403-406
* **Discrepancy Description**: The NFR lists "tres commits (más uno opcional) ... (assets, canon, roster y Run/Weapon)". No Goal, Non-Goal, Technical Plan section or Future Improvement defines Run/Weapon. The Non-Goals list of unused clips leaves out Run and Weapon, so not all 14 clips are accounted for. The brief's caveat is also dropped: Run over 2 cells cuts across the board because `walkTo` moves in a straight line. The Overview counts "partes", G7 counts "etapas" and the NFR counts "commits", and the commit split doesn't map to A/B.
* **Rationale & Recommendation**:
  - Either add a short "A7. Opcional: Run y Weapon" subsection with its risks, or list both under Non-Goals / Future Improvements, and remove them from the NFR.
  - Use one term for the deliverable unit.
  - State the mapping once as a numbered list: A = commits 1, 2 and optional 4; B = commit 3.

### Alternative labels can't be resolved from this document - Severity: Major
* **Reviewer Lens:** `egm-structural`, `egm-style`, `egm-design`
* **Affected Scope:** Lines 260, 303-393
* **Discrepancy Description**: The clip alternatives are lettered A, C, D, E with no B, yet C is defined as "B + salto al seleccionar" (324). The label alternatives are "b", "c" and one entry with no letter (386). The chosen "opción a" is never introduced. Both chosen options are defined only in the brief. Uppercase "B" also collides with "Parte B".
* **Rationale & Recommendation**: Either add short "B (elegida)" and "a (elegida)" entries that point to the Technical Plan, or reletter everything in order. Rewrite C so it stands alone, and give the entry at 386 a letter.

### The title and "Parte B" name a feature the design dropped - Severity: Major
* **Reviewer Lens:** `egm-style` (Major), `egm-structural` (Nit)
* **Affected Scope:** Lines 1, 21-26, 55, 258-261, 360
* **Discrepancy Description**: The title and the Part B heading say "etiqueta de vida", but line 260 says there is no floating label. Part B only moves `#roster`. Readers who skim will expect a label feature.
* **Rationale & Recommendation**: Rename Part B (e.g. "Parte B: roster legible con debug") and adjust the title. Keep "etiqueta" only inside the rejected alternatives.

### `win`, `hit` and `attack` each mean two or three things - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 113-114, 130-131, 174-178, 196-202, 223-226
* **Discrepancy Description**: `win` is both the server's end-of-game event and the moment key for the per-death gesture. Line 201 uses both meanings. The brief already flagged this ambiguity. `hit` is an outcome, a clip and an event, and `attack` is both an event and a clip. Line 226 only makes sense once the reader works out that it means outcomes.
* **Rationale & Recommendation**: Rename the moment key (e.g. `victory` or `cheer`). Always qualify the other terms: "resultado `hit`", "clip `hit`", "evento `hit`".

### The timing arithmetic contradicts the surrounding text - Severity: Major
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 211-216, repeated at 354-356
* **Discrepancy Description**: The text says the gesture starts at the same time as the fade, but "unos 3.2 s" adds them one after the other. If they overlap, an awaited handler takes about 2.6 s. "Suma 1.7 s" doesn't follow from either model.
* **Rationale & Recommendation**: State which overlap model applies and recompute both figures. Keep the numbers only in A3 and have Alternative E refer to them.

### Part B has no user journey - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** Lines 107-140
* **Discrepancy Description**: All four CUJs cover Part A. G4 (life readable with debug on and the image mirrored) can't be traced from goal to journey to design.
* **Rationale & Recommendation**: Add "CUJ 5: Leer la vida con debug". Given: debug on, mirror on. When: a hit lands. Then: the roster at bottom-left shows the updated HP and isn't covered.

### Additional Resources and Future Improvements are nested under NFR - Severity: Major
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** Lines 411, 422
* **Discrepancy Description**: Both are H3, so they fall under `## Non-Functional Requirements`. In the baseline, `## Future Improvements` is an H2.
* **Rationale & Recommendation**: Promote both to H2.

### No alternatives considered for the stop-motion mechanism - Severity: Major
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** A5 (around lines 233-247); Alternatives (303-393)
* **Discrepancy Description**: G3 adds a new behavior to every creature but lists no rejected alternatives. Candidates include:
  - A render-side approach.
  - Baking the stepped sampling into the glTF samplers in `adapt_glb`. This makes the stepping data-driven and gives a rollback without a flag.
  - A per-clip `timeScale` trick.
* **Rationale & Recommendation**: Add 1-2 rejected alternatives with concrete trade-offs.

### Mixed English and Spanish labels - Severity: Nit
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** Lines 309-393
* **Discrepancy Description**: "Pros", "Cons", "Reason for Rejection" and "Rejected by author:" are in English, while the content is in Spanish. The baseline writes "Motivo del rechazo".
* **Rationale & Recommendation**: Use one language for labels, preferably the baseline's.

### Inconsistent part split across sections - Severity: Nit
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** Lines 36, 55 vs 144/258 and 305/360
* **Discrepancy Description**: The Problem uses bold run-in text for Clips/Etiqueta, while Plan and Alternatives use H3 headings. The Goals aren't tagged by part.
* **Rationale & Recommendation**: Use the same heading style everywhere. Optionally tag each goal with A or B.

### Over-long line - Severity: Nit
* **Reviewer Lens:** `egm-structural`, `egm-style`
* **Affected Scope:** Line 404
* **Discrepancy Description**: About 120 columns; the rest of the document wraps at about 80.
* **Rationale & Recommendation**: Rewrap.

### CUJ label formatting differs from the baseline - Severity: Nit
* **Reviewer Lens:** `egm-structural`
* **Affected Scope:** Lines 111-138
* **Discrepancy Description**: The labels are written `**Given**:`, while the baseline writes `**Given:**`.
* **Rationale & Recommendation**: Move the colon inside the bold.

### The file-size evidence looks contradictory - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 159-161
* **Discrepancy Description**: The text says the full binary buffer is copied, yet the files are about 35 KB smaller.
* **Rationale & Recommendation**: Say where the difference comes from (e.g. the trimmed JSON).

### Undefined or colloquial terms; freeze date missing - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 183, 210, 240, 336, 425
* **Discrepancy Description**: "cápsula de reemplazo" and `secs` are never defined. "la pareja no queda vieja" is colloquial. "freeze" has no date; the brief gives 2026-11-26.
* **Rationale & Recommendation**: Define each term once, write "desactualizada" instead of "vieja", and give the freeze date.

### The FADE claim is untested - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 244-246
* **Discrepancy Description**: The claim that FADE avoids pose jumps while keeping a sharp hit is perceptual and hasn't been tested.
* **Rationale & Recommendation**: Present it as a starting value to be tuned in rehearsal.

### Leftover hedge - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 25-26
* **Discrepancy Description**: "si la etiqueta se complica" no longer applies, because Part B is now a single CSS change.
* **Rationale & Recommendation**: Delete the clause.

### Line 277 refers to a question only the brief asks - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Line 277
* **Discrepancy Description**: "La pregunta ... desaparece" assumes the reader has seen the brief.
* **Rationale & Recommendation**: State the outcome directly: the dead-piece summary is kept because the roster stays.

### NFR wording and an absolute claim - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 401-402
* **Discrepancy Description**: "Mientras no suenan" uses the wrong verb. "no cuestan nada por cuadro" hasn't been measured.
* **Rationale & Recommendation**: Write "se reproducen" and "costo por cuadro despreciable mientras están inactivas".

### G7 overstates what the flag restores - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 79-80 vs 138-140, 405-406
* **Discrepancy Description**: G7 says the flag goes back to today's 5 clips, but the `counter` fix stays and the extra clips are still loaded.
* **Rationale & Recommendation**: Reword G7 as "desactiva el gesto de victoria y los pasos".

### Ambiguous "G3" reference - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Line 418
* **Discrepancy Description**: The reference means `dejarik_ar.md` G3, but this document has its own G3.
* **Rationale & Recommendation**: Write "dejarik_ar.md G3".

### Diagram doesn't match the prose - Severity: Nit
* **Reviewer Lens:** `egm-style`
* **Affected Scope:** Lines 291-301
* **Discrepancy Description**: `#turn` and `#notice` appear without explanation. `#errors`, discussed at line 284, is missing from the diagram.
* **Rationale & Recommendation**: Add `#errors`, and either explain `#turn` and `#notice` or remove them.

### Part B problem statement overstates the issue - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 55-57 vs 263-267
* **Discrepancy Description**: The roster is covered only while the debug overlay is on, not "durante la demo" in general.
* **Rationale & Recommendation**: Limit the claim to when debug is on.

### Bottom-left roster placement not checked against the video - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 269-273
* **Discrepancy Description**: Player 0's pieces likely sit low in the frame, so an 8-row roster at bottom-left may cover them. Readability through Teams compression hasn't been checked.
* **Rationale & Recommendation**: Verify in rehearsal with the real camera framing and a Teams share, and add it to "Límites conocidos".

### Return-to-idle guard has no stated mechanism - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 186-190
* **Discrepancy Description**: The spec doesn't say how "otro clip arrancó" is detected, or what happens to the gesture's promise if a crossfade stops the action.
* **Rationale & Recommendation**: Add one sentence on each, e.g. "check that the current action is still win when the promise resolves; an unresolved promise is fine".

### `lastFight` lifecycle - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 196-210
* **Discrepancy Description**: The spec doesn't say when `lastFight` is cleared or what happens if it is null.
* **Rationale & Recommendation**: Clear it after the `death` handler uses it, and null-check it so a stray `death` can't pick a stale pair.

### Clip-renaming edge cases and drift in related docs - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 84-86, 153-157
* **Discrepancy Description**:
  - The brief strips the prefix `Armature|` and the spec strips `CharacterArmature|`.
  - Two source clips could map to the same name (e.g. Punch and Headbutt both becoming `attack`).
  - Three related documents still describe 5 clips: `docs/assets_checklist.md` (line 37 and the review step), `dejarik_ar.md` item 35a, and the `SOURCES.md` table.
* **Rationale & Recommendation**: Strip everything up to `|` and detect name collisions. List the doc updates in the same commit.

### `console.warn` under `?clips=basic` - Severity: Nit
* **Reviewer Lens:** `egm-design`
* **Affected Scope:** Lines 180-184
* **Discrepancy Description**: The spec doesn't say whether the one-time warning fires when `MOMENTS.win` is intentionally `null`. If it does, it is noise.
* **Rationale & Recommendation**: Suppress the warning when the null is intentional.
