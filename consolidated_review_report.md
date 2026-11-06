# Consolidated Review: `docs/designs/hand_interaction.md`

Mode: uninterrupted, all five stages, one round each, no fixes applied.
Split: FeatureRange 1-507, DetailedRange 508-927. Goldfish context: none (the doc has no markdown links).
Stage reports:
- [zoom_out_report.md](zoom_out_report.md) (Stage 5)
- [comprehension_report.md](comprehension_report.md) (Stage 6)
- [critic_report.md](critic_report.md) (Stage 7)
- [intermediate_zoom_out_report.md](intermediate_zoom_out_report.md) (Stage 8)
- [implementation_readiness_report.md](implementation_readiness_report.md) (Stage 9)

All 10 reviewer runs completed. None failed.

## Bottom line

**Not ready to implement.** The architecture holds up: four reviewers checked its claims about the current code, and none of those claims is wrong. The goals and the fix for the root problem are sound. But the central piece, the `Confirm` state machine, is wrong as specified:

- After a "salió" cancel, it re-activates `Pinch` in the same frame.
- On the next frame it crashes the hands thread on `cell_center(None)`.
- It never makes the player open the fingers before trying again.
- It cancels legitimate locks near a cell's edge.
- It leaves the plan-B `dwell` mode unable to play a turn.

Five independent reviewers found this. I confirmed it against `dejarik/hands.py:30-38` and `dejarik/board.py:70-77`.

Most of the remaining work is a short list of edits. Stage 8 shows that one change, a merged state machine (A1), closes about 12 findings at once.

## 🔴 Blockers

**A1. Rewrite `Confirm` as one self-contained state machine.**
- Today it is a wrapper that drives `Pinch` through `update(None)` side effects.
- Use Stage 8's table: fields `armed`, `lock_cell`, `lock_xy`, `t0`, `reason`.
  - Lock the cell that is shown (`shown`) and record `xy` at lock time.
  - Cancel when the fingertip moves more than `r` from `lock_xy`, the fingers open, or the hand is lost.
  - Fire once, then stay disarmed until release.
  - "Release" means metric > `off`, or the hand lost. In `dwell` it also means moving more than `r` from `lock_xy`.
- Write the table once, in Technical Plan section 3, and delete the step list at L559-586.
- `hold = (t - t0) / hold_s`. Guard the division for `hold_ms = 0`.
- Convert mm to m once in `gesture_params`.
- Closes: the re-arm crash, the edge-cell loop, the dwell two-tap problem, the highlight/lock mismatch, the `Pinch`-internals coupling, the two disagreeing copies, and the units ambiguity.

**A2. Add a short Risks & Mitigations section (about 5 rows) that points at mitigations already in the doc.** The standard requires it. Rows:
- open hand hovering triggers the gesture → G2 test
- world-landmark depth may not help → the 2D/3D log (A4)
- `dwell` usability → plan-B criterion, L919
- no separation in E1 → `dwell`, then the mouse or the ArUco pointer
- the box misses the forearm or a tall creature → accepted (OQ1)

Leave out a "security" row: `hold` and `box` are plain numbers, and no trust boundary is crossed.

## 🟡 Major

**A3. Cut `gesture = "pinch"` mode.**
- Remove the `[hands.touch]`/`[hands.pinch]` subtables (use flat keys in `[hands]`), the old-key warning, OQ3, Alternative M and the concepts_brief edit at L847-849.
- The Problem section already shows the in-air pinch is wrong, and the safety nets are the mouse and `dwell`.
- This is what makes A1 simple. *Your decision:* this reverses Change 4, which you decided against the brief.

**A4. Log the 2D ratio `d2(8,12)/d2(0,9)` in `dbg` next to the 3D metric, and add "open hand hovering over a valid destination" to the E1 histograms and the G2 test.**
- This answers two concerns: the 3D advantage is unproven, and the default `on = 0.35` (about 3.2 cm) counts a relaxed open hand as "closed".
- Logging is enough; no new gesture mode is needed.

