# Stage 8: Intermediate Zoom Out Review

Target: `docs/designs/hand_interaction.md` (lines 1-927). Reviewer: egm-zoom-out (zoom-out-standard). It also read the Stage 5-7 reports, `dejarik/hands.py` and `dejarik/board.py`.
**Context sufficiency: PASS. Verdict: 1 Blocker, 3 Major, 4 Nits.** No document edits were made between stages.

The fixes queued from Stages 5-7 are mostly right on their own. Applied one by one, though, they would roughly double the `Confirm` text, which is already written twice. Most of them collapse into one structural change (Z8-1). A few proposed additions are not worth their cost (Z8-3, Z8-4, Z8-6).

## Code fact that settles Stage 6 #1 and Stage 7 D-M3
`Pinch.update(None, t)` only clears `closed_since` and `fired` (`hands.py:31-32`). On the next frame, a metric below `on` reactivates it immediately (`hands.py:33-34`). Nothing forces the fingers to open again. Three consequences:
- The design's cancel-by-`update(None)` re-locks on the next frame.
- `test_confirm_cancels_outside_radius` (L654-657, "hace falta abrir y volver a cerrar") would fail against the design as written.
- In `dwell`, `fired` stays True while the hand is in frame, because a metric of 0.0 never exceeds `off`. So `dwell` gives one tap per hand appearance. A turn needs at least two taps (select, then destination), so plan B can't play a turn without pulling the hand out of frame.

## Findings

### Z8-1 🔴 Blocker: patching `Confirm` around `Pinch` multiplies the complexity; merge them into one small state machine
Where: L206-226, L555-587, Alternative L (L454-461), OQ4 (L132-137), Alternative E / OQ5.

The queued fixes all land in `Confirm`:
- explicit re-arm (S6 #1, D-M3)
- re-arm for `dwell` (D-M5)
- measure the radius from the lock point (D-B1)
- lock the cell that is shown (D-M6)
- stop reading `closed_since`/`min_s` (S6 #2, Z5-2, D-N8)
- reconcile the two state-machine copies (Z5-3, S6 #7)

Bolted onto a wrapper that drives `Pinch` through `update(None)` side effects, each fix needs a new flag or special case, and each has to be edited in two places.

Simpler shape: drop the "`Pinch` untouched" constraint (it only protects `gesture="pinch"`, which Z5-1 cuts). `Confirm` owns about five fields: `armed`, `lock_cell`, `lock_xy`, `t0`, `reason`. Write it once in the Technical Plan as a transition table and delete step list L559-586:

| State | Condition | Next |
|---|---|---|
| idle, armed | closed and `shown` not None | locked: `lock_cell = shown`, `lock_xy = xy`, `t0 = t` |
| locked | open / no hand / `xy` None / `\|xy - lock_xy\| > r` | idle, not armed; reason is suelta / sin mano / salió |
| locked | `t - t0 >= hold` | fire once, then spent, not armed |
| not armed | released | armed |

"Released" means metric > off, or no hand. For `dwell` it also means the finger moved more than `r` from `lock_xy`, so moving to the destination re-arms it.

This closes:
- **D-B1:** the radius is measured from `lock_xy`. `Confirm` no longer needs `spec` or `cell_center`, and OQ4 shrinks to "r > fingertip jitter".
- **D-M3 / S6 #1:** the `armed` flag is the re-arm rule, and "intento" means one armed cycle.
- **D-M5:** `dwell` gets the movement re-arm above.
- **D-M6:** the lock takes `shown`.
- **S6 #2, Z5-2, D-N8:** `hold = (t - t0) / hold_s`, using its own fields.
- **Z5-3, S6 #7, S-6:** a single copy of the logic.

`Pinch` and its test can stay for the old code path, or be deleted along with `pinch` mode. The units fix (S6 #6) costs one line: `board.py` works in metres (`radii_m`), so convert mm to m once in `gesture_params`.

### Z8-2 🟡 Major: Z5-1 (cut `pinch` mode) still stands and is a precondition for Z8-1; D-M2 pushes the other way
Where: L189-193, L270-296, L545-554, Alternative M (L463-470), OQ3.
- D-M2 asks to keep the 2D metric selectable. As a fourth `gesture` value, that keeps the subtables and the old-key warning.
- Simpler: log the 2D ratio `d2(8,12)/d2(0,9)` as one more field in `dbg` (L265-267). That gives E1 its comparison data at the cost of one dict entry, with no new mode. If E1 shows the 3D ratio is no better, switching is a one-line edit before the 20/11 freeze.
- D-M1 needs no code: add "open hand hovering over a valid destination" to the E1 histograms and the G2 test (L908).
- With `pinch` gone, the config becomes flat keys in `[hands]`. OQ3, Alternative M, the old-key warning (and S6 #8), and the `concepts_brief.md` edit (L847-849) can all be deleted.

### Z8-3 🟡 Major: an explicit `result` field or attempt counter (D-M4) is not justified
Where: L250-253, L760-765, L772.
- The 15 fps remote never plays the ring or the hold sounds (L772: `you === 1` hides them), so the fragility only affects the host, which gets every frame.
- The one host gap is a cancel followed by an immediate re-lock, and Z8-1's `armed` flag prevents it.
- If extra safety is wanted, change the check to `hold < prevHold && prevHold < 1`. Skip the new field.

### Z8-4 🟡 Major: the Risks section (D-B2/S-1) should be a short table pointing at existing mitigations
- Drop "security of the new fields": `hold` is a float and `box` is four pixel coordinates. There is no trust boundary.
- "15 fps remote" is moot under Z8-3.
- "Re-arm" is a spec gap that Z8-1 closes, not a risk.
- "Old `.dj`" is already handled at L515-518 (`?? 0`, `?? null`), which also covers D-N4.
- What remains fits in about five rows:
  - open-hand false positive (G2 test)
  - world-landmark depth accuracy (the 2D/3D log from Z8-2)
  - `dwell` usability (L919)
  - no separation in E1 (`dwell`, then the mouse or the ArUco pointer at L921-923)
  - the box missing the forearm or a tall creature (accepted in OQ1, which also covers D-N5)

### Z8-5 🟢 Nit: one milestones line in the Overview fixes several definition findings
- It covers S6 #5, S6 #14, D-N1, ST-M4 and part of ST-M2.
- It should define E0-E4, "el control" and who runs it (the 5 students), and give a single date against the 18/11 E4 cut-off and the 20/11 freeze.

### Z8-6 🟢 Nit: don't add a third opacity factor for S6 #3 / D-N2
The tracking/death overwrite predates this design and is cosmetic. Fix the claim instead: "`pass` se compone con la opacidad existente".

### Z8-7 🟢 Nit: a frame-time budget (D-N9) is YAGNI
World landmarks come from the same `detect_for_video` call, and the math covers 21 points.

### Z8-8 🟢 Nit: keep the G3/G4 criteria fix (ST-M2) light
"2 of 3 first-time testers" is enough for a student demo.

Z5-5, Z5-6 and Z5-7 still stand unchanged.

## What to apply versus skip
- **Apply:** Z8-1, Z5-1 plus the 2D value logged in `dbg`, the milestones line, and a five-row Risks table.
- **Skip:** the `result` field, a selectable 2D mode, a security risk item, a frame budget, and extra opacity factors.
