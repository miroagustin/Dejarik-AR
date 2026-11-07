# Consolidated Review Report: criaturas_canon.md

**Target:** `docs/designs/criaturas_canon.md` (673 lines). FeatureRange 1-428, DetailedRange 429-673.
**Mode:** Consolidated report, all five stages, no checkpoints.
**Context given to reviewers:** `concepts_brief_personajes.md`, `docs/assets_checklist.md`, `docs/designs/dejarik_ar.md`, `assets_src/SOURCES.md` (not given to Stage 6).

## Stage reports

| Stage | Reviewers | Status | Raw findings (B / M / N) | Report |
| --- | --- | --- | --- | --- |
| 5 Initial Zoom Out | zoom-out | completed | 0 / 3 / 7 | [zoom_out_report.md](zoom_out_report.md) |
| 6 Comprehension | comprehension | completed | 0 / 6 / 6 | [comprehension_report.md](comprehension_report.md) |
| 7 Critic | design, structural, style | all completed | 2 / 14 / 19 | [critic_report.md](critic_report.md) |
| 8 Intermediate Zoom Out | zoom-out | completed | 0 / 4 / 1 | [intermediate_zoom_out_report.md](intermediate_zoom_out_report.md) |
| 9 Implementation Readiness | impl-readiness, codebase-details, style | all completed | 0 / 13 / 14 | [implementation_readiness_report.md](implementation_readiness_report.md) |

The document was not edited between stages, so every finding applies to the current text.

## Verdict

The design is not ready to implement. The core ideas held up in every stage:
- keep all 14 clips in `adapt_glb`;
- show the defender striking on `counter`;
- do not await the victory gesture;
- move the roster with CSS only.

The problems come from extra scope around that core. Three pieces cause most of the findings:
- Commit 4 (Run/Weapon);
- the `?clips=basic` flag;
- the `MOMENTS` map, of which only `win` maps to a different name.

Each causes defects or ambiguity in at least three stages. Removing them closes about a third of all findings without writing anything new. The doc should end up shorter than 673 lines.

Applying every Stage 7 recommendation as written would do the opposite: roughly double the doc and add new mechanisms (a CLI flag, per-kind overrides, a Blender fallback clip, CUJ 5, an A7 subsection). Stage 8 ruled on each of those requests. This report follows those rulings except where noted under "Contested points".

## Recommended order of work

1. **Cut first:** M1, M2, M3. These remove findings before you spend effort fixing them.
2. **Fix real defects:** M4 (one clock), M5 (`celebrate()` guard), M14-M17 (plan defects found against the code).
3. **Meet the standard cheaply:** B1, B2 (Risks table, rejection wording).
4. **Clarity:** M6-M13, then Nits.

## Action items

### 🔴 Blockers

**B1. Add a short Risks & Mitigations section.**
- The feature-spec standard requires one, and the base doc `dejarik_ar.md` has one.
- Add it between Alternatives and NFR, with at most 5 rows (Riesgo / Mitigación / Respaldo en vivo):
  1. The victory gesture reads badly. Fallback: win clip `null`.
  2. 12 fps stepping judders on the Teams capture (15-30 fps). Mitigation: tune `STEP` while watching the share from another account.
  3. The gesture sticks or overrides `walk`. Mitigation: the M5 guard.
  4. `lastFight` goes stale. Mitigation: clear it after `death`.
  5. The roster at bottom-left covers pieces in the real camera framing.
- Move "Límites conocidos" (lines 279-289) into the table.
- Add one rehearsal checklist to the Verification Plan (clip choice, `STEP` tuning, roster placement) and point the table at it.
- Do not add rows for defects that M1-M3 remove.

**B2. Reword the seven rejections (lines 320-393).**
- Each "Motivo del rechazo" opens with "rechazada por el autor" and has no link. The standard forbids that.
- Start each rejection with its technical trade-off and link the brief once (for example `[brief, decisión 2](../../../briefs/concepts_brief_personajes.md#...)`).
- Alternative C needs a real trade-off: it duplicates the existing highlight and needs a stance layer.
- Collapsing the three label alternatives (M12) leaves four rejections to fix instead of seven.

### 🟡 Major

