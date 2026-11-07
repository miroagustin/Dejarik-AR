# Goldfish Review Report: Stage 8 (Intermediate Zoom Out)

**Target:** `C:/Users/miroa/OneDrive/Documentos/Repos/Dejarik-AR/docs/designs/criaturas_canon.md` (full file, lines 1-673; not edited since Stages 5-7)

## Reviewer Status

| Reviewer | Status |
| --- | --- |
| `egm-zoom-out` | completed |

**Severity breakdown (new findings and severity changes only):** 0 Blocker, 4 Major, 1 Nit.

**Context check:** passes. The objective is still clear.

## Verdict

If every Stage 6/7 ask is applied as written, the design roughly doubles in length. It would gain a Risks section, CUJ 5, a glossary, a project intro, stop-motion alternatives, an A7 subsection for Run/Weapon, a CLI entry point for the flag, per-kind clip overrides, a Blender fallback clip, and the victory gesture on every exchange.

About a third of the Stage 6/7 findings go away with three cuts:

1. Drop Commit 4 (Run/Weapon). This was Stage 5 #1.
2. Drop the `?clips=basic` flag.
3. Replace `MOMENTS` with one `WIN_CLIP` constant. This was Stage 5 #2.

Make those cuts first, then apply what's left in its smallest form. The revised doc should be shorter than today's 673 lines.

## Prioritized Findings (Blockers -> Major -> Nits)

### `?clips=basic` flag should be cut (Stage 5 #4 raised from Nit to Major) - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** G7; CUJ 4 (lines 134-140); flag sentences in A2, A5 and the NFR; `BASIC ?` branches in item 9.
* **Discrepancy Description**: Stage 7 showed two problems with the flag:
  * It can't be reached from the host's `--app` window. That window has no address bar, and its URL carries the unprinted `host_token` (dejarik_ar.md:499, 265).
  * `STEP = 0` makes `walkTo` divide by zero.

  The flag is the source of three Stage 6/7 defects, and it doesn't work in the live demo, which is the one place it was meant for.
* **Rationale & Recommendation**: The web files are static and served locally, so rollback is `git revert` plus a reload. A decision made in rehearsal doesn't need a runtime switch. Remove `BASIC`, the flag clause in G7, CUJ 4, the flag sentences, and the `BASIC ?` branches. Reword G7 to "cada commit se revierte solo".

### Victory gesture restarts on `win` (Stage 5 #8 raised from Nit to Major) - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** `celebrate()` in A2/A3 and item 10; CUJ 3.
* **Discrepancy Description**: Stage 7 confirmed a visible defect. When the match ends, the final killer's gesture starts over, at the most visible moment of the match. Brief decision 2 shows the author wants the gesture to repeat in `win`, so it should stay.
* **Rationale & Recommendation**: Fix it in the shared function, not in each caller. Add one guard at the top of `celebrate()`: if `this.current` is already the win action, return. That fixes both the `death` path and the `win` path. In CUJ 3, write "sobreviviente".

### Applying the Stage 6/7 asks literally would bloat the design - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Whole document.
* **Discrepancy Description**: Six asks add new mechanism, not clarity:
  * a CLI flag or host key
  * a per-kind clip override
  * a Blender fallback clip
  * the gesture on every exchange
  * CUJ 5
  * an A7 subsection for Run/Weapon

  Four more asks add whole sections: Risks, a glossary, stop-motion alternatives, and a project intro. Most of these exist to document or patch scope the design doesn't need: the flag, Commit 4, and the `MOMENTS` indirection.
* **Rationale & Recommendation**: Revise in this order:
  1. Cut Commit 4, the flag, and `MOMENTS` (replace it with `WIN_CLIP`).
  2. Add the one-line `celebrate()` guard and a single global step clock.
  3. Add a Risks table of at most 5 rows, plus one sentence each for project context, outcome names, and `anim_done`.
  4. Make the wording fixes.

  Aim for a net line count below 673. The per-ask rulings are below.

### Technical Plan and Detailed Plan describe the same mechanisms twice - Severity: Major
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** A2-A5 (lines 167-250) against items 9-11 (lines 529-580); the A3 diagram against item 10.
* **Discrepancy Description**: Both sections specify the same behavior at the same level of detail: the `play` translation, the return-to-idle guard, `walkTo` rounding, the step accumulator, and the `fight` pair and when it's cleared. They already disagree: A2 has `events.js` calling `play("win")`, while item 10 calls `celebrate()`. Stages 6 and 7 reviewed only lines 1-428, so each of their fixes would also have to be copied by hand into items 9-11.
* **Rationale & Recommendation**: Keep behavior and rationale in the Technical Plan only. Cut items 9-11 down to file, scope, and a pointer ("implementa A2-A5"). Keep the few facts that appear nowhere else, such as which file and whether a function is exported. Several of the code-level weeds from Stage 5 #9 go with them.

### Perceptual risks have no rehearsal gate - Severity: Nit
* **Reviewer Lens:** `egm-zoom-out`
* **Affected Scope:** Verification Plan (lines 656-667); the manual step between commits 1 and 2 (lines 521-523).
* **Discrepancy Description**: The likeliest failures are judgment calls:
  * which victory clip reads well
  * whether 12 fps judders on Teams
  * whether the roster covers pieces

  Only the clip choice has a manual gate. The `STEP` and roster checks are scattered or missing.
* **Rationale & Recommendation**: Expand the manual step into one rehearsal checklist: pick the clip, tune `STEP` while watching the Teams share, and check roster placement on the real camera framing. Point the Risks table at this checklist. The table can then drop a separate "rehearsal check" column.

## Rulings on Stage 6/7 Asks

Each ruling is one of: apply as asked, apply smaller, cut scope instead, or drop.

