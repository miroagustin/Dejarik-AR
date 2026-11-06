# Stage 9: Implementation Readiness Test

Target: `docs/designs/hand_interaction.md`, DetailedRange (lines 508-927). Standard: implementation-readiness-standard (readiness, codebase). Goldfish context: none.
Reviewers: egm-implementation-readiness (completed), egm-codebase-details (completed), egm-style (completed). One round, uninterrupted mode.

**Verdict: NOT READY.** The browser, CSS and docs items are close to ready. The blockers are in `Confirm.update`, its config and its tests.

| Reviewer | 🔴 | 🟡 | 🟢 |
|---|---|---|---|
| implementation-readiness | 2 | 5 | 10 |
| codebase-details | 1 | 5 | 9 |
| style | 0 | 7 | 11 |

Verified accurate: every cited line reference (hands.py:14/92, vision.py:171-183/207, __main__.py:42/110, config.toml:36-40, test files, protocol.md:60, main.js:102, events.js:51, style.css:2/29, debug.js:65, README:73/80, rules.md:47, demo_script:42, dejarik_ar.md:380/843, concepts_brief:160-164/328). The phases each leave the code runnable, `hands.py` has no top-level MediaPipe import, and `uPass` follows the `uFlash` pattern.

## 🔴 Blockers

- **IR-B1 / CD-B1. A "salió" cancel restarts the gesture in the same frame, then crashes** (L564-583, test L654-657).
  - Step 3 calls `pinch.update(None)`. Step 4 then calls `pinch.update(metric)` with the metric still closed, so Pinch is active again (hands.py:33-34).
  - `was` is True, so step 5 is skipped, and step 6 is skipped because Pinch is active. The frame ends with `lock_cell = None`.
  - On the next frame, `cell_center(None)` raises `TypeError` (board.py:70-77), which kills the daemon hands thread with no message.
  - The test's "hace falta abrir y volver a cerrar" isn't implemented by any step. The "afuera" path re-enters every frame.
  - Fix: add an explicit `need_open` latch.
- **IR-B2. `dwell` can't do select-then-move** (L543, 552-553, 919-920).
  - The metric is always 0.0, so after the first confirm `fired` stays True for as long as the hand is visible.
  - The only way out is to pull the hand out of frame.
  - Fix: define dwell's re-arm and add `test_confirm_dwell_two_taps`.

## 🟡 Major

- **IR-M1 / CD-N1. `ext_on`/`ext_off` and `dbg.extended` are undefined for `pinch` and `dwell`** (L545-554, 594-605).
  - Missing keys give a `KeyError`.
  - `p.ext_off` uses attribute access on a dict.
  - `cfg` is actually `cfg["hands"]` (`__main__.py:110`).
  - The `cancel_radius_mm/1000` conversion and the `extended_*` → `ext_*` mapping are not stated.
- **IR-M2 / CD-M2. `scale_hand` raises `KeyError` on old recordings without `box`** (L515-518, 622-625). `recording.py:55-56` sends the recorded header through `encode_remote`. Use `.get`, and add a test with a legacy hand dict.
- **IR-M3. The coverage rule at L899-901 is not met.** No tests for:
  - "suelta"
  - `hold_ms = 0` with `cell None`
  - the `pinch` metric
  - the `extended` hysteresis
  - the `box` math

  `test_confirm_uses_locked_cell` should pass `cell=6` synthetically: 10 mm from the centre of cell 5 doesn't reach cell 6 (about 13.9 mm to the edge).
- **IR-M4 / ST-M3. A non-finite metric can reach JSON** (L603-606).
  - `round(metric,3) or None` turns dwell's 0.0 into `None`, and `inf` serializes as `Infinity`, which `JSON.parse` rejects.
  - The no-hand `dbg={...}` contents are unspecified.
- **IR-M5 / CD-M4. `#hint` "centrado abajo" overlaps `#combat`** (style.css:33). Give exact CSS.
- **CD-M1 / ST-M4. The `hands_loop` nesting is ambiguous** (L591-606). `conf.update` appears to run twice on no-hand frames. Add a `continue` as `hands.py:88-91` does today.
- **CD-M3. `docs/protocol.md:3` says the file was frozen on day 2 and any change bumps `v`.** Item 7 adds fields but keeps `v: 1`. Say which rule wins, or amend line 3.
- **CD-M5. `demo_script.md` has no row for the host's first use of the hand** (L826-827). Name the row and the narrator's text.
- **ST-M1. Three versions of the gesture phrase** (L531, 751, 806, 818, 827). Make the `HINT` constant the single source.
- **ST-M2. "anillo" is used for both the hold ring and the board rings** (L904, 906).
- **ST-M5. "sin bajar el brillo" vs the `(1 - 0.65·pass)` opacity** (L868-881).
- **ST-M6. The E3 block's guard (`h?.box && pose.ok`) means `pass` never decays** (L775-781). The block must always run.
- **ST-M7. The G4 pass criterion can't be checked** (L913-915).

## 🟢 Nits

**Implementation readiness**
- IR-N1. The ring anchor (centre or corner) is unspecified, and so are how `--p` is set and the exact mask.
- IR-N2 / CD-N7. Use `getWorldPosition` plus the `project` NDC mapping (factor it out). `cellCenter` is not imported in main.js.
- IR-N3. `prevHint` is needed and not named.
- IR-N4. `holdStart` fires one frame late. State that this is intended.
- IR-N5. Step 7 doesn't say when the debounce candidate resets.
- IR-N6. `dist` clashes with the distortion parameter; use `math.dist`. `cell_center` is missing `spec`.
- IR-N7. The import-check command asserts nothing.
- IR-N8. The debug-line number format and `strokeStyle` are unspecified.
- IR-N9 / CD-M5. The new demo_script row needs all 4 columns.
- IR-N10 / CD-N9. Stale docs not in the file list: `dejarik_ar.md:415, 911` and `concepts_brief.md:98, 296`.

**Codebase details**
- CD-N2. `math.inf` needs `import math`.
- CD-N3. `hold` divides by `min_s`, so `hold_ms = 0` raises `ZeroDivisionError`.
- CD-N5. The test's `net_cfg` needs `remote_quality`.
- CD-N6 / ST-N6. The TOML ordering rationale is wrong. The only real constraint is that no `[hands]` keys follow `[hands.touch]`.
- CD-N8. Tracking and death still overwrite `baseOpacity`. Reword the claim.

**Style**
- ST-N1. `min_s` and `closed_since` are not introduced.
- ST-N2. Dict access is written as attribute access.
- ST-N3. `extended_on/off` vs `ext_on/off`.
- ST-N4. The `hold_ms = 0` note is redundant with step 8.
- ST-N5. "Un solo lugar (… tres lugares)".
- ST-N7. The tests depend on unstated config values, and "w12 cerca de w9" is vague.
- ST-N8. Some "Por qué" lines add nothing (L695, 712, 732).
- ST-N9. Hedged wording at L693, 722, 784 and 917.
- ST-N10. `hay pose` vs `lastHeader.pose.ok`. The "Solo en el remoto" heading is misleading.
- ST-N11. "control", "16-18/11" and "5 estudiantes" are undefined. `hold_ms` appears in player-facing README text.

**Reuse suggested:** `math.dist`, `Object3D.getWorldPosition`, and the `project` NDC→pixel mapping in main.js.
