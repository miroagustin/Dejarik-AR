Status: resolved (auto accept, 2026-11-06). All 24 PROPOSE FIX items were applied to `docs/designs/hand_interaction.md`, including Issue 3. Issue 18 (contested) and Issues 26-30 (declined) were left unchanged.

# Goldfish Annotated Review Report

**Target:** `docs/designs/hand_interaction.md` (full file, lines 1-927)
**Findings source:** [consolidated_review_report.md](consolidated_review_report.md), action items A1-A25 plus the five items it recommends skipping. Finding IDs follow that report's traceability matrix.

Evidence checked for this pass:
- `dejarik/hands.py:17-38`: `Pinch`. `update(None)` resets it, and a closed metric on the next call re-activates it with no need to open.
- `dejarik/hands.py:79`: `Pinch`'s only use outside its test.
- `dejarik/board.py:57-77`: `cell_at`/`cell_center` work in metres, and cell 0 is the centre disc of radius `r0`.
- `web/main.js:3, 84-89, 97-102`: main.js imports only `createScene`; `project` uses `board.matrix` then `projectionMatrix`; `poseAlpha` uses τ = 0.1.
- `web/hologram.js:36`: the flicker formula.
- `web/style.css:33`: `#combat` sits at `bottom: 18px`, centred.
- `docs/protocol.md:3`: the freeze rule.
- `docs/demo_script.md:16-24, 38-43`: the script table and the fallback table.
- `concepts_brief.md:263-264`, `docs/designs/dejarik_ar.md:1329`, `hand_interaction_brief.md:117, 138`: "el control" is control 2 of the general plan (days 14-16), and "los 5 estudiantes" are the team.

Totals: 24 PROPOSE FIX (one needs your decision: Issue 3), 1 CONTEST, 0 ESCALATE, 5 DECLINE. Issues 2, 4, 12 and 20 are fixes that also contest part of their finding.

