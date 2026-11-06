Status: resolved (auto accept, 2026-11-06). R2-1 through R2-10 were applied to `docs/designs/hand_interaction.md`; R2-11 was declined. The re-audit limit for this stage is reached, so the review is closed.

# Goldfish Annotated Review Report — Stage 9 re-audit (round 2)

**Target:** `docs/designs/hand_interaction.md` (lines 218-264 and 552-996)
**Reviewers:** egm-implementation-readiness (completed), egm-codebase-details (completed), egm-style (completed).

| Reviewer | 🔴 | 🟡 | 🟢 |
|---|---|---|---|
| implementation-readiness | 1 | 4 | 3 |
| codebase-details | 2 | 2 | 4 |
| style | 0 | 2 | 18 |

**Verdict: not ready, but the problems are narrow.** Every finding is in the new `Confirm` table, its tests, or `hand_msg`. The browser, docs and E3 items passed, and every file and line reference matches the code.

This is the one re-audit the process allows. After these fixes the stage is closed, and anything left over is recorded as an accepted trade-off.

Evidence checked for this pass:
- `hands.py:99` rounds `px` to floats today.
- `protocol.py:14` calls `json.dumps(header)`.
- `encode_remote(frame_id, t_ms, bgr, pose_msg, k4, hand, net_cfg)` is defined at `vision.py:171`.
- The `hands_loop` docstring at `hands.py:76-77` mentions `pinch_ratio`.

---

## Prioritized Findings & AI Suggestions