### Comprehension report (Stage 6)

| # | Ask | Ruling |
| --- | --- | --- |
| 1 | Project never introduced | **Apply smaller.** One sentence in the Overview (AR holochess for a Teams demo; Python server, browser client, hand or mouse input) plus a link to the dejarik_ar.md Overview. |
| 2 | Run/Weapon status | **Cut scope instead.** Delete Commit 4 (items 13-15, lines 602-654), the "más uno opcional" text (403-404, 431), and `run` in LOOPING (466). List `run` and `weapon` under Non-Goals and in the "sin usar a propósito" section of SOURCES. |
| 3 | `anim_done` / 5 s wait | **Apply smaller.** One sentence in G5. |
| 4 | Timing math | **Apply smaller.** Fix the number once in A3 (about 2.6 s, about +1.07 s over today, if the gesture overlaps the fade). Alternative E points to A3. |
| 5 | "hit" means three things | **Apply smaller.** One sentence naming the engine outcomes (`hit`, `counter`, `tie`). Qualify only the ambiguous spots (CUJ 1/2, line 226). No glossary section. |
| 6 | Title promises a label | **Apply as asked.** Rename the title and Part B. |
| 7 | Undefined terms | **Apply smaller.** Define "cápsula de reemplazo" once. Give 2026-11-26 as the delivery date. Most uses of "dwell"/`hold` go away once Alternative A is trimmed. Drop `&still`. |
| 8 | Alternative labels | See the Critic "Alternative labels" ruling. |
| 9 | Brief-only references | **Apply smaller.** Turn them into links, and state the outcome of line 277 directly. |
| 10 | Clip names | **Apply smaller.** One parenthetical in A1 (attack=Punch, hit=HitReact, die=Death). |
| 11 | Clock instruction | Resolved by the single-clock fix. |
| 12 | 2-square rule | **Cut scope instead.** It goes away with Commit 4. |

### Critic report (Stage 7)

| Ask | Ruling |
| --- | --- |
| No Risks section (Blocker) | **Apply smaller.** At most 5 rows (Riesgo / Mitigación / Respaldo en vivo): (1) the gesture reads badly, so leave the win clip null; (2) stepped motion judders on Teams, so tune `STEP` while watching the share; (3) the gesture gets stuck or overrides `walk`, so add the `this.current` guard; (4) `fight` goes stale, so clear it after `death`; (5) the roster covers pieces. Move "Límites conocidos" (279-289) into the table. No rows for defects that the cuts remove. |
| Rejections credited to the author without links (Blocker) | **Apply smaller.** Start each "Motivo del rechazo" with the trade-off; this is mostly reordering. Link the brief once per rejection. Collapsing the three label alternatives (Stage 5 #6) leaves four rejections to fix instead of seven. |
| Flag unreachable from the host window | **Cut scope instead.** Drop the flag. No CLI flag and no host key. |
| `STEP = 0` breaks walking | **Cut scope instead.** It goes away with the flag. |
| Two clocks (Stage 5 #3) | **Apply smaller.** One global grid: `floor(performance.now() / STEP) * STEP`. The mixer updates when that value changes, and `tween` uses it. This removes `stepMixer` and the accumulator. No classification list. |
| Gesture plays twice at game end | **Apply smaller.** One-line guard in `celebrate()`. |
| G1 vs G6 (gesture on every exchange) | **Apply smaller; don't extend the gesture.** Add one sentence to G1: the attack/hit pair already shows who won a non-lethal exchange. |
| No arms-up clip, no fallback | **Apply smaller.** Write "gesto de victoria (Wave o Yes)" and "si ninguno se lee bien, queda null". No per-kind override and no Blender clip. |
| Commit plan vs A/B | **Cut scope instead.** Without Commit 4, A = commits 1-2 and B = commit 3. Use "commit" as the only unit. No A7. |
| Alternative labels | **Apply smaller.** Reletter in order, add one line for the chosen option ("B (elegida)"), and make C stand alone. |
| Title/Part B names a dropped feature | **Apply as asked.** |
| win/hit/attack overloaded | **Cut scope instead** for `win` (`WIN_CLIP` removes the key). For hit/attack, use the one-sentence qualifier. |
| Timing arithmetic | **Apply smaller.** Same fix as Comprehension #4. |
| Part B has no user journey | **Drop.** At most, add "(ver control del commit 3)" to G4. |
| Additional Resources / Future Improvements nested under NFR | **Apply as asked.** Heading-level change only. |
| No stop-motion alternatives | **Apply smaller or drop.** At most one rejected line: baking stepped keys into the glTF. |
| Nits: wording, EN/ES mix, line 404, CUJ format, hedge at 25-26, NFR wording, FADE | **Apply as asked.** |
| Nit: file-size evidence (159-161) | **Apply smaller.** Delete the KB figures. |
| Nit: diagram (291-301) | **Cut scope instead.** Delete the diagram. |
| Nit: idle guard and `fight` lifecycle | **Apply smaller.** One clause each in A2/A3, or resolve through the duplication finding. |
| Nit: renaming edge cases | **Apply smaller.** One line: "skip a name already present". Cut the collision fixture. Keep the `assets_checklist.md` and `SOURCES.md` edits. Drop the dejarik_ar.md 35a edit. |
| Nit: `console.warn` under the flag; G7 overstates | **Cut scope instead.** Both go away with the flag. |
| Nit: roster vs camera framing | **Apply as asked**, as Risks row 5. |

## Unchanged from Stage 5

Stage 5 #1 (Commit 4), #2 (`MOMENTS`) and #3 (two clocks) stay Major. The rest stay Nit, except #4 and #8, which are raised above.

**Keep:**
* all clips in adapt
* the independent `counter` fix
* not awaiting the gesture
* the CSS-only roster move