---

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design`, `comprehension`, `codebase-details`, `implementation-readiness`, `zoom-out`] - Severity: High
*   **Affected Scope:** [Lines 206-232](docs/designs/hand_interaction.md#L206-L232) (§3 `Confirm`) and [Lines 555-587](docs/designs/hand_interaction.md#L555-L587) (item 1, `class Confirm`)
*   **Discrepancy Description:** The `Confirm` state machine has four problems.
    *   After a "salió" cancel, step 4 re-activates `Pinch` in the same frame, leaving `lock_cell = None`. On the next frame `cell_center(None)` raises `TypeError` and kills the hands thread.
    *   Nothing makes the player open the fingers before trying again.
    *   The cancel radius is measured from the cell centre, so a lock near a cell's edge cancels at once and loops.
    *   `dwell` fires once and then stays fired, so it can't do select-then-move.

    Other defects in the same text:
    *   The lock takes the raw cell, not the highlighted one.
    *   `hold` reads `Pinch` internals (`closed_since`, `min_s`).
    *   The logic is written twice, and the copies disagree.
    *   `hold_ms = 0` divides by zero.
    *   The mm→m conversion is never stated.
*   **Rationale:** Verified against `hands.py:30-38` and `board.py:70-77`. The test at L654-657 ("hace falta abrir y volver a cerrar") can't pass against the steps as written.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This is a real defect, and every fix lands in `Confirm`. Patching the wrapper needs a new flag at every step. If `Confirm` owns its own small state, one table covers all the cases. `Pinch` has no other user (`hands.py:79`), so it can be deleted along with its test. This works whether or not A3 is accepted: the `pinch` metric would just feed the same `Confirm`.
*   ***Proposed Edit:***
    *   Location: §3, replace L206-232 entirely.
    *   Change:
        ````markdown
        ### 3. `Confirm`: la máquina de estados

        Es una clase nueva en `hands.py` que reemplaza a `Pinch`. Tiene su propia
        histéresis, el tiempo de sostén, la casilla fijada y la cancelación por
        distancia. No sabe nada de MediaPipe, así que se testea con secuencias
        sintéticas. `Pinch` y su test (`tests/test_hands.py:9-19`) se borran:
        `hands_loop` era su único uso.

        ```text
        Confirm(on, off, hold_ms, cancel_radius_m, cell_frames, rearm_on_move)
          update(metric, cell, xy, t) -> casilla confirmada | None
          estado: armed, lock_cell, lock_xy, t0, fired, reason, shown
          "cerrado" para empezar: metric < on. "Abierto" estando fijado: metric > off.
        ```

        En cada cuadro, primero se actualiza `shown` (sección 4) y después se
        aplica la primera fila que corresponda:

        | Estado | Condición | Pasa a |
        |---|---|---|
        | cualquiera | `metric None` (sin mano) | libre y armado; si estaba fijado, `reason = "sin mano"` |
        | libre, sin armar | `metric > off`, o `rearm_on_move` | armado |
        | libre, armado | cerrado y (`shown None` o `xy None`) | libre; `reason = "afuera"`; queda armado solo si `rearm_on_move` |
        | libre, armado | cerrado | fijado: `lock_cell = shown`, `lock_xy = xy`, `t0 = t`, `reason = ""` |
        | fijado | abierto | libre y armado; `reason = "suelta"` si no había disparado |
        | fijado | `xy None` o `math.dist(xy, lock_xy) > cancel_radius_m` | libre; `reason = "salió"` si no había disparado; queda armado solo si `rearm_on_move` |
        | fijado, sin disparar | `t - t0 >= hold_ms / 1000` | disparado: `update` devuelve `lock_cell`, una sola vez |

        *   **La casilla fijada es la resaltada.** `lock_cell` sale de `shown`, la
            casilla que el jugador está viendo, no de la casilla cruda del cuadro.
        *   **El radio se mide desde `lock_xy`**, el punto donde se apoyó el dedo,
            no desde el centro de la casilla. La casilla 0 tiene ~35 mm de radio, así
            que medir desde el centro cancelaría solo un toque cerca del borde. `xy`
            está en metros (`board.py`), y `cancel_radius_m = cancel_radius_mm / 1000`.
        *   **Un intento** es un ciclo armado → fijado → libre. Después de cancelar o
            de disparar hay que abrir los dedos (o sacar la mano) para volver a armar.
        *   **En `dwell`** la métrica nunca abre, así que `rearm_on_move = True`:
            salir del radio ya arma de nuevo. Se elige la pieza, se mueve el dedo al
            destino y se sostiene otra vez, sin sacar la mano.
        *   `hold` vale 0 si está libre, 1 si ya disparó y `min(1, (t - t0) /
            (hold_ms / 1000))` si no. Con `hold_ms = 0` vale 1.

        `hands_loop` llama a `on_tap(...)` con lo que devuelve `Confirm`, nunca con
        la casilla del cuadro actual. Si la pose no está ok, `cell` y `xy` son
        `None`, así que no se puede empezar ("afuera") y un gesto en curso se cancela
        ("salió"). El efecto es el mismo que hoy, donde `on_tap` solo se llama con la
        pose ok.
        ````
    *   Location: item 1, replace L555-587 (the `class Confirm` bullet and its eight steps).
    *   Change:
        ```markdown
        *   `class Confirm`: implementa la tabla de la sección 3, sin una lista de
            pasos aparte.
            *   `__init__(on, off, hold_ms, cancel_radius_m, cell_frames,
                rearm_on_move)`. Estado inicial: `armed=True`, `lock_cell=None`,
                `lock_xy=None`, `t0=None`, `fired=False`, `reason=""`,
                `shown=None`, `cand=None`, `cand_n=0`, `t_last=0`.
            *   `update(metric, cell, xy, t) -> int | None`: guarda `t_last = t`,
                actualiza `shown` y aplica la primera fila de la tabla que
                corresponda. `shown`: si está fijado, vale `lock_cell`. Si no, si
                `cell == shown`, se resetea el candidato; si no, se cuenta cuántos
                cuadros seguidos se repite `cell`, y al llegar a `cell_frames` pasa a
                `shown = cell` (`None` también es candidato). El candidato se
                resetea al fijar.
            *   Propiedades: `active` (`lock_cell is not None`) y `hold` (sección 3,
                calculado con `t_last`).
        *   Borrar `class Pinch`.
        ```
    *   Location: §2 table row `"dwell"` (L193). Change "ninguno; vale `hold_ms`" to "ninguno; vale `hold_ms`, y re-arma al moverse (`rearm_on_move`)".
    *   Location: Alternative L (L454-461). Replace with:
        ```markdown
        #### L: Envolver `Pinch` con `Confirm` sin cambiarlo

        *   **Pros**: deja `Pinch` y su test sin tocar.
        *   **Cons**: para cancelar hay que llamar `pinch.update(None)`, y con los
            dedos todavía juntos `Pinch` se vuelve a activar en el mismo cuadro. Re-
            armar, medir el radio desde el punto fijado y el `dwell` necesitarían un
            caso aparte cada uno. `hold` tendría que leer `closed_since` y `min_s`.
        *   **Reason for Rejection**: una sola tabla de estados en `Confirm` es más
            corta que esos parches, y `Pinch` no tiene otro uso (`hands.py:79`).
        ```

### [Issue 2] [`design`, `structural`, `zoom-out`] - Severity: High
*   **Affected Scope:** whole document. Insert between [Lines 340-342](docs/designs/hand_interaction.md#L340-L342) (end of §8, before "## Alternatives Considered").
*   **Discrepancy Description:** There is no Risks & Mitigations section, which the standard requires. Risks are scattered across OQ1, Alternatives D, F and H, and the Goals.
*   **Rationale:** The standard requires that the spec state its own failure modes and how each is mitigated.
*   ***AI Suggestion:*** PROPOSE FIX (and contest the "security" item)
*   ***Justification:*** Valid. Five rows cover it, and each points at a mitigation the doc already has. I contest D-B2's security item: `hold` is a float and `box` is four pixel coordinates sent to the same viewer that already receives the video, so no trust boundary is crossed. The "re-arm" item is closed by Issue 1. The "old `.dj`" item is closed by L515-518 and Issue 6.
*   ***Proposed Edit:***
    *   Location: new H2 after L340.
    *   Change:
        ```markdown
        ## Risks & Mitigations

        | Riesgo | Mitigación |
        |---|---|
        | Una mano abierta o relajada con el medio estirado cuenta como "cerrada" (`on = 0,35` son ~3 cm entre puntas) y empieza el gesto sobre un destino válido. | El paso G2 del control incluye "mano abierta quieta sobre un destino válido". Los histogramas de E1 tienen que separar apuntar, dos dedos juntos y mano abierta. Si no separan: `gesture = "dwell"`. |
        | La profundidad de `hand_world_landmarks` la estima el mismo modelo con la misma imagen, así que el ratio 3D puede no ser mejor que el 2D justo con las puntas alineadas a la cámara. | `dbg` registra los dos ratios (`metric` y `metric2d`). Si en E1 el 2D separa mejor, se cambia la métrica antes del 20/11 (una línea). |
        | `dwell` confirma cualquier pausa de 1 s sobre una casilla, y al mover la mano suena tic/cancelación. | Es solo el plan B. Los sonidos tienen umbral (`hold` ≥ 0,15, ítem 12), y el paso 7 del control lo prueba. |
        | E1 no llega a 9/10 desde algún lado. | `dwell`, después el mouse o el puntero ArUco, como prevé `concepts_brief.md`. |
        | La caja no cubre el antebrazo ni el cuerpo de una criatura alta cuya base queda fuera de la caja. | Aceptado (OQ1). |
        ```

### [Issue 3] [`zoom-out` Z5-1, Z8-2; `comprehension` S6#8] - Severity: Medium — **needs your decision**
*   **Affected Scope:**
    *   Spec: [L89-95](docs/designs/hand_interaction.md#L89-L95) (G5, G6), [L114-115](docs/designs/hand_interaction.md#L114-L115), [L130-131](docs/designs/hand_interaction.md#L130-L131) (OQ3), [L189-193](docs/designs/hand_interaction.md#L189-L193), [L270-296](docs/designs/hand_interaction.md#L270-L296), [L463-470](docs/designs/hand_interaction.md#L463-L470) (Alt M), [L500-502](docs/designs/hand_interaction.md#L500-L502) (Change 4).
    *   Plan: items 1, 3, 4, 14 and 18.
*   **Discrepancy Description:** The three gesture modes bring a `gesture` enum, two TOML subtables, a `gesture_params` builder and an old-key warning.
    *   The `pinch` mode keeps the gesture the Problem section shows is wrong.
    *   The safety nets the doc relies on are the mouse and `dwell`.
    *   The warning guards a stale `config.toml` that doesn't exist, because item 3 rewrites the only one.
*   **Rationale:** Cutting `pinch` removes both subtables, OQ3, Alternative M, the warning and the concepts_brief edit.
*   ***AI Suggestion:*** PROPOSE FIX — **reverses Change 4, which you decided against the brief**
*   ***Justification:*** The critique holds. G6 promises "el gesto viejo se puede elegir por config", but nothing in the Verification Plan uses that option, and the fallbacks the plan does use are `dwell` and the mouse. It is still your call, because it undoes a recorded decision. If you reject it, Issue 1 still works unchanged.
*   ***Proposed Edit (only if you accept):***
    *   §6 config becomes:
        ```toml
        [hands]
        gesture = "touch"        # "touch" | "dwell"
        on = 0.35                # se calibra con histogramas (E1)
        off = 0.45
        extended_on = 1.15
        extended_off = 1.05
        hold_ms = 1000
        cancel_radius_mm = 20
        cell_frames = 3
        box_margin = 0.15
        input_width = 640
        ```
        Delete L292-294 (the old-key warning). Keep "Los `on/off` arrancan como suposición: el valor real sale de E1."
    *   §2 table: delete the `"pinch"` row, and change "Umbrales" to `[hands] on, off`.
    *   G5: delete ", y hay un aviso si aparecen las claves viejas (`pinch_on/off`)".
    *   G6: delete ", y el gesto viejo (pulgar-índice) se puede elegir por config".
    *   Non-Goals L114-115: change to "**Volver al pinch pulgar-índice.** Queda en el historial de git."
    *   OQ3: delete it.
    *   Alternative M: replace its Reason with "con claves planas en `[hands]` y un solo `config.toml`, que este cambio reescribe, no hay configs viejas que proteger".
    *   Change 4: make it "`gesture = "touch"|"dwell"` y claves planas en `[hands]`, en lugar de `confirm_on/off/ms`".
    *   Item 1:
        *   Delete the `"pinch"` branch of `gesture_metric` and the old-key bullets (L548-551, L554).
        *   `gesture_params` reads only `[hands]` and returns `{gesture, on, off, ext_on, ext_off, hold_ms, cancel_radius_m, cell_frames, box_margin, rearm_on_move}`.
    *   Item 3: change "las subtablas `[hands.touch]` y `[hands.pinch]`" to "las claves de la sección 6", and drop the sentence about the subtables' position.
    *   Item 4: delete `test_gesture_params_warns_old_keys`, and add `test_gesture_params` (dwell → `rearm_on_move` True; `cancel_radius_m == 0.02`).
    *   Item 14 L809-810: "(`touch` o `dwell`)".
    *   Item 18 L847-849: "con histéresis (`[hands] on/off` en `config.toml`)".
    *   Verification L909: "`[hands] on/off`".

### [Issue 4] [`design` D-M1, D-M2; `zoom-out` Z8-2] - Severity: Medium
*   **Affected Scope:** [L265-267](docs/designs/hand_interaction.md#L265-L267) (`dbg`), [L369-375](docs/designs/hand_interaction.md#L369-L375) (Alt C), [L908-910](docs/designs/hand_interaction.md#L908-L910) (Verification step 3), and item 1 publish dict (L602-606).
*   **Discrepancy Description:** Two gaps.
    *   The default `on = 0.35` counts a relaxed open hand as "closed", and the G2 test doesn't include a hovering open hand.
    *   The claim that 3D world landmarks beat the 2D ratio is unproven, because z comes from the same monocular crop.
*   **Rationale:** Both are risks to G2 that E1 can measure, if the data is logged.
*   ***AI Suggestion:*** PROPOSE FIX (and contest the "selectable 2D mode" part)
*   ***Justification:*** Both concerns are valid. Logging the 2D ratio gives E1 the comparison data at the cost of one dict entry. A selectable 2D mode (D-M2) would bring back the config machinery that Issue 3 removes, so I contest that part.
*   ***Proposed Edit:***
    *   `dbg` (§5 L265 and item 1 L603-606): add `metric2d` = `d2(lm8,lm12) / d2(lm0,lm9)`. Also add it to the debug line in item 13.
    *   Verification step 3: after "sin confirmaciones falsas", add "incluida una mano abierta quieta 3 s sobre un destino válido". After "línea de debug", add "Los histogramas de E1 comparan `metric` y `metric2d` para apuntar, dos dedos juntos y mano abierta."

### [Issue 5] [`codebase-details` CD-M1; `implementation-readiness` IR-M1, IR-M4; `style` ST-M3, ST-M4; `comprehension` S6#9] - Severity: Medium
*   **Affected Scope:** [Lines 588-606](docs/designs/hand_interaction.md#L588-L606) (`hands_loop`) and [L545-554](docs/designs/hand_interaction.md#L545-L554) (`gesture_params`)
*   **Discrepancy Description:** The per-frame nesting is ambiguous, so `update` appears to run twice on no-hand frames. Several things are unspecified or wrong:
    *   `ext_on`/`ext_off` for non-touch gestures, the `extended` formula, and the no-hand `dbg` contents are never given.
    *   `p.ext_off` uses attribute access on a dict.
    *   `round(metric, 3) or None` turns dwell's 0.0 into `None`, and `inf` would reach JSON as `Infinity`.
    *   `cfg` is really `cfg["hands"]` (`__main__.py:110`).
*   **Rationale:** An implementer would have to guess at each of these, and the JSON issue breaks the browser's `JSON.parse`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Pulling the dict building into a pure helper also makes it testable (Issue 7).
*   ***Proposed Edit:***
    *   Location: replace L588-606.
    *   Change:
        ```markdown
        *   `def hand_msg(conf, lm2d, metric, metric2d, extended, box_margin) ->
            dict`, pura, para que se pueda testear:
            *   sin mano (`lm2d None`): `dict(NO_HAND, cell=conf.shown,
                dbg={"metric": None, "metric2d": None, "extended": False,
                "hold": 0, "lock_cell": None, "reason": conf.reason})`;
            *   con mano: `{"cell": conf.shown, "pinch": conf.active, "px":
                lm2d[8], "hold": round(conf.hold, 2), "box": [u0, v0, u1, v1],
                "dbg": {...}}`. `box` es el mínimo y el máximo de `lm2d`,
                agrandados `box_margin × (ancho, alto)` por lado y redondeados a
                0,1 px. En `dbg`, `metric` vale `None if math.isinf(metric) else
                round(metric, 3)`.
        *   `hands_loop(get_packet, publish_hand, on_tap, stop, K, dist, spec,
            cfg)`, misma firma. `cfg` es la tabla `[hands]`, como hoy
            (`__main__.py:110`).
            *   `p = gesture_params(cfg)` y `conf = Confirm(p["on"], p["off"],
                p["hold_ms"], p["cancel_radius_m"], p["cell_frames"],
                p["rearm_on_move"])`.
            *   Por cuadro, sin `lm`: `conf.update(None, None, None, t)`, se
                publica `hand_msg(conf, None, ...)` y `continue` (como
                `hands.py:88-91` hoy).
            *   Por cuadro, con `lm`:
                *   `ext_thresh = p["ext_off"] if conf.active else p["ext_on"]`;
                    `extended = middle_extended(lmw, ext_thresh)`;
                    `metric = gesture_metric(p["gesture"], lm2d, lmw, ext_thresh)`.
                *   Si `pose.ok`: `xy = image_to_board(*lm2d[8], ...)` y
                    `cell = cell_at(*xy, spec)`. Si no, `xy = cell = None`.
                *   `tap = conf.update(metric, cell, xy, t)`; si `tap is not None`,
                    `on_tap(tap)`.
                *   Se publica `hand_msg(...)`.
        ```
    *   Location: `gesture_params` (L545-554). Add: "Para `dwell`, `on`/`off` valen `0.5`/`0.5` y `ext_on`/`ext_off` valen `0.0`. `cancel_radius_m = cancel_radius_mm / 1000`. `rearm_on_move = gesture == "dwell"`. La config usa `extended_on/off`; el dict los devuelve como `ext_on/ext_off`." Add `import math` at the top of `hands.py`.

### [Issue 6] [`implementation-readiness` IR-M2; `codebase-details` CD-M2; `design` D-N4] - Severity: Medium
*   **Affected Scope:** [Lines 622-625](docs/designs/hand_interaction.md#L622-L625) (`scale_hand`) and [L680-683](docs/designs/hand_interaction.md#L680-L683) (test)
*   **Discrepancy Description:** Old `.dj` files have no `box` key, and `recording.replay` passes recorded headers through `encode_remote`. "Multiplicados cuando no son `None`" doesn't say what happens when the key is missing, so a remote `--replay` could raise `KeyError`.
*   **Rationale:** This breaks the compatibility claim at L515.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. `recording.py:55-56` sends recorded headers through this path.
*   ***Proposed Edit:***
    *   L623-625: change to "devuelve una copia con `px` y `box` multiplicados por `(sx, sy)` cuando `hand.get(...)` no es `None`. Las claves que no están no se agregan."
    *   L680-683: append "Un segundo caso con el `hand` viejo `{cell, pinch, px}` (sin `box`) no levanta error y no agrega `box`. `net_cfg = {"remote_width": 640, "remote_quality": 60}`."

### [Issue 7] [`implementation-readiness` IR-M3; `codebase-details` CD-N4; `style` ST-N7] - Severity: Medium
*   **Affected Scope:** [Lines 642-675](docs/designs/hand_interaction.md#L642-L675) (item 4 tests) and [L899-901](docs/designs/hand_interaction.md#L899-L901) (coverage rule)
*   **Discrepancy Description:** Tests are missing for:
    *   "suelta"
    *   `hold_ms = 0`
    *   re-arm
    *   `dwell` two taps
    *   `extended` hysteresis
    *   `box` math

    Also, `test_confirm_uses_locked_cell` derives cell 6 from a 10 mm move, which the geometry doesn't support (about 13.9 mm to the edge). The tests also rely on config values they never state.
*   **Rationale:** The coverage rule says every branch has a test.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, and Issue 1 changes which branches exist.
*   ***Proposed Edit:***
    *   L645-646: change to "El test de `Pinch` (`test_hands.py:9-19`) se borra junto con la clase. El de `image_to_board` queda. Todos los tests de `Confirm` lo construyen explícito con `Confirm(0.35, 0.45, 1000, 0.02, 3, False)`, salvo que se diga otra cosa. Se agregan:"
    *   `test_confirm_uses_locked_cell`: "a los 500 ms se pasa `cell=6` sintético con un `xy` a 10 mm de `lock_xy`. Dispara con `5`."
    *   `test_confirm_cancels_outside_radius`: "un `xy` a 30 mm de `lock_xy` cancela con `reason == "salió"` y `hold == 0`. Con la métrica todavía cerrada no vuelve a fijar. Después de una métrica `> off` y otra vez cerrada, fija de nuevo."
    *   Add:
        *   `test_confirm_edge_lock`: fixed on cell 0 with `xy` 30 mm from its centre, it doesn't cancel and it fires.
        *   `test_confirm_release_reason`: opening before 1 s gives `reason == "suelta"`, and opening after the fire leaves `reason == ""`.
        *   `test_confirm_dwell_two_taps`: `rearm_on_move=True` with the metric always 0. It fires on 5, the `xy` moves 30 mm with `cell=6`, and it fires on 6.
        *   `test_confirm_hold_ms_zero`: it fires on the lock frame and `hold == 1`.
        *   `test_hand_msg`: `box` with its margin and rounding, `metric inf → None`, and `0.0` stays `0.0`.
    *   `test_gesture_metric` L667: change "(w12 cerca de w9)" to "(`|w12-w0| / |w10-w0|` por debajo de `extended_off`)".
    *   L899-901: "Cada fila de la tabla de `Confirm` (sección 3) y el debounce tienen al menos un test que falla si se rompen."

### [Issue 8] [`comprehension` S6#4; `structural` S-4, S-10; `style` ST-M4] - Severity: Medium
*   **Affected Scope:** [Lines 119-140](docs/designs/hand_interaction.md#L119-L140) (Open Questions)
*   **Discrepancy Description:** OQ3 says "Falta confirmar", but Alternative M and Change 4 treat it as decided. OQ4 and OQ5 are marked "propuesto" but used as settled. OQ1 is "resuelta" but still listed as open.
*   **Rationale:** A reader can't tell what is still open.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. Only OQ2 (the numeric defaults) is genuinely open, because E1 decides it.
*   ***Proposed Edit:*** Rename the section to "## Open Questions y decisiones". Then:
    *   OQ1: keep "(resuelta: opción B)".
    *   OQ2: keep "(abierta: la cierra E1)".
    *   OQ3: delete it if Issue 3 is accepted. Otherwise change it to "(resuelta: subtablas, ver alternativa M)".
    *   OQ4: change to "**OQ4 (resuelta): el radio de cancelación es 20 mm, medido desde el punto donde se fijó el dedo** (sección 3)". Keep the cell sizes and change the last sentence to "Con 20 mm se absorbe el temblor de ~10 mm, y como se mide desde `lock_xy` no depende del tamaño de la casilla."
    *   OQ5: change "(propuesto: …)" to "(resuelta: …)".

### [Issue 9] [`comprehension` S6#5, S6#14; `design` D-N1; `style` ST-M4, ST-N11; `zoom-out` Z8-5] - Severity: Medium
*   **Affected Scope:** [Lines 29-31](docs/designs/hand_interaction.md#L29-L31) (Overview dates), [L59-61](docs/designs/hand_interaction.md#L59-L61), [L909-910](docs/designs/hand_interaction.md#L909-L910)
*   **Discrepancy Description:** Several terms are undefined:
    *   "el control"
    *   "16-18/11"
    *   "los 5 estudiantes"
    *   E1-E3, which are used before their definition at L511
*   **Rationale:** This is a comprehension gap, and every acceptance criterion depends on "el control".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The facts are in the repo: control 2 is days 14-16 of the plan (`concepts_brief.md:264`, `dejarik_ar.md:1329`), the brief puts it "antes del 16-18/11" (`hand_interaction_brief.md:138`), and "los 5 estudiantes" are the team (`hand_interaction_brief.md:117`).
*   ***Proposed Edit:***
    *   Location: replace L29-31.
    *   Change:
        ```markdown
        Etapas y fechas:

        *   **E0:** medir el gesto actual con el overlay de debug, sin tocar código.
        *   **E1:** el gesto nuevo en Python.
        *   **E2:** el anillo, los sonidos, el HUD y los docs.
        *   **E3:** "se deja atravesar".
        *   **E4:** oclusión real, opcional.
        *   **El control** es el control 2 del plan general (días 14-16,
            [concepts_brief.md](../../concepts_brief.md)), entre el 16 y el
            18/11. Ahí los 5 integrantes del equipo miden E1-E3 contra E0.
        *   E4 solo entra si E1-E3 cierran antes del **18/11**. El
            congelamiento es el **20/11/2026** y la demo el **26/11/2026**.

        El mouse (`--input mouse` / `--input both`) es la entrada de respaldo
        si la mano no llega a los criterios.
        ```
    *   L909-910: "mirando la línea de debug con la mano de cada uno de los 5 integrantes".

### [Issue 10] [`design` D-M7; `structural` S-3, S-11; `style` ST-N7] - Severity: Medium
*   **Affected Scope:** [Lines 342-481](docs/designs/hand_interaction.md#L342-L481) (Alternatives)
*   **Discrepancy Description:** Rejections are attributed to "Rechazado por el autor" or "(aprobó el Technical Plan)" without a linked record.
    *   C rests on "pidió medirlo en 3D".
    *   G is a deferral condition, not a rejection.
    *   E is labelled as a rejection but is kept.
*   **Rationale:** The Alternatives Rule requires a concrete trade-off.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The author decisions are real and recorded in `hand_interaction_brief.md`, but the reviewers couldn't see it because it wasn't linked. Linking it once (Issue 16) and leading each reason with the trade-off fixes both problems.
*   ***Proposed Edit:***
    *   L344-345: append "Todas las decisiones son del autor y están registradas en [hand_interaction_brief.md](../../hand_interaction_brief.md). Abajo va el motivo técnico de cada una."
    *   Remove the prefixes "Rechazado por el autor: " and "Rechazado por el autor (aprobó el Technical Plan): " (13 places). Each reason then starts with its trade-off.
    *   C reason: "en 2D, desde el lado cercano, las puntas alineadas con la cámara parecen juntas. El ratio 3D no depende de esa dirección si el modelo estima bien la profundidad, y E1 lo verifica comparando con el 2D (`metric2d`)."
    *   G reason: "una sola profundidad está mal para los nudillos y el brazo, y además requiere enmendar `concepts_brief.md:328`. F, que no tiene esos problemas, ya está fuera del alcance obligatorio."
    *   E: change the label "Reason for Rejection" to "**Estado**: plan B, no se descarta."

### [Issue 11] [`codebase-details` CD-M3] - Severity: Medium
*   **Affected Scope:** [Lines 697-712](docs/designs/hand_interaction.md#L697-L712) (item 7)
*   **Discrepancy Description:** `docs/protocol.md:3` says the file is frozen from day 2 and that any change bumps `v`. Item 7 adds fields but keeps `v: 1`.
*   **Rationale:** The implementer would have to settle a project rule.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid (`protocol.md:3` verified). Its last sentence ("Cada lado ignora los campos que no conoce") already supports additive fields, but the rule should say so explicitly.
*   ***Proposed Edit:*** Replace the L710-711 bullet with: "La línea 3 pasa a ser: "**Se congela el día 2.** Agregar un campo opcional no sube `v`, porque cada lado ignora los campos que no conoce. Cambiar o quitar un campo sí: se sube `v` y se cambian Python y el navegador en el mismo commit."" Change L712 "**Por qué**" to: "E2, y deja escrita la regla que permite no subir `v`."

### [Issue 12] [`implementation-readiness` IR-M5; `codebase-details` CD-M4, CD-N7; `style` ST-M6; `design` D-N3, D-N5, D-M5] - Severity: Medium
*   **Affected Scope:** [Lines 310-316](docs/designs/hand_interaction.md#L310-L316), [L743-744](docs/designs/hand_interaction.md#L743-L744), [L760-784](docs/designs/hand_interaction.md#L760-L784)
*   **Discrepancy Description:** Several browser details are wrong or missing:
    *   `#hint` "centrado abajo" overlaps `#combat` (`style.css:33`).
    *   The E3 block is guarded by `h?.box && pose.ok`, so `pass` never decays back to 0.
    *   The creature projection is "la misma cuenta que `project`", but `project` takes board coordinates.
    *   `cellCenter` is not imported (main.js:3).
    *   The hold sounds fire on any brief lock, which gives a tic/cancel stream in `dwell`.
    *   `uPass` must be per material.
