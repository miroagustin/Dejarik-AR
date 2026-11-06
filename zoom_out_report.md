# Stage 5: Initial Zoom Out Review

Target: `docs/designs/hand_interaction.md` (full file, lines 1-927)
Reviewer: egm-zoom-out (zoom-out-standard). Goldfish context: none.

Code the reviewer read to check claims: `dejarik/hands.py`, `dejarik/vision.py`, `dejarik/one_euro.py`, `web/main.js`, `web/creatures.js`, `web/events.js`. The cited locations match the code (hands.py:14/92, vision.py:171-183/206-207, main.js:84-89/100-102, creatures.js:102, events.js:51).

**Context sufficiency: PASS.** The goal and motivation are clear, and the design attacks the root problem: touching the paper removes the height error at its source. The translucency for Problem 1 is a deliberate workaround, framed against the concepts_brief.md:328 Non-Goal. Data flow is minimal: it reuses on_tap -> tap -> game.apply, and the gesture logic lives only in Python.

**Verdict: no blockers. 1 Major, 6 Nits.**

## Findings

### Z5-1 🟡 Major: three gesture modes; `pinch` mode is dead weight
Scope: G6 (L93-95), section 2 table (L189-193), section 6 config (L270-296), OQ3 (L130-131), Alternatives L/M (L454-470), impl item 1 `gesture_params` and the old-key warning (L545-554), Change 4 (L500-502).
- The `pinch` mode keeps alive the gesture that the Problem section (L40-44) shows is wrong, and Non-Goals (L114-115) already demote it.
- The safety nets the doc relies on are the mouse (G6) and `dwell` (OQ5). Neither needs `[hands.pinch]`.
- Dropping `pinch` gives flat keys in `[hands]` (`gesture = "touch"|"dwell"`, `touch_on/off`, `extended_on/off`, `hold_ms`). That removes both subtables, OQ3, Alternative M's rationale, and the concepts_brief edits (L847-849).
- The old-key warning guards against stale configs that don't exist: there is one `config.toml`, and item 3 rewrites it.
- It weakens Alternative L: with no `pinch` mode, `Pinch` only runs inside `Confirm`.

Recommendation: cut `pinch` mode, the subtables and the old-key warning. Git history keeps the old gesture.

### Z5-2 🟢 Nit: `Confirm` is not really wrapping `Pinch` "without changing it"
Scope: L213-226, L555-587, Alternative L (L454-461).
- `Confirm` resets `Pinch` by calling `pinch.update(None, t)` as a side effect.
- It reads `Pinch` internals (`closed_since`, `min_s`).
- It needs a special case for `hold_ms = 0`.

A two-line `cancel()` and `progress(t)` on `Pinch` would be cleaner. Or merge `Pinch` into `Confirm` if Z5-1 is accepted.

### Z5-3 🟢 Nit: the state machine is written out twice, and the two copies disagree
Scope: L213-226 vs L559-586.
- L218 sets `reason = "sin mano"` unconditionally; L561-562 sets it only if `was`.
- L224 says `hold` stays at 1 until release; L584-586 derives it from `fired`.

Keep a state/transition table in the Technical Plan and leave step ordering to the code and the tests.

### Z5-4 🟢 Nit: the highlight debounce lives inside `Confirm`
Scope: section 4 (L234-242), `shown`/`cand`/`cand_n` and step 7 (L557-558, L577-581).
- The debounce is a display concern, but it makes `Confirm`'s state and tests bigger.
- `dejarik/one_euro.py` (`OneEuro`) already exists. Filtering `lm2d[8]` with it would also reduce neighbor-cell flicker, at the cost of a little lag.
- Check whether the 3-frame debounce is needed at all, given the fingertip rests on the paper and the cell is locked by `lock_cell` during the gesture. Let the E0/E1 measurement decide.

### Z5-5 🟢 Nit: the shader frequency changes over time and causes chaotic flicker
Scope: item 19 (L864-867).
`sin(uTime * (37.0 + 40.0 * uPass))` with a fading `uPass` moves the phase by thousands of radians once `uTime` is large. Raise only the amplitude (`uFlicker + 0.35 * uPass`).

### Z5-6 🟢 Nit (altitude): the doc fixes cosmetic constants that will be tuned by eye
Scope: items 8, 10, 13 (L718-723, L738-744, L792-795); ring offset (L319 vs L770).
Tone frequencies, gains, ring size, the debug string, and the ring offset are tuning values. They already disagree: the ring offset is "~60 px" at L319 and "(+40, -40) px" at L770. State the constraints instead.

### Z5-7 🟢 Nit: the "same smoothing as `poseAlpha`" claim is wrong
Scope: L313-315, L780-781, G4 (L84-85).
`poseAlpha` uses τ = 0.1 s (main.js:101), but the design uses τ = 0.05 s. Drop the "same as" or share a helper, and keep a single number for the ~150 ms fade.

## Reuse summary
The design reuses `image_to_board`, `cell_at`, `Pinch`, `project`, the `tone()`/`sounds` pattern, `--blue`, `makeHologramMaterial`, and the `__main__.py` warning style. The `NO_HAND` dedup (vision.py:183 duplicates hands.py:14) and the `encode_remote` px scaling fix (vision.py:171-180) are real cleanups. It misses only `OneEuro` (Z5-4). No speculative infrastructure beyond Z5-1. E4 is correctly kept out of scope.