**M1. Cut Commit 4 (Run/Weapon).**
- It isn't needed for any goal and adds the most new machinery.
- It also brings five plan defects:
  - `KIND_MOMENTS` throws a ReferenceError if it isn't created;
  - the two-leg run stops on idle at the middle cell;
  - run speed follows the requested moment, not the clip that actually plays;
  - the viewer loses Punch after the soldado's attack becomes Weapon;
  - `run` and `weapon` stay "pending" if the commit is skipped.
- Action:
  - Delete items 13-15 (lines 602-654), the "más uno opcional" text (403-404, 431) and `run` in LOOPING (466).
  - List `run` and `weapon` under Non-Goals and in SOURCES' "sin usar a propósito" list.
  - Move the idea to Future Improvements.

**M2. Cut the `?clips=basic` flag.**
- It can't be used in the place it was meant for: the host runs in a Chrome `--app` window with no address bar, and its URL carries an unprinted `host_token`.
- `STEP = 0` makes `walkTo` divide by zero, so walking breaks while the flag is on.
- It also adds `BASIC ?` branches to every feature and a misleading missing-clip warning.
- Rollback becomes `git revert` plus a reload.
- Action: remove `BASIC`, CUJ 4, the flag sentences in A2, A5 and the NFR, and the branches in item 9. Reword G7 to "cada commit se revierte solo".

**M3. Replace `MOMENTS` with one constant, `WIN_CLIP`.**
- Five of the six entries map a name to itself.
- The doc contradicts itself on who uses the map: A2 has `events.js` calling `play("win")`, while item 10 calls `celebrate()`.
- `win` is also both a server event and a moment key, which confuses line 201.
- `MOMENTS` is exported, but nothing imports it.

**M4. Drive stop-motion from one clock.**
- The mixer steps on an accumulator in `Army.update`, while `walkTo` steps on its own `performance.now()`.
- The two 12 fps grids are out of phase, so legs and body change pose up to 83 ms apart.
- The `stepMixer(mixer, dt, acc)` signature also conflicts with "one shared accumulator": used the obvious way, it adds `dt` up to 8 times per frame.
- The plan states this as a warning ("hay que cuidar…", line 554) and never decides it.
- Action:
  - Use one global grid, `floor(performance.now() / STEP) * STEP`. The mixer updates when that value changes, and tweens read it.
  - Say which motions are stepped (position, facing) and which stay smooth (flash, fades, shake).
  - Add one rejected alternative: baking stepped keys into the glTF.

**M5. Stop the victory gesture from restarting at game end.**
- On the final kill, `death` starts the gesture and `win` immediately restarts it on the same survivor, at the most visible moment of the match.
- Fix it once: at the top of `celebrate()`, return if the win action is already playing. That covers both paths.
- In CUJ 3, write "sobreviviente" instead of "el atacante".