*   **Rationale:** Each of these is a guess left to the implementer, or a visible bug.
*   ***AI Suggestion:*** PROPOSE FIX (and contest the `uPass` part)
*   ***Justification:*** The rest is valid. I contest the `uPass` part: L305 already says "un uniform nuevo por material" and L862 puts it in `mat.userData.pass`, the same as `uFlash`. The implementation-readiness reviewer confirmed that this pattern is right.
*   ***Proposed Edit:***
    *   L743-744: "`#hint`: `bottom: 64px; left: 50%; transform: translateX(-50%)`, encima de `#combat` (`style.css:33`), con el mismo estilo de caja que los demás `#hud > div`."
    *   L762-764: "si `prevHold < 0.15 && hold >= 0.15`: `audio.play("holdStart")`; si `prevHold >= 0.15 && prevHold < 1 && hold === 0`: `audio.play("holdCancel")`. El umbral evita sonidos por fijaciones de un par de cuadros, sobre todo en `dwell`."
    *   L775-783: "**E3:** después del bloque de `poseAlpha`, **siempre**, para cada criatura de `army.byId`: `target = 1` si `h?.box`, `lastHeader.pose.ok` y la raíz cae dentro de `h.box`; si no, `0`. Después, `c.pass += (target - c.pass) * Math.min(1, dt / 0.05)` y `c.setPass(c.pass)`. La raíz se pasa a píxeles con `toPx(c.root.getWorldPosition(tmp))`, donde `toPx(v)` es la parte de `project` que aplica `projectionMatrix` y convierte de NDC a píxeles. `project` pasa a usar `toPx`."
    *   L784: "`main.js:3` pasa a `import { createScene, cellCenter } from "./scene.js"`."
    *   L310-312: replace "con la misma cuenta que `project` (`main.js:88`)" with "con la proyección de `project` (`main.js:84-89`) partiendo de la posición de mundo".