### [R2-1] [`implementation-readiness` B1, `codebase-details` B1] - Severity: High
*   **Affected Scope:** [Lines 238-244](docs/designs/hand_interaction.md#L238-L244) (table), [L605-612](docs/designs/hand_interaction.md#L605-L612), [L707-709](docs/designs/hand_interaction.md#L707-L709)
*   **Discrepancy Description:** In `dwell`, the gesture re-locks on the previous cell.
    *   Trace: it fires on 5, and the finger moves to 6. On the frame after "salió", the machine is free and armed, so it locks again at once with `lock_cell = shown`.
    *   `shown` is still 5. The debounce needs 3 free frames to move it, the candidate resets on lock, and while locked `shown` is pinned to `lock_cell`.
    *   Result: it fires 5 again, so `test_confirm_dwell_two_taps` fails and plan B can't play a turn.
    *   In `touch` the same lag locks the previous cell if you close within about 66 ms of crossing a border.
*   **Rationale:** Two reviewers traced this independently, and I confirmed it against the table.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The lock must wait until the highlight has caught up with the finger. One extra row does this, and it fixes both modes. The "afuera" row is also changed to test the raw `cell`, so that a debounce that hasn't settled yet waits instead of cancelling.
*   ***Proposed Edit:***
    *   Location: table rows 3-4 (L240-241).
    *   Change:
        ```markdown
        | libre, armado | cerrado y (`cell None` o `xy None`) | libre; `reason = "afuera"`; queda armado solo si `rearm_on_move` |
        | libre, armado | cerrado y `cell != shown` | libre y armado, sin cambiar `reason`: espera a que el resaltado alcance al dedo |
        | libre, armado | cerrado | fijado: `lock_cell = shown`, ... |
        ```
    *   Location: the bullet "La casilla fijada es la resaltada" (L246-247). Append: "Solo se fija cuando el dedo está en la casilla resaltada (`cell == shown`), así no se fija la casilla anterior mientras el debounce alcanza al dedo. En `dwell`, después de salir del radio se espera `cell_frames` cuadros y se fija la casilla nueva."

### [R2-2] [`codebase-details` B2, `implementation-readiness` M5] - Severity: High
*   **Affected Scope:** [L582-583](docs/designs/hand_interaction.md#L582-L583) (`middle_extended`), [L621-625](docs/designs/hand_interaction.md#L621-L625) (`hand_msg`), [L724-725](docs/designs/hand_interaction.md#L724-L725) (`test_hand_msg`)
*   **Discrepancy Description:** `hand_msg` publishes values that `json.dumps` can't encode.
    *   `"px": lm2d[8]` is a numpy array, and `middle_extended` returns `np.bool_`.
    *   `encode_frame` calls `json.dumps` (`protocol.py:14`). It raises `TypeError` on the first frame with a hand, which kills the vision thread and freezes the app.
*   **Rationale:** Today's code converts these values explicitly (`hands.py:99`).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, and it would crash the whole app.
*   ***Proposed Edit:***
    *   `middle_extended`: returns `bool(|w12-w0| / max(1e-6, |w10-w0|) > thresh)`.
    *   `hand_msg`: `"px": [round(float(u), 1), round(float(v), 1)]` (as `hands.py:99` does today). The `box` values are also plain `float`s rounded to 0.1. `metric2d` is converted with `round(float(...), 3)`.
    *   `test_hand_msg`: also assert that `json.dumps(hand_msg(...))` doesn't raise, with numpy arrays as input.

### [R2-3] [`implementation-readiness` M3, `codebase-details` M1] - Severity: Medium
*   **Affected Scope:** [Lines 685-714](docs/designs/hand_interaction.md#L685-L714) (tests)
*   **Discrepancy Description:** With `shown=None` at start and `cell_frames=3`, a test that starts closed doesn't behave as described. The table as written cancels with "afuera" and disarms. With R2-1, it waits 3 frames. Either way the sequences as written fail. The tests also don't say from which instant "1000 ms" is measured.
*   **Rationale:** An implementer would have to invent the sequences.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Building the `Confirm` tests with `cell_frames=1` makes `shown = cell` on the same frame. That is the simplest preamble, and the debounce keeps its own test.
*   ***Proposed Edit:*** In item 4, change the constructor sentence to: "Todos los tests de `Confirm` lo construyen con `Confirm(0.35, 0.45, 1000, 0.02, 1, False)` (`cell_frames=1`, así `shown` alcanza al dedo en el mismo cuadro), salvo `test_confirm_debounce`, que usa `cell_frames=3`. Los tiempos se miden desde el primer cuadro cerrado, que es el que fija. `xy = cell_center(c, spec)` con el `spec` escalado de `board_spec.json`."

### [R2-4] [`implementation-readiness` M2, `codebase-details` M2] - Severity: Medium
*   **Affected Scope:** [L244](docs/designs/hand_interaction.md#L244), [L257-258](docs/designs/hand_interaction.md#L257-L258), [L710-711](docs/designs/hand_interaction.md#L710-L711)
*   **Discrepancy Description:** `hold_ms = 0` conflicts with "one row per frame".
    *   Locking and firing are separate rows, so with `hold_ms = 0` the fire happens on the frame after the lock, but the test expects it on the lock frame.
    *   The division in the `hold` formula is not guarded.
*   **Rationale:** The spec and the test contradict each other.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Keep the one-row rule, since it is simpler, and change the test.
*   ***Proposed Edit:***
    *   `test_confirm_hold_ms_zero`: "con `hold_ms=0`, fija en un cuadro y dispara en el siguiente; `hold` vale 1 desde que fija, sin dividir por cero".
    *   L257-258: "`hold` vale 0 si está libre, 1 si ya disparó o si `hold_ms == 0` (sin dividir), y `min(1, (t - t0) / (hold_ms / 1000))` si no."

### [R2-5] [`implementation-readiness` M4, `style` N15] - Severity: Medium
*   **Affected Scope:** [Lines 685-725](docs/designs/hand_interaction.md#L685-L725), [L966-968](docs/designs/hand_interaction.md#L966-L968)
*   **Discrepancy Description:** The coverage rule is still not met. Untested:
    *   row 6 with `xy None` (pose lost mid-gesture)
    *   row 1's "and armed" effect
    *   row 3 with `xy None`
    *   row 3 staying armed in `dwell`
    *   the new "waits" row from R2-1
*   **Rationale:** If `xy None` is checked in the wrong order, `math.dist(None, …)` raises.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Extending existing tests covers it with few lines.
*   ***Proposed Edit:***
    *   `test_confirm_cancels_on_lost_hand`: append "Si la mano vuelve ya cerrada, fija sin tener que abrir."
    *   `test_confirm_ignores_start_off_board`: append "Lo mismo con `cell=5` y `xy None` (pose no ok)."
    *   New `test_confirm_pose_lost`: fixed, then `xy None` gives `reason == "salió"` with no error.
    *   `test_confirm_dwell_two_taps`: build it with `cell_frames=3`. The second fire returns `6`, not `5`, after 3 frames on 6. Also: starting off the board (`cell None`) leaves it armed.
    *   `test_confirm_debounce`: append "Cerrado sobre una casilla que todavía no es `shown` no fija hasta que `shown` la alcanza."

### [R2-6] [`style` M1] - Severity: Medium
*   **Affected Scope:** [Lines 605-612](docs/designs/hand_interaction.md#L605-L612)
*   **Discrepancy Description:** The `shown` debounce is written as nested conditional prose ("si no, si … si no"). It also duplicates section 4.
*   **Rationale:** It is easy to mis-nest when implementing.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. A list is clearer, and item 1 becomes the single spec, with section 4 describing the effect.
*   ***Proposed Edit:*** Replace the `shown` sentence with a sub-list:
    *   "si está fijado, `shown = lock_cell`;"
    *   "si no y `cell == shown`, se resetea el candidato;"
    *   "si no, `cell` es el candidato: se cuentan los cuadros seguidos, y al llegar a `cell_frames`, `shown = cell` (`None` también es candidato). El candidato se resetea al fijar."
    *   Then add: "Esta es la regla; la sección 4 describe el efecto."

### [R2-7] [`style` M2] - Severity: Medium
*   **Affected Scope:** [Lines 975-979](docs/designs/hand_interaction.md#L975-L979) (Verification step 3)
*   **Discrepancy Description:** The "histogramas de E1" have no data source, no tool and no pass rule.
*   **Rationale:** As written, the step can't be checked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. A hand-filled table read off the debug line is enough. No new tool is needed.
*   ***Proposed Edit:*** Replace that sentence with: "Para calibrar, cada integrante pone 3 poses (apuntar, dos dedos juntos y mano abierta) desde cada lado. De la línea de debug se anotan en una tabla `metric` y `metric2d` (mínimo y máximo de unos segundos). `on`/`off` van entre "dos dedos juntos" y las otras dos. Si los rangos se superponen, se prueba `metric2d` y, si tampoco separa, se pasa a `dwell`."

### [R2-8] [`implementation-readiness` N6, N7] - Severity: Low
*   **Affected Scope:** table rows 1-2 (L238-239)
*   **Discrepancy Description:** Row 1 sets "sin mano" even after a fire. Row 2's "o `rearm_on_move`" can never be reached.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** These are cheap fixes, and they keep the table consistent with rows 5 and 6.
*   ***Proposed Edit:*** Row 1: "si estaba fijado y no había disparado, `reason = "sin mano"`". Row 2: condition "`metric > off`".

### [R2-9] [`codebase-details` N1-N4, `implementation-readiness` N8] - Severity: Low
*   **Affected Scope:** item 1, item 5, item 12
*   **Discrepancy Description:** Small implementation gaps:
    *   An unknown `gesture` is only caught on the first hand frame, inside a daemon thread.
    *   `cell_center` is missing `spec`.
    *   The docstrings of `hands_loop` (`hands.py:76-77`) and `transport.py:252` will go stale.
    *   `tmp` is never declared.
    *   `encode_remote` is missing the `pose_msg`/`k4` arguments in the test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One line each.
*   ***Proposed Edit:***
    *   `gesture_params`: "levanta `ValueError` si `gesture` no es `"touch"` ni `"dwell"`, al arrancar el hilo".
    *   `hands_loop`: "su docstring cambia "pinch_ratio" por "dbg" y "pinch" por "gesto"". Item 1 also gains: "`transport.py:252` queda como está (solo dice "pinch" en un docstring)".
    *   Item 12: "`const tmp = new THREE.Vector3()` arriba del loop".
    *   Item 5: "`pose_msg = {"ok": False}`, `k4 = [1000, 1000, 640, 360]`".

### [R2-10] [`style` N1, N2, N7, N8, N9, N13, N14] - Severity: Low
*   **Affected Scope:** L230, L249, L824-838, L889-893
*   **Discrepancy Description:** Small wording and syntax errors:
    *   L249: "solo" is ambiguous.
    *   L230: "cerrado"/"Abierto" are capitalised differently.
    *   "un par de cuadros" is vague.
    *   `left = x + 40 − 22` uses U+2212 instead of an ASCII minus, so it won't parse if copied.
    *   "los sonidos no se muestran".
    *   Nested double quotes.
    *   Backslash escapes inside a code span render as literal backslashes.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The minus sign and the backslashes would be copied into code and docs, and the rest is one word each.
*   ***Proposed Edit:***
    *   "cancelaría por sí solo".
    *   "Cerrado"/"Abierto".
    *   "fijaciones de menos de 150 ms (con `hold_ms = 1000`)".
    *   ASCII `-` in `left`/`top`.
    *   "el anillo no se muestra y los sonidos de hold no suenan".
    *   «Apuntá…» for the inner quote.
    *   The demo_script row written with a double-backtick span.

### [R2-11] [`style` N3-N6, N10-N12, N16-N18] - Severity: Low
*   **Discrepancy Description:** Phrasing and terminology:
    *   "sostén/hold", "disparar/confirmar" and "fijado/lock" vary.
    *   Long bullets.
    *   The README copy.
    *   "control" and its date (defined in the Overview since round 1).
    *   Line length.
    *   English template headings.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** These are Nits. The code names are the identifiers, "control" is defined in the Overview, and the headings come from the EGM template.
*   ***Proposed Edit:*** none.