**A5. Make `hands_loop` explicit.**
- Write the no-hand branch so it publishes and then `continue`s, as `hands.py:88-91` does today.
- Give the exact `dbg` dict for both branches.
- `metric`: `None if math.isinf(m) else round(m, 3)`. Today's `or None` turns dwell's 0.0 into `None`, and `inf` would be rejected by `JSON.parse`.
- Give the exact formula for `extended`.
- Use `p["..."]` (dict access). Note that `cfg` is `cfg["hands"]`.

**A6. Make `scale_hand` tolerate old recordings.**
- Use `hand.get("px")` / `hand.get("box")`. Don't add keys that are missing.
- Add a test with the legacy `{cell, pinch, px}` dict. `recording.replay` feeds old headers through `encode_remote`, so this path is real.

**A7. Bring the test list up to the coverage rule at L899-901.**
- Add tests for: "suelta", the re-arm after a cancel, `dwell` two taps, `extended` hysteresis, and `box` math.
- Pass `cell=6` synthetically in `test_confirm_uses_locked_cell`: 10 mm from the centre of cell 5 does not reach cell 6.
- State the `Confirm` parameters each test builds with.

**A8. Fix the Open Questions status.**
- Mark OQ1-OQ5 resolved (or still open) consistently with Alternatives K-N and "Cambios respecto del brief".
- Move resolved ones out of Open Questions, or move the whole section after the Technical Plan.

**A9. Add one milestones line to the Overview.**
- Define E0-E4, "el control" and who runs it (the 5 students).
- Give one date for the control, against the 18/11 E4 cut-off and the 20/11 freeze.

**A10. Rewrite the rejection reasons as trade-offs, not "Rechazado por el autor" / "(aprobó el Technical Plan)".**
- Say once at L344 that the author decided.
- C needs its technical reason.
- G is a deferral condition, not a rejection.
- E is "kept as plan B", not rejected.

**A11. Settle the `docs/protocol.md:3` rule.** It says the file is frozen and any change bumps `v`. Amend line 3, or say why additive fields don't bump it.

**A12. Fix the browser specifics.**
- `#hint` overlaps `#combat` (`style.css:33`). Give exact CSS.
- The E3 block must always run, so `pass` can decay back to 0.
- Compute the creature position with `getWorldPosition` plus the shared NDC→pixel mapping from `project`.
- Import `cellCenter` in main.js.
- Make `uPass` a per-material uniform.

**A13. Make G3 and G4 testable.**
- Name a pass threshold, for example "2 of 3 first-time testers".
- Narrow G3's "sin mirar la pantalla" claim, or test it with sound only.

**A14. Use one phrase for the gesture everywhere (G7).**
- Make the `HINT` constant the single source.
- Note that `hand.pinch` keeps its name but now means "gesture closed".

**A15. Fix the factual claims that are wrong.**
- L43 "~4 cm" contradicts OQ4: use 37 mm radial and 28 mm arc.
- "Sin bajar el brillo" contradicts the opacity drop to 0.35.
- "Same smoothing as `poseAlpha`" is wrong: 0.05 s vs 0.1 s.
- Opacity "se componen": scope it to `pass`. Tracking and death still overwrite each other, which predates this design; don't add a new factor.
- Mark ~1.25, 3-4 cm and +10-20 ms as estimates.

**A16. Promote "Additional Resources" and "Cambios respecto del brief" to H2, and turn the cited files into relative Markdown links.**

**A17. Name the demo_script row for the host's first use of the hand, and fill all 4 columns of the new row.**

## 🟢 Nits (grouped)

**A18. Shader.** Raise only the flicker amplitude, not the frequency: `sin(uTime·(37+40·uPass))` makes the flicker chaotic while `uPass` fades.

**A19. Cosmetic constants and their conflict.**
- Drop the exact tones, sizes and strings in favour of constraints.
- The ring offset is "~60 px" at L319 and "(+40, -40)" at L770. Pick one, and say whether it moves the centre or the corner.

**A20. Undefined terms.**
- `.dj`, the remote viewer, `poseAlpha`, the ArUco pointer, `hand.px`, the MediaPipe landmark numbering.
- E1 is used before it is defined.
- "Un radio" in G2.

**A21. Formatting.**
- The `json` block doesn't parse.
- "Dónde vive cada cosa" is unnumbered.
- L85 runs past the wrap width.
- Horizontal rules are inconsistent.
- The TOML ordering rationale is wrong.

