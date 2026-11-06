# Stage 6: Comprehension Test

Target: `docs/designs/hand_interaction.md`. FeatureRange: lines 1-507. DetailedRange: lines 508-927.
Reviewer: egm-comprehension. It read only the document and its persona file. No standard applied.

**What this proposes**

The design replaces the current hand input, a thumb-index pinch with the fingertip held in the air, with a new gesture. The player rests the index fingertip (landmark 8) on the paper to pick a cell, and the existing homography projects it onto the board. Because the finger touches the paper, the height error goes away. To confirm, the player brings the middle finger against the index and holds still for 1 s. A new Python class, `Confirm`, wraps the existing `Pinch` class without changing it. `Confirm` locks the cell when the gesture starts, cancels if the fingertip drifts more than 20 mm from the cell centre or the hand is lost, and fires `on_tap(lock_cell)` once.

The protocol header's `hand` field gains `hold` (progress from 0 to 1) and `box` (the hand's bounding box). The browser uses them to draw a CSS loading ring offset from the cell, to play start and cancel sounds, and, in stage E3, to make creatures whose projected root falls inside `hand.box` translucent (~0.35) with stronger flicker, so the hand looks like it passes through them. Thresholds move to `[hands]` plus the subtables `[hands.touch]` and `[hands.pinch]` in `config.toml`. Old keys produce a warning. `gesture = "pinch"` keeps the old gesture and `gesture = "dwell"` (hold still only) is plan B. The mouse stays as the fallback, and real depth occlusion (E4) is out of scope.

**How the existing system works, per this document**

A vision thread reads camera frames and pose into a frame bus. A separate hands thread runs MediaPipe (`HandTracker`), computes a 2D pinch ratio, uses `Pinch` (hysteresis, minimum time, single fire) and calls `on_tap → tap → game.apply`, which is the same path as a mouse click. It publishes `hand = {cell, pinch, px}`, and the vision loop encodes it into a `[uint32][header][JPEG]` frame for the host browser and a scaled-down remote viewer. The remote has a known bug: `px` is not scaled. The browser renders hologram creatures always on top of the video. Their opacity is written by both the tracking-lost fade and the death animation. Sessions can be recorded as `.dj` files and replayed.

## Findings

1. 🔴 **Blocker. Re-arming after a cancel is undefined, and plan B contradicts the cancellation test** (L208-209, 560-576, 654-657, 193, 552-553).
   - The steps rely on `pinch.update(None, t)` to cancel, but the document never says what that does to `Pinch`'s state. In particular, it does not say whether `Pinch` needs the metric to go above `off` before it can activate again.
   - L656 ("Hace falta abrir y volver a cerrar") says it does need that. Otherwise the next frame's step 4 would reactivate with the metric still closed, and step 5 would lock a new cell.
   - If that is true, `dwell` can never open, because its metric is always 0.0 and on/off are 0.5/0.5. After its first confirmation or cancel it could never fire again while the hand stays in frame. If it is false, the cancellation test is wrong, and "afuera" (step 5) re-triggers every frame.
   - The reviewer could not paraphrase how a second confirmation happens under `dwell`. The document needs to state `Pinch`'s re-arm rule and how `dwell` ends a cycle.
2. 🟡 **Major. `hold` depends on `Pinch` internals that are never described** (L225, 584-586).
   - `closed_since` and `min_s` are used but never defined. Are they `Pinch` attributes? Is `min_s` equal to `hold_ms/1000`?
   - The `Pinch` interface itself (`active`, the return value of `update`) is only implied.
   - This matters because the design claims `Pinch` is untouched while `Confirm` reads its state.
3. 🟡 **Major. The fix for overlapping opacity writers is overstated** (L300-303, 885-887).
   - `baseOpacity` is still written by both the tracking fade (`main.js:102`) and death (`events.js:51`). Only `pass` is composed separately.
   - L886 says the two "se compone[n] … en vez de pisarse", but tracking and death still overwrite each other.
   - Either scope the claim to `pass`, or say how tracking and death combine.
4. 🟡 **Major. OQ3 is listed as open but treated as decided elsewhere** (L130-131 vs 463-470, 500-502).
   - OQ3 says "Falta confirmar". Alternative M says the author approved the subtables, and "Cambios respecto del brief" item 4 lists them as decided.
   - OQ2, OQ4 and OQ5 are also marked "propuesto", yet the plan uses them as settled. A reader cannot tell which values are still open.
5. 🟡 **Major. "El control" and "los 5 estudiantes" are never defined** (L59-60, 80, 902, 909-910).
   - Every acceptance criterion is measured "en el control (antes del 16-18/11)", but the document never says what the control is or who runs it.
   - "La línea de debug de los 5 estudiantes" brings in an undefined group.
   - The range "16-18/11" gives no single deadline relative to the E4 cut-off of 18/11.
6. 🟡 **Major. Coordinate units are unstated for `xy` and the cancel radius** (L164, 276, 556, 564-565).
   - The config holds `cancel_radius_mm` and `Confirm` takes `cancel_radius_m`, but the conversion is never stated.
   - Neither is the unit that `image_to_board` / `cell_center` return.
   - A reader cannot check `dist(xy, …) > cancel_radius_m`.
7. 🟢 **Nit. The Technical Plan state sketch and the detailed steps disagree** (L218, 223 vs 561-576).
   - The sketch sets "sin mano" unconditionally. Step 2 sets it only if `was`.
   - The sketch sets "suelta" only for a release without firing. Step 6 also sets it after a successful confirmation.
8. 🟢 **Nit. Where the old-key warning goes is inconsistent** (L292-294 vs 548-551). One says `hands_loop` writes a warning to the log. The other says `gesture_params` uses `print`.
9. 🟢 **Nit. The `hands_loop` pseudo-code nesting is unclear** (L591-599). The indentation suggests `conf.update` (L598) also runs in the no-`lm` branch, which would call `update` twice. State that L598 is only in the `lm` branch.
10. 🟢 **Nit. The ring offset is given in two inconsistent ways** (L318-319 vs 769-770). "~60 px del cuadro" vs `(+40, −40)` px in `#stage` pixels. These are different spaces.
11. 🟢 **Nit. `hand.px` is never defined** (L168, 176, 247, 328). The document does not say which landmark it is, or whether it changes under `touch`.
12. 🟢 **Nit. Translucency is said not to dim, but it does** (L306-308, 869). "Sin bajar el brillo" sits next to an opacity drop to 0.35. Clarify that the distinction from "Tracking perdido" is the flicker plus the HUD notice.
13. 🟢 **Nit. Several project-specific terms are used without definition:**
    - `.dj` files and "replay" (L105, 116, 263)
    - the remote viewer and `you === 1` (L772)
    - `poseAlpha` (L314, 775)
    - "puntero ArUco" (L922)
    - "cuadro de render" vs camera frame
    - the MediaPipe landmark numbering (L15, 69)
14. 🟢 **Nit. E1 is used before it is defined** (L129, 138, 282). The stages are defined only at L511.
15. 🟢 **Nit. "Un radio" in G2 is ambiguous** (L71). It only resolves to 20 mm in OQ4.