**M6. Remove the duplicate description in the Detailed Plan.**
- A2-A5 and items 9-11 describe the same mechanisms at the same level of detail, and they already disagree (see M3).
- Shrink items 9-11 to the file, the scope and "implementa A2-A5". Keep only facts found nowhere else.
- This also removes most of the code-level detail (Stage 5 #9).

**M7. Make G1 achievable and consistent with G6.**
- G1 promises "levantando los brazos", but neither Wave nor Yes raises the arms, and the question has no decision rule or fallback.
- G1 limits the gesture to fights that end in a death, while G6 asks viewers to say who won any exchange.
- Action:
  - Rewrite G1 as "gesto de victoria (Wave o Yes)".
  - Add who decides (at real scale, through Teams) and the fallback: if neither reads well, `WIN_CLIP = null`.
  - Either state why non-lethal fights get no gesture and narrow G6 to match, or extend the gesture. See "Contested points".
  - Give G6 a way to pass or fail.

**M8. Order the Wave/Yes decision in the plan.**
- Commit 1 writes the choice into SOURCES.md before it is made, and no commit lists the follow-up edit.
- Either write "pendiente" in commit 1 and add the edit to commit 2, or make the choice a step before commit 1.

**M9. Rename the title and Part B.**
- "Etiqueta de vida" promises a floating HP label, which the design dropped (line 260).
- Example: "Parte B: roster legible con debug". Keep "etiqueta" only in the rejected alternatives.

**M10. Add four context sentences.**
These are not glossaries or sections:
1. Overview: what the project is (AR holochess for a Teams demo, Python server, browser client, hand input), with a link to `dejarik_ar.md`.
2. G5: the `anim_done` handshake (the server waits up to 5 s per event, the client times out at 8 s, input stays blocked meanwhile).
3. Name the engine outcomes (`hit`, `counter`, `tie`) once, and qualify "resultado / evento / clip" only where it is ambiguous (CUJ 1/2, line 226).
4. A1: map contract clips to source names (attack = Punch, hit = HitReact, die = Death).

**M11. Fix the timing arithmetic (lines 211-216, 354-356).**
- The text says the gesture overlaps the fade, but "3.2 s" and "+1.7 s" add them one after the other.
- With overlap, an awaited handler takes about 2.6 s, about +1.07 s over today.
- State the figure once in A3 and have Alternative E point to it. E's rejection depends on this number.

**M12. Reletter the alternatives.**
- The clip alternatives are A, C, D, E with no B, yet C is "B + salto".
- The label alternatives are b, c and one with no letter.
- Add "B (elegida)" and "a (elegida)" lines that point to the Technical Plan, make C stand alone, and collapse the three label alternatives (Part B is a one-line CSS change).

**M13. Promote "Additional Resources" and "Future Improvements" to H2.**
They currently sit under NFR.

**M14. Make the commit 2 check reproducible.**
- The check replays a `.dj` file, but replays contain no combat, so there is no `counter` to see.
- Give a seed or a saved-state fixture that produces a counter.

**M15. Specify duplicate-name handling in `adapt_glb` in one line.**
- The rule: skip a name already present, and keep the source order.
- Stage 9 asks for an extra-vs-extra test, while Stage 5 says the real models can't hit this case.
- Write the rule and drop the collision fixture.

**M16. Fix the verification command for PowerShell.**
PowerShell does not expand `*.glb`. Use explicit paths or `Get-ChildItem`.

**M17. Fix item 6.**
It "adds" files that are already tracked in git. State what actually changes.

**M18. Bring the commit 3 check in line with the spec.**
- The check is stricter than the overlaps the spec already accepts. Align it with the accepted limits.
- Do not add CUJ 5. At most add "(ver control del commit 3)" to G4.

### 🟢 Nits

- **N1. Wording.** Mixed English/Spanish labels, over-long lines (431 and others), CUJ label format, the leftover hedge at 25-26, NFR wording and its absolute claim, the untested FADE claim. (Stage 7 style nits, Stage 9 #26-27)
- **N2. Undefined terms.**
  - Define "cápsula de reemplazo" once.
  - Give the freeze date. Stage 8 cites 2026-11-26 from `dejarik_ar.md`; confirm it.
  - Say that "8 piezas" means 4 kinds per side.
  - Most uses of `hold`/dwell go away when the alternatives are trimmed. (Stage 6 #7, Stage 7)
- **N3. Brief-only references.** State the content inline or link it: "brief, etapa 1", "decisión 2", and the question at line 277. Overlaps B2. (Stage 6 #9, Stage 7)
- **N4. Delete clutter.** The diagram at 291-301 (it doesn't match the prose), the KB file-size figures at 159-161, and background text copied from the brief. (Stage 7, Stage 5 #7)
- **N5. One clause each** for the return-to-idle guard and the `lastFight` lifecycle in A2/A3. Resolved by M6 if the plan points to A2-A5. (Stage 7)
- **N6. Document drift.**
  - Update `assets_checklist.md` and SOURCES.md for 14 clips.
  - `dejarik_ar.md` still says exactly 5 clips. See "Contested points". (Stage 7, Stage 9 #21)
- **N7. Small plan fixes.** (Stage 9 #14, #16, #17, #22, #23, #25)
  - The SOURCES table change and its stale regeneration command.
  - The wrong docstring is named.
  - The test edit cites a line number and leaves a stale comment.
  - The lint step is vague.
  - The `LOOPING` literal is ambiguous (`jump_idle` doesn't loop).
  - The mirror key "F" is unconfirmed.
- **N8. Narrow the revert claim** to what each commit actually restores. (Stage 9 #15)
- **N9. `BASIC` parses the URL again.** Removed by M2. (Stage 9 #19)

## Contested points

Reviewers disagreed on these points. Each entry gives my position and the strongest argument against it.

1. **Cut the flag (M2) versus give it a real entry point (Stage 7).**
   - I side with the cut. The flag fails in the demo window, and it causes three defects.
   - Counter-argument: `git revert` during a live demo needs a terminal and a reload, maybe a server restart, while the flag needed none.
   - Check before cutting: if the Python server reads `web/` from disk on every request, a reload is enough and the cut holds. If not, rollback in the demo means a restart. Then write that step into the Risks table instead of keeping the flag.
2. **Gesture on every exchange (Stage 7 option) versus lethal-only plus a narrower G6 (Stage 8).**
   - Stage 8 argues that the attack/hit pair already shows who won a non-lethal exchange.
   - Counter-argument: the brief and the Overview both describe the winner celebrating after every won fight. Most exchanges are non-lethal (damage 1, HP 2-3), so lethal-only means the gesture is rare.
   - Extending it costs little, because the gesture isn't awaited.
   - This is a product decision for the author. Either choice is fine, as long as G1, G6 and the Overview agree.
3. **Editing `dejarik_ar.md`.**
   - Stage 8 says drop the edit. Stage 9 found that `dejarik_ar.md` states exactly 5 clips, which becomes false after commit 1.
   - I side with Stage 9: one line, or the base doc contradicts the code.
4. **Severity of B1/B2.**
   - They are Blockers only because the standard requires them. Neither stops the code from working.
   - Both are cheap: one table, plus reordering seven sentences.

## Traceability matrix

Raw finding IDs: `Z5-n` = Stage 5 #n, `C6-n` = Stage 6 #n, `K7-<topic>` = Stage 7 heading, `Z8-<topic>` = Stage 8 heading, `R9-n` = Stage 9 #n.

| Action | Raw findings |
| --- | --- |
| B1 | K7-risks, K7-roster-vs-video, Z8-rehearsal-gate |
| B2 | K7-rejections, C6-9 (part) |
| M1 | Z5-1, C6-2, C6-12, K7-run-weapon, R9-5, R9-6, R9-7, R9-8, R9-24 |
| M2 | Z5-4, Z8-flag, K7-flag-unreachable, K7-STEP0, K7-console-warn, K7-G7-overstates, R9-19 |
| M3 | Z5-2, K7-win-hit-attack (win part), R9-12, R9-18 |
| M4 | Z5-3, K7-two-clocks, K7-no-stopmotion-alts, C6-11, R9-1, R9-2 |
| M5 | Z5-8, Z8-gesture-restart, K7-double-gesture, R9-20 |
| M6 | Z8-duplication, Z5-9 |
| M7 | K7-G1-vs-G6, K7-arms-up, Z5-10 |
| M8 | R9-4 |
| M9 | C6-6, K7-title |
| M10 | C6-1, C6-3, C6-5, C6-10, K7-win-hit-attack (hit/attack part) |
| M11 | C6-4, K7-timing |
| M12 | C6-8, K7-labels, Z5-6 |
| M13 | K7-nested-headings |
| M14 | R9-3 |
| M15 | Z5-5, R9-9, K7-renaming-edge-cases |
| M16 | R9-10 |
| M17 | R9-11 |
| M18 | R9-13, K7-partB-no-CUJ |
| N1 | K7-EN/ES, K7-long-line, K7-CUJ-format, K7-hedge, K7-NFR-wording, K7-FADE, R9-26, R9-27 |
| N2 | C6-7, K7-undefined-terms |
| N3 | C6-9, K7-line-277 |
| N4 | K7-diagram, K7-file-size, Z5-7 |
| N5 | K7-idle-guard, K7-lastFight |
| N6 | K7-doc-drift, R9-21 |
| N7 | R9-14, R9-16, R9-17, R9-22, R9-23, R9-25 |
| N8 | R9-15 |
| N9 | R9-19 (shared with M2) |
| Superseded (not adopted) | K7 asks for a CLI flag or host key, per-kind clip override, Blender fallback clip, CUJ 5, A7 subsection, glossary section; style reviewer's `&still` finding (dropped in Stage 9: `main.js:206` defines it) |