**A22. Wording.**
- English mixed into Spanish prose.
- "corrido" has three meanings.
- The ratio notation varies.
- "anillo" means both the hold ring and the board rings.
- Some "Por qué" lines add nothing.
- Vague words: "mucho trabajo", "se explica fácil", and others.

**A23. Small code details.**
- `import math` / `math.dist`; `dist` clashes with the distortion parameter.
- `cell_center` is missing `spec`.
- The import check should assert that MediaPipe was not loaded.
- `prevHint` is needed and not named.
- `holdStart` fires one frame late (say it's intended).
- The debug-line format is unspecified.
- The test's `net_cfg` needs `remote_quality`.

**A24. Optional.** Consider `OneEuro` on `lm2d[8]` instead of the 3-frame debounce, and let E0/E1 decide whether the debounce is needed at all.

**A25. Stale docs not in the file list:** `dejarik_ar.md:415, 911` and `concepts_brief.md:98, 296`. List them, or say on purpose that they stay unchanged.

## Recommended to skip

Reviewers raised these, but they add scope without enough payoff. Stage 8 argued against them and I agree:
- **An explicit `result` field or attempt counter (D-M4).** The remote never plays hold sounds (`you === 1`), and A1's `armed` flag closes the host-side gap.
- **A selectable 2D gesture mode (D-M2).** Logging it (A4) gives the same data.
- **A security risk row (D-B2).**
- **A frame-time budget (D-N9).**
- **A third opacity factor (S6 #3, D-N2).**

## Traceability matrix

| Action | Source findings |
|---|---|
| A1 | S6#1, S6#2, S6#6, S6#7, S7 D-B1, D-M3, D-M5, D-M6, D-N8, S-6, Z5-2, Z5-3, Z8-1, S9 IR-B1, IR-B2, CD-B1, CD-N3, IR-N6, ST-N1, ST-N4 |
| A2 | D-B2, S-1, Z8-4 |
| A3 | Z5-1, Z8-2, S6#8 |
| A4 | D-M1, D-M2, Z8-2 |
| A5 | S6#9, IR-M1, IR-M4, CD-M1, CD-N1, ST-M3, ST-M4, ST-N2, ST-N3 |
| A6 | IR-M2, CD-M2, D-N4 |
| A7 | IR-M3, CD-N4, ST-N7 |
| A8 | S6#4, S-4, ST-M4(S7), S-10 |
| A9 | S6#5, S6#14, D-N1, ST-M4(S7), Z8-5, ST-N11 |
| A10 | D-M7, S-3, S-11, ST-N7(S7) |
| A11 | CD-M3 |
| A12 | IR-M5, CD-M4, ST-M6, IR-N2, CD-N7, D-N3, D-N5 |
| A13 | ST-M2(S7), ST-M7, Z8-8 |
| A14 | ST-M3(S7), ST-M1(S9) |
| A15 | ST-M1(S7), ST-M5(S7), ST-M6(S7), ST-M5(S9), S6#3, S6#12, D-N2, D-N6, CD-N8, Z5-7, Z8-6 |
| A16 | S-2, S-5 |
| A17 | CD-M5, IR-N9 |
| A18 | Z5-5 |
| A19 | Z5-6, S6#10, IR-N1, IR-N8 |
| A20 | S6#11, S6#13, S6#14, S6#15, ST-N4(S7), ST-N8(S7) |
| A21 | S-7, S-8, S-9, S-12, CD-N6, ST-N6(S9) |
| A22 | ST-N1, ST-N2, ST-N3, ST-N5, ST-N6 (S7); ST-M2, ST-N5, ST-N8, ST-N9, ST-N10 (S9) |
| A23 | CD-N2, CD-N5, IR-N3, IR-N4, IR-N5, IR-N7 |
| A24 | Z5-4 |
| A25 | IR-N10, CD-N9 |
| Skipped | D-M4, Z8-3, D-N9, Z8-7 |

Finding IDs: S6# = comprehension_report; D- / S- / ST- = critic_report (design / structural / style); Z5- / Z8- = zoom-out reports; IR- / CD- / ST- = implementation_readiness_report.