### [Issue 13] [`style` ST-M2 (S7), ST-M7 (S9); `zoom-out` Z8-8] - Severity: Medium
*   **Affected Scope:** [Lines 75-88](docs/designs/hand_interaction.md#L75-L88) (G3, G4) and [L911-915](docs/designs/hand_interaction.md#L911-L915)
*   **Discrepancy Description:** The G3 and G4 criteria name no tester count and no pass threshold. G3's title promises "sin mirar la pantalla", but the criterion never tests it.
*   **Rationale:** As written, neither criterion can be checked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. A light threshold is enough for a student demo.
*   ***Proposed Edit:***
    *   G3 title: "**G3: el jugador sabe en qué estado está el gesto.**"
    *   G3 criterion: "2 de 3 personas que prueban por primera vez dicen, sin explicación, si el gesto se confirmó o se canceló."
    *   G4 criterion: "2 de 3 personas sin contexto describen la mano sobre una criatura como que "la atraviesa", y ninguna la confunde con "Tracking perdido"."
    *   Mirror both criteria in Verification steps 4 and 5.

### [Issue 14] [`style` ST-M3 (S7), ST-M1 (S9)] - Severity: Medium
*   **Affected Scope:** [L96-98](docs/designs/hand_interaction.md#L96-L98), [L327-329](docs/designs/hand_interaction.md#L327-L329), [L530-531](docs/designs/hand_interaction.md#L530-L531), [L751](docs/designs/hand_interaction.md#L751), [L806-807](docs/designs/hand_interaction.md#L806-L807), [L818-819](docs/designs/hand_interaction.md#L818-L819), [L827](docs/designs/hand_interaction.md#L827)
*   **Discrepancy Description:** G7 asks for one phrase for the gesture, but the doc uses five versions of it. Separately, `hand.pinch` keeps its old name but now means "gesture closed".
*   **Rationale:** The doc breaks its own goal.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. The `HINT` constant is the natural single source.
*   ***Proposed Edit:***
    *   G7: "Se usa una sola frase, **"Apuntá con el índice y juntá dos dedos"**: es la constante `HINT` de `hud.js` y se copia igual en el README, `docs/rules.md` y el guion."
    *   Use that exact phrase at L531 (docstring), L806-807 (README: "…o apuntá con el índice y juntá dos dedos (con el índice apoyado en el papel; se sostiene con un anillo de carga)…"), L819 and L827.
    *   §5 L256: append "El nombre queda por compatibilidad con el protocolo v1."

### [Issue 15] [`style` ST-M1, ST-M5, ST-M6 (S7), ST-M5 (S9); `comprehension` S6#3, S6#12; `design` D-N2, D-N6; `codebase-details` CD-N8; `zoom-out` Z5-7, Z8-6] - Severity: Medium
*   **Affected Scope:** [L41-44](docs/designs/hand_interaction.md#L41-L44), [L52-53](docs/designs/hand_interaction.md#L52-L53), [L198](docs/designs/hand_interaction.md#L198), [L300-316](docs/designs/hand_interaction.md#L300-L316), [L421](docs/designs/hand_interaction.md#L421), [L867-870](docs/designs/hand_interaction.md#L867-L870), [L885-887](docs/designs/hand_interaction.md#L885-L887)
*   **Discrepancy Description:** Several claims are false or overstated:
    *   L43 "~4 cm" contradicts OQ4.
    *   "Sin bajar el brillo" contradicts the opacity drop, and the shader's average brightness also drops (`hologram.js:36`).
    *   "La misma suavización que `poseAlpha`" is wrong: τ is 0.05 here and 0.1 in `main.js:101`.
    *   "Se componen en vez de pisarse" is overstated: tracking and death still overwrite each other.
    *   ~1.25, 3-4 cm and +10-20 ms are presented as measurements.
    *   "No hay error de altura" ignores landmark 8 sitting 5-8 mm above the pad.
*   **Rationale:** A reader can't trust the numbers or the descriptions.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each one checks out against the code or against the doc itself. Fix the claims; don't add an opacity factor (Z8-6).
*   ***Proposed Edit:***
    *   L41: "a unos 3-4 cm del papel (estimado)".
    *   L43-44: "Eso es una casilla interior entera o más (~37 mm en dirección radial y ~28 mm de arco, OQ4), así que…".
    *   L52-53: "(con el dedo en el papel el error de altura baja a lo que hay entre la uña y la yema, ~5-8 mm)".
    *   L198: "Con el dedo estirado se estima ~1,25…".
    *   L306-308: "El look es "parpadeo fuerte y translúcido": la opacidad baja a ~0,35 y el parpadeo crece (el brillo promedio baja un poco). Se distingue de "Tracking perdido" porque aquel es un fundido parejo a 0,2, sin parpadeo extra, con el aviso en el HUD."
    *   L313-314: "con una suavización exponencial como la de `poseAlpha` pero más rápida, τ ≈ 0,05 s".
    *   L300-302: replace "que se pisan" with "(que entre sí se pisan, y eso no cambia acá)".
    *   L421: "(estimado +10-20 ms por cuadro)".
    *   L869-870: "**Por qué**: G4. Más parpadeo además de la opacidad baja, para que no se confunda con el fundido parejo de "Tracking perdido"."
    *   L885-887: "**Por qué**: `pass` se compone con la opacidad que ya existe en vez de pisarla. El tracking (`main.js:102`) y la muerte (`events.js:51`) siguen escribiendo los dos en `baseOpacity`, como hoy."

### [Issue 16] [`structural` S-2, S-5] - Severity: Medium
*   **Affected Scope:** [Lines 483-506](docs/designs/hand_interaction.md#L483-L506)
*   **Discrepancy Description:** "Additional Resources" and "Cambios respecto del brief" are H3s nested under Alternatives. The cited files are written as plain code text, not links.
*   **Rationale:** A table of contents misfiles them, and readers have to find the sources themselves.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, and it is the root cause of Issue 10: the reviewers couldn't find the brief.
*   ***Proposed Edit:*** Change both headings to `##`. Turn the bullets into links:
    *   `[hand_interaction_brief.md](../../hand_interaction_brief.md)`
    *   `[concepts_brief.md](../../concepts_brief.md)`
    *   `[dejarik_ar.md](dejarik_ar.md)`

### [Issue 17] [`codebase-details` CD-M5; `implementation-readiness` IR-N9] - Severity: Medium
*   **Affected Scope:** [Lines 826-830](docs/designs/hand_interaction.md#L826-L830) (item 16)
*   **Discrepancy Description:** `demo_script.md` has no row for "the first time the host uses the hand", and the new fallback row is missing columns.
*   **Rationale:** The implementer would have to choose the row.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. The 0:20-1:10 row is where the host first moves a piece (`demo_script.md:19`).
*   ***Proposed Edit:*** L826-827: "En la fila 0:20–1:10, después de "el anfitrión mueve", agregar: "con la mano; el narrador dice: "Apuntá con el índice y juntá dos dedos"". L828-830: "En la tabla de respaldos (línea 38), una fila: `| El gesto da confirmaciones falsas | Pasar al plan B y reiniciar | \`gesture = "dwell"\` en \`config.toml\` | — |`."

### [Issue 18] [`design` D-M4; `zoom-out` Z8-3] - Severity: Medium
*   **Affected Scope:** [Lines 250-253](docs/designs/hand_interaction.md#L250-L253)
*   **Discrepancy Description:** The browser infers "cancel" from sampled `hold` values. That is fragile on the 15 fps remote, so the reviewer asks for an explicit `result` field or an attempt counter.
*   **Rationale:** A false or missed cancel sound.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** The doc already says the remote never plays the ring or the hold sounds: L772-774 ("si `you === 1`, el anillo y los sonidos de hold no se muestran"). The host gets every frame. The one host-side gap, a cancel followed by an immediate re-lock, is closed by Issue 1: after "salió" or "afuera", `Confirm` stays unarmed until the fingers open, so at least one frame publishes `hold = 0`. Issue 12's 0.15 threshold covers `dwell`. A new field would add protocol, doc and test lines for a case that can't happen.
*   ***Proposed Edit:*** none.

### [Issue 19] [`zoom-out` Z5-5] - Severity: Low
*   **Affected Scope:** [Lines 864-867](docs/designs/hand_interaction.md#L864-L867)
*   **Discrepancy Description:** `sin(uTime * (37 + 40·uPass))` changes the frequency while `uPass` fades. Because `uTime` grows over the session, this sweeps the phase by thousands of radians and gives chaotic flicker.
*   **Rationale:** A visible glitch on every fade.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid, and the fix is one token.
*   ***Proposed Edit:*** Change the formula to `float flicker = 1.0 - (uFlicker + 0.35 * uPass) * (0.5 + 0.5 * sin(uTime * 37.0) * sin(uTime * 13.0));`, and change L867 to "`uPass` sube la amplitud del parpadeo. La frecuencia no cambia, porque cambiarla con `uTime` grande hace saltar la fase."

### [Issue 20] [`zoom-out` Z5-6; `comprehension` S6#10; `implementation-readiness` IR-N1, IR-N8] - Severity: Low
*   **Affected Scope:** [L317-320](docs/designs/hand_interaction.md#L317-L320), [L738-742](docs/designs/hand_interaction.md#L738-L742), [L766-770](docs/designs/hand_interaction.md#L766-L770)
*   **Discrepancy Description:** The ring offset is "~60 px del cuadro" at L319 but "(+40, -40)" px of `#stage` at L770, and the anchor is unspecified. Z5-6 also asks to drop the cosmetic constants in favour of constraints.
*   **Rationale:** The two values contradict each other.
*   ***AI Suggestion:*** PROPOSE FIX (and contest dropping the constants)
*   ***Justification:*** The conflict is real. I contest dropping the constants from the implementation plan: the readiness reviewer asked for *more* exact values (IR-N1, IR-N8), and the readiness standard wants concrete values in the DetailedRange. They stay as starting values to tune by eye.
*   ***Proposed Edit:*** L318-319: "…más un corrimiento fijo arriba a la derecha (ítem 12) para que el dedo no lo tape." L770: "El centro del `<div>` va ahí más `(+40, −40)` px de `#stage` (`left = x + 40 − 22`, `top = y − 40 − 22`), con `style.setProperty("--p", hold)`." L739-740: specify the mask as `mask: radial-gradient(circle, transparent 55%, #000 57%)`. L796: "`strokeStyle = "rgba(255,255,255,0.5)"`", and the metric in the debug line uses `toFixed(2)`.

### [Issue 21] [`comprehension` S6#11, S6#15; `style` ST-N4] - Severity: Low
*   **Affected Scope:** [L71](docs/designs/hand_interaction.md#L71), [L168](docs/designs/hand_interaction.md#L168), [L247](docs/designs/hand_interaction.md#L247)
*   **Discrepancy Description:** `hand.px` is never defined, and "un radio" in G2 is ambiguous.
*   **Rationale:** A reader has to guess both.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, and a human reader needs both.
*   ***Proposed Edit:*** G2 L70-71: "…La casilla queda fijada al empezar, y el gesto se cancela si la punta del índice se aleja más de `cancel_radius_mm` (20 mm) del punto donde se fijó." §5, after the JSON: "`px`: la punta del índice (`lm2d[8]`) en píxeles del cuadro, o `null` sin mano."

### [Issue 22] [`structural` S-7, S-9; `codebase-details` CD-N6; `style` ST-N6 (S9)] - Severity: Low
*   **Affected Scope:** [L246](docs/designs/hand_interaction.md#L246), [L85](docs/designs/hand_interaction.md#L85), [L638-639](docs/designs/hand_interaction.md#L638-L639)
*   **Discrepancy Description:** The `json` block doesn't parse, L85 runs past the wrap width, and the TOML ordering rationale is wrong.
*   **Rationale:** Small, objective errors.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each fix is one line.
*   ***Proposed Edit:*** L246: change ` ```json ` to ` ```text `. Re-wrap L85 at 80 columns. L638-639, if Issue 3 is rejected: "Las subtablas van después de todas las claves de `[hands]`, porque en TOML una clave después de `[hands.touch]` queda dentro de la subtabla." If Issue 3 is accepted, delete the sentence.

### [Issue 23] [`style` ST-M2 (S9), ST-N2 (S7)] - Severity: Low
*   **Affected Scope:** [L76](docs/designs/hand_interaction.md#L76), [L136](docs/designs/hand_interaction.md#L136), [L904-907](docs/designs/hand_interaction.md#L904-L907)
*   **Discrepancy Description:** "anillo" means both the hold ring and the board rings. "corrido" has three meanings.
*   **Rationale:** At L904, "10 toques por anillo" can be read as taps on the progress ring.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Cheap, and the "anillo" collision really is ambiguous.
*   ***Proposed Edit:***
    *   L66-67, L904 and L906: change "anillo" to "aro del tablero (interior y exterior)".
    *   L76: "desplazado al costado de la casilla".
    *   L135-136: "El "~4 cm / ~7,8 cm" del brief no coincide con esto."

### [Issue 24] [`codebase-details` CD-N2, CD-N5; `implementation-readiness` IR-N3, IR-N4, IR-N5, IR-N6, IR-N7] - Severity: Low
*   **Affected Scope:** [L771](docs/designs/hand_interaction.md#L771), [L891-893](docs/designs/hand_interaction.md#L891-L893), item 1
*   **Discrepancy Description:** Small code details:
    *   `import math` is missing.
    *   `dist` clashes with the distortion parameter.
    *   `prevHint` is not named.
    *   The import check asserts nothing.
    *   It's unstated whether `holdStart` firing late is intended.
    *   It's unstated when the debounce candidate resets.
    *   The test's `net_cfg` lacks `remote_quality`.
*   **Rationale:** Implementer guesswork.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Issues 1, 5 and 6 already cover `math`, `math.dist`, the candidate reset, `net_cfg` and the `holdStart` timing (now a 0.15 threshold). The rest is two lines.
*   ***Proposed Edit:*** L771: "**Pista:** `let prevHint = false`; se llama `hud.hint(show)` solo cuando `show = h?.px != null` cambia." L891-893: "`python -c "import sys, dejarik.hands, dejarik.vision; assert 'mediapipe' not in sys.modules"`."

### [Issue 25] [`implementation-readiness` IR-N10; `codebase-details` CD-N9] - Severity: Low
*   **Affected Scope:** [Lines 833-854](docs/designs/hand_interaction.md#L833-L854) (items 17, 18)
*   **Discrepancy Description:** `dejarik_ar.md:415, 911` and `concepts_brief.md:98, 296` describe the old `hand` contract, but they are not in the file list.
*   **Rationale:** They go stale without notice.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Valid. One sentence per item covers it.
*   ***Proposed Edit:*** Item 17 L840: "No se reescribe el resto. Las líneas 415 (esquema de `hand`) y 911 (`debug.pinch_ratio`) quedan viejas a propósito: el aviso de la línea 380 las cubre." Item 18: add "Las líneas 98 y 296 (`hand` viejo) quedan como están, cubiertas por la nota de 160-164."

### [Issue 26] [`comprehension` S6#13] - Severity: Low
*   **Affected Scope:** [L105](docs/designs/hand_interaction.md#L105), [L314](docs/designs/hand_interaction.md#L314), [L772](docs/designs/hand_interaction.md#L772), [L922](docs/designs/hand_interaction.md#L922)
*   **Discrepancy Description:** Project terms are used without definition: `.dj`, replay, the remote viewer and `you === 1`, `poseAlpha`, the ArUco pointer, and the MediaPipe landmark numbering.
*   **Rationale:** A fresh reader can't follow them.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** This is a Nit. These terms are defined in the general design, which Issue 16 links, and the readers of this doc are the team that built those parts.
*   ***Proposed Edit:*** none.

### [Issue 27] [`structural` S-8, S-12] - Severity: Low
*   **Affected Scope:** [L144](docs/designs/hand_interaction.md#L144), [L7](docs/designs/hand_interaction.md#L7), [L483](docs/designs/hand_interaction.md#L483), [L506](docs/designs/hand_interaction.md#L506)
*   **Discrepancy Description:** "Dónde vive cada cosa" is unnumbered, and horizontal rules are used inconsistently.
*   **Rationale:** Formatting.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** This is a Nit with no effect on the reader. Issue 16 removes the rule that misled the heading tree.
*   ***Proposed Edit:*** none.

### [Issue 28] [`style` ST-N1, ST-N3, ST-N5, ST-N6 (S7); ST-N8, ST-N9, ST-N10 (S9)] - Severity: Low
*   **Affected Scope:** throughout
*   **Discrepancy Description:** Wording issues:
    *   English mixed into Spanish (goal, draft, design, look, debounce)
    *   the ratio notation varies
    *   vague words ("mucho trabajo", "se explica fácil")
    *   rhetorical sentences (L38, L49)
    *   "Por qué" lines that add nothing
    *   hedges ("si no está importado ya", already fixed by Issue 12)
    *   "hay pose" vs `lastHeader.pose.ok`
*   **Rationale:** Style.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** These are Nits. The English words are the team's working register and match the template headings. The notation varies only between the overview and the code-level sections. The one hedge that mattered is fixed by Issue 12.
*   ***Proposed Edit:*** none.

### [Issue 29] [`zoom-out` Z5-4] - Severity: Low
*   **Affected Scope:** [Lines 234-242](docs/designs/hand_interaction.md#L234-L242)
*   **Discrepancy Description:** The suggestion is to use `OneEuro` on `lm2d[8]` instead of the 3-frame debounce, or to drop the debounce if measurement shows it isn't needed.
*   **Rationale:** Reuse of an existing filter.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** This is an optional Nit. After Issue 1, the debounce is also what keeps the locked cell equal to the highlighted one, and `OneEuro` would add lag to the lock point. Revisit it after E0/E1.
*   ***Proposed Edit:*** none.

### [Issue 30] [`design` D-N9; `zoom-out` Z8-7] - Severity: Low
*   **Affected Scope:** [Lines 179-185](docs/designs/hand_interaction.md#L179-L185)
*   **Discrepancy Description:** There is no frame-time budget for the hand thread.
*   **Rationale:** The claim of no added inference cost is unsupported.
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** This is a Nit. World landmarks come from the same `detect_for_video` call, and the new math covers 21 points.
*   ***Proposed Edit:*** none.
