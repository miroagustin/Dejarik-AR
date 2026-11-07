Status: resolved

# Goldfish Annotated Review Report

**Target:** `docs/designs/criaturas_canon.md` (`full file`, 1-673)
**Findings source:** [consolidated_review_report.md](consolidated_review_report.md) (B1-B2, M1-M18, N1-N9)
**Severity mapping:** Blocker = High, Major = Medium, Nit = Low

**Summary:** 27 PROPOSE FIX, 1 CONTEST (in part), 0 ESCALATE, 4 DECLINE (in whole or in part).

**Facts checked in the repo before classifying:**

| Fact | Evidence |
| --- | --- |
| The server reads `web/` from disk on every request with `Cache-Control: no-store`, so `git revert` plus a page reload is enough to roll back the client. This settles contested point 1 in favor of cutting the flag. | `dejarik/transport.py:57-70` |
| The 4 originals are already tracked in git. Item 6 and A1 line 164 are wrong. | `git ls-files assets_src/originals` |
| `check_glb.py` reads `sys.argv` directly and does not expand `*.glb`. | `tools/check_glb.py:185-187` |
| The mirror key is F. | `web/main.js:96` |
| The brief gives 2026-11-26 as the delivery date, with the freeze "bastante antes". | `docs/briefs/concepts_brief_personajes.md:138` |
| `dejarik_ar.md` G3 says "los 5 clips". | `docs/designs/dejarik_ar.md:91` |

## Prioritized Findings & AI Suggestions

### [B1] No Risks section [`egm-structural`, `egm-design`] - Severity: High
*   **Affected Scope:** [Lines 279-289](../../criaturas_canon.md#L279-L289) (Límites conocidos); the section is missing between Alternatives and NFR.
*   **Discrepancy Description:** The standard requires a Risks & Mitigations section. Risks are scattered across the doc.
*   **Rationale:** At most 5 rows. Move "Límites conocidos" into the table.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid, and a table with five rows is the smallest form that satisfies the standard.
*   ***Proposed Edit:***
    *   Location: new `## Riesgos y mitigaciones` before `## Non-Functional Requirements`. Delete "Límites conocidos" (279-289) and move its 3 items into the table as rows 5-6.
    *   Change:
        ```
        | Riesgo | Mitigación | Respaldo en vivo |
        | --- | --- | --- |
        | El gesto de victoria no se lee bien a escala | Se elige en el ensayo (checklist) | `WIN_CLIP = null` y recargar |
        | Los pasos de 12 fps tiemblan en la captura de Teams (15-30 fps) | Ajustar `STEP` mirando el share desde otra cuenta | Revertir el commit 2 |
        | El gesto pisa un `walk` o queda clavado | `celebrate()` vuelve a idle solo si `this.current` sigue siendo el gesto | Revertir el commit 2 |
        | `fight` queda viejo | Se limpia al final de `death` | — |
        | El roster tapa piezas, marcadores del debug o queda bajo `#errors` | Se acepta: el debug es del operador y `#errors` es más importante | Mover `#roster` en `style.css` |
        ```
        Add to the Verification Plan: `*   **Ensayo (checklist):** elegir Wave o Yes en el visor a escala; ajustar STEP mirando el share de Teams; mirar el roster con la cámara real encuadrada.`

### [B2] Rejections credited to the author without links [`egm-structural`, `egm-design`, `egm-style`] - Severity: High
*   **Affected Scope:** [Lines 320-393](../../criaturas_canon.md#L320-L393)
*   **Discrepancy Description:** All seven rejections start "Rejected by author" with no link. Alternative C has no trade-off.
*   **Rationale:** Start each one with the trade-off and link the brief once.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The standard forbids rejections credited to a person without a link. Mostly this means reordering text that is already there. After M12, four rejections remain.
*   ***Proposed Edit:***
    *   A: `**Reason for Rejection**: Contradice la regla "solo canon" y necesita eventos y campos de protocolo nuevos solo para justificar clips ([brief](../briefs/concepts_brief_personajes.md)).`
    *   C: `**Reason for Rejection**: Duplica el resaltado de casilla que ya existe y obliga a una capa de postura por criatura. Pasa a Future Improvements.`
    *   D: `**Reason for Rejection**: Elegir el clip obliga a regenerar los .glb; conservar todos cuesta lo mismo una sola vez ([brief, etapa 1](../briefs/concepts_brief_personajes.md)).`
    *   E: `**Reason for Rejection**: Suma unos 1.07 s de "Esperá…" en cada muerte (ver A3) a cambio de que el gesto no se corte ([brief, decisión 2](../briefs/concepts_brief_personajes.md)).`
    *   The label alternatives are merged; see M12.
    *   Note: the example link in `critic_report.md` and `consolidated_review_report.md` (`../../../briefs/...`) is relative to the reports folder. From the design doc the right path is `../briefs/...`.

### [M1] Cut Commit 4 (Run/Weapon) [`egm-zoom-out`, `egm-comprehension`, `egm-design`, `egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** [Lines 602-654](../../criaturas_canon.md#L602-L654), 403-404, 431, 466, 504, 344
*   **Discrepancy Description:** Commit 4 is optional scope with no goal behind it. It brings 5 defects (`KIND_MOMENTS` ReferenceError, a stop on idle at the middle cell, run speed, the viewer, "pendiente" status).
*   **Rationale:** Cut it and list `run` and `weapon` as unused on purpose.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The doc itself says that without Commit 4 "el diseño igual cumple todos los goals" (line 605). Fixing its 5 defects would cost more than the feature is worth.
*   ***Proposed Edit:***
    *   Delete lines 602-654 completely.
    *   Line 431: `Son tres commits y van en este orden.`
    *   Line 466: `LOOPING` pasa a ser `{idle, walk}` (sin `run`).
    *   Line 504: `` *   `run`: el canon no muestra piezas corriendo; el `walk` alcanza para 2 casillas. `` and `` *   `weapon`: el daño es siempre 1, así que no hay un golpe "más fuerte" que mostrar. ``
    *   Non-Goals (line 84): add Run and Weapon to the list of unused clips.
    *   Future Improvements: `*   **Run para movimientos de 2 casillas.** Necesita pasar por la casilla del medio (walkTo va en línea recta) y una velocidad propia.`
    *   Alternative D (line 344): drop "(Run, Weapon)".

### [M2] Cut the `?clips=basic` flag [`egm-zoom-out`, `egm-design`] - Severity: Medium
*   **Affected Scope:** G7 (79-80), CUJ 4 (134-140), 180-184, 228-229, 246-247, NFR 403-406, item 9 (531-536)
*   **Discrepancy Description:** The flag can't be reached from the `--app` window, `STEP = 0` breaks `walkTo`, and the flag adds branches everywhere.
*   **Rationale:** Roll back with `git revert` plus a reload.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Verified: `transport.py:57-70` serves `web/` from disk with `no-store`, so after `git revert` an F5 in the app window loads the old client without restarting the server.
*   ***Proposed Edit:***
    *   G7: `*   **G7. Rollback barato:** cada commit se revierte solo. Como el servidor lee web/ del disco en cada pedido, git revert y recargar la página alcanza, sin reiniciar.`
    *   Delete CUJ 4 (134-140).
    *   Delete from "Con `?clips=basic`…" through "…en uso." in A2 (180-184). Keep the `console.warn` line if you want it, as its own sentence.
    *   Delete the paragraph at 228-229 and the sentence at 246-247.
    *   NFR rollout: `*   **Rollout y rollback:** tres commits que se revierten por separado (assets, canon, roster).`
    *   Item 9: delete `BASIC`; `STEP = 1/12`.

### [M3] Replace `MOMENTS` with `WIN_CLIP` [`egm-zoom-out`, `egm-style`, `egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** A2 (167-184), A3 diagram (200-201), A6 (256), item 9 (533-546), line 523
*   **Discrepancy Description:** Five of the six entries map a name to itself. A2 says `play("win")` while item 10 says `celebrate()`. `win` means two different things. Nothing imports `MOMENTS`.
*   **Rationale:** One constant.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This removes the contradiction and the overloaded `win` without adding anything.
*   ***Proposed Edit:***
    *   A2 title: `#### A2. El clip de victoria`. Body: `` `Creature` crea una acción por **cada** clip del glTF, no solo por los de `CLIPS`. En `creatures.js` una constante, `WIN_CLIP = "<wave|yes>"`, dice cuál es el gesto de victoria; cambiar de Wave a Yes es tocar esa línea. `Creature.celebrate()` reproduce esa acción sin devolver la promesa. Si la acción no existe (cápsula de reemplazo, o `WIN_CLIP = null`), no hace nada. `` Keep the idle-return paragraph (186-190).
    *   Diagram: `sobreviviente.celebrate()   ← sin await` and `win ──► cada criatura viva con owner == winner: celebrate()`.
    *   A6 / line 523: `MOMENTS.win` → `WIN_CLIP`.
    *   Item 9: delete the `MOMENTS` bullet; `play(name)` stays as it is today plus the one-time `console.warn`.

### [M4] One clock for stop-motion [`egm-zoom-out`, `egm-design`, `egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** A5 (231-250), item 9 `walkTo` + `stepMixer` (547-557), item 11 (576-580)
*   **Discrepancy Description:** The mixer and `walkTo` step on two grids that are out of phase. The `stepMixer(mixer, dt, acc)` signature adds `dt` once per creature (×8). Line 554 states a warning instead of a decision.
*   **Rationale:** One global grid.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One grid is simpler than an accumulator and fixes both defects.
*   ***Proposed Edit:***
    *   A5, replacing lines 233-242: `` Hay un solo reloj de pasos: `tick = Math.floor(performance.now() / 1000 / STEP)`, con `STEP = 1/12` s. `Army.update` llama a `mixer.update` de cada criatura solo cuando `tick` cambia, con el tiempo transcurrido desde el último paso, así todas cambian de pose en el mismo cuadro. El `tween` de `walkTo` (`creatures.js:107`) calcula `t` con el tiempo de ese mismo `tick`, así el cuerpo y las patas saltan juntos. Se cuantizan la posición y el giro de la pieza. El flash del golpe, los fades y la sacudida siguen suaves: son efectos del holograma, no movimiento de la pieza. ``
    *   Alternatives: `#### Alternativa F: hornear los pasos en los samplers del glTF (adapt)` — Cons: no cuantiza el `tween` de `walkTo`, y para ajustar `STEP` en el ensayo hay que regenerar los 4 modelos.
    *   Item 9: replace the `walkTo` and `stepMixer` bullets with `` *   `stepTime()` (exportado): devuelve `Math.floor(performance.now() / 1000 / STEP) * STEP`. `Army.update` y `walkTo` la usan (ver A5). `` Delete "Hay que cuidar…".
    *   Item 11: `runViewer` actualiza el mixer con `stepTime()` igual que `Army.update`.

### [M5] Gesture restarts at game end [`egm-zoom-out`, `egm-design`, `egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** CUJ 3 (126-132), item 9 `celebrate()` (543-546)
*   **Discrepancy Description:** `death` starts the gesture and `win` restarts it on the same survivor.
*   **Rationale:** One guard in `celebrate()`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Item 9, `celebrate()`: start with `Si `this.current` ya es la acción del gesto, no hace nada (así `win` no reinicia el gesto que arrancó en `death`).`
    *   CUJ 3 Then: `el sobreviviente hace el gesto en el handler death. Después, en el handler win, las demás piezas azules vivas hacen el gesto (el sobreviviente lo sigue sin reiniciar) y aparece el banner GANA AZUL.`

### [M6] Detailed Plan duplicates A2-A5 [`egm-zoom-out`] - Severity: Medium
*   **Affected Scope:** items 9-11 (527-580)
*   **Discrepancy Description:** The same mechanisms are described twice, and the two versions already disagree.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** After M2-M5, item 9 keeps only the facts that appear nowhere else: `this.owner`, `celebrate()` and its guard, `stepTime()` exported, the one-time `console.warn`. Each is one line with a pointer "(ver A2/A3/A5)". Item 10 keeps the `fight` steps, because A3 doesn't name `fight` or when it is cleared.
*   ***Proposed Edit:*** Rewrite item 9 as 4 one-line bullets with pointers. In A3, rename `lastFight` to `fight` so it matches item 10.

### [M7] G1 can't be met; G1 and G6 don't match [`egm-design`, `egm-style`, `egm-zoom-out`] - Severity: Medium
*   **Affected Scope:** Overview 29-31, G1 (63-65), G6 (76-78), Open Questions (99-105)
*   **Discrepancy Description:** No candidate clip raises the arms. The gesture only plays when a fight ends in a death, but G6 measures every exchange. G6 has no pass/fail check.
*   ***AI Suggestion:*** PROPOSE FIX (default: lethal-only, narrow G6)
*   ***Justification:*** The default follows Stage 8: in a non-lethal fight, the attack/hit pair already shows who won. **This is a product decision. If you'd rather have the gesture after every exchange, say so**, and the change becomes: `celebrate()` is also called from `hit` for the winner of the exchange, and G6 stays as it is.
*   ***Proposed Edit:***
    *   G1: `*   **G1. Cada momento del canon tiene clip:** moverse, atacar, recibir el golpe, morir y desaparecer. Además, cuando una pelea termina con una muerte, el sobreviviente hace un gesto de victoria (Wave o Yes; ninguno es brazos arriba, ver Open Questions). En las peleas sin muerte, el par attack/hit ya muestra quién ganó.`
    *   G6: `...dicen quién ganó una pelea con muerte solo mirando la animación...`
    *   Open Questions, clip: add `Decide el autor en el ensayo, mirando por Teams. Si ninguno se lee bien, WIN_CLIP = null y no hay gesto.`

### [M8] The Wave/Yes choice is written to SOURCES.md before it is made [`egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** item 7 (505), manual step (521-523), commit 2
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Item 7, line 505: `*   El que pierda entre wave y yes (se completa en el commit 2).`
    *   Commit 2: add item `#### `assets_src/SOURCES.md` (Modify)` — `El clip que no se eligió pasa a "Clips sin usar a propósito" con su motivo.`

### [M9] The title promises a label [`egm-comprehension`, `egm-style`, `egm-structural`] - Severity: Medium
*   **Affected Scope:** lines 1, 21, 25-26, 55, 258, 360
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Title: `# Criaturas fieles al canon: clips y roster legible`
    *   Line 21: `*   **Parte B, roster legible.**`
    *   Line 26: `si el roster se complica, los clips se entregan igual.`
    *   Line 55: `**Roster.**`
    *   Line 258: `### Parte B: roster legible con debug`
    *   Line 360: `### Roster`
    *   Line 57: "La etiqueta no es canon" → "Mostrar la vida no es canon".

### [M10] Four missing context sentences [`egm-comprehension`, `egm-style`] - Severity: Medium
*   **Affected Scope:** Overview (11), G5 (72-75), CUJs/A4 (113, 226), A1 (153)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** These are comprehension gaps. A human reader of this doc alone needs them too.
*   ***Proposed Edit:***
    *   Overview, first sentence: `Dejarik AR es el ajedrez holográfico de Star Wars proyectado sobre un tablero real, para una demo por Teams: un servidor Python con el motor, un cliente en el navegador con las criaturas en 3D y entrada por mano o mouse (ver [el diseño base](dejarik_ar.md)).`
    *   G5, add: `Por cada evento, el cliente anima y responde anim_done; el servidor espera hasta 5 s y mientras tanto la entrada queda bloqueada ("Esperá…").`
    *   Before CUJ 1: `En este doc, "resultado" es lo que decide el motor en un ataque (hit, counter o tie), "evento" es lo que llega a la cola del cliente (attack, hit, death, win) y "clip" es la animación.` CUJ 1 line 113: `sale el resultado hit`.
    *   A1, line 153: `(attack sale de Punch, hit de HitReact y die de Death)`.

### [M11] Timing arithmetic [`egm-comprehension`, `egm-style`] - Severity: Medium
*   **Affected Scope:** A3 (211-216), Alternative E (354-356)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** If the gesture overlaps the fade: 0.75 + 0.2 + max(0.6, 1.67) = 2.62 s, against 1.55 s today, which is +1.07 s.
*   ***Proposed Edit:*** A3: `Si sí se esperara, el handler death duraría unos 2.6 s (die 0.75 + crossfade 0.2 + gesto 1.67, que tapa al fade de 0.6). Eso entra en los 5 s del servidor, pero suma alrededor de 1.1 s de "Esperá…" en cada muerte.` Alternative E Cons: `suma alrededor de 1.1 s de "Esperá…" en cada muerte (ver A3).`

### [M12] Alternative labels [`egm-comprehension`, `egm-structural`, `egm-style`, `egm-zoom-out`] - Severity: Medium
*   **Affected Scope:** 303-393
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Clips: `#### Alternativa A` (stays), `#### Alternativa B (elegida): conservar todos los clips y usar solo los del canon` — `Ver A1-A5.`, C: `#### Alternativa C: salto al seleccionar como ayuda de interfaz` (no "B +"), D, E, F (from M4).
    *   Roster: collapse the three entries into one, `#### Alternativas descartadas: etiquetas sobre las piezas u ocultar el roster`, with one paragraph per option of 2-3 lines and one shared rejection: `La opción elegida (mover #roster con CSS) cumple G4 con una línea y sin JS nuevo; las etiquetas suman proyección por cuadro con espejo a mano, y ocultar el roster no cumple G4.`

### [M13] Headings nested under NFR [`egm-structural`] - Severity: Medium
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Lines 411 and 422: `###` → `##`.

### [M14] The commit 2 check can't be reproduced [`egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** 584-587
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** `*   Los CUJs 1 a 3 con click del mouse. El replay (--replay) solo reproduce la cámara y la mano, no trae combates. *   Para CUJ 2, jugar con mouse hasta que salga un counter.`

### [M15] Duplicate clip names in adapt [`egm-zoom-out`, `egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** item 1 (442-444), item 2 (454-459)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The real models have no collisions (A1 measured them). One rule is enough.
*   ***Proposed Edit:***
    *   Item 1: `...en minúscula, en el orden de origen. Si el nombre ya está en la salida, el clip se saltea.`
    *   Item 2, new test: `test_adapt_keeps_extra_clips`: el origen trae los 5 del contrato más `A|Wave` y `A|Yes`; el resultado tiene los 5 más `wave` y `yes` y `check()` devuelve la lista vacía. (Without the collision fixture.)

### [M16] Verification command fails in PowerShell [`egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** 663-664
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Verified: `check_glb.py` uses `sys.argv` without glob expansion.
*   ***Proposed Edit:*** `` `python tools/check_glb.py web/assets/creatures/guardian.glb web/assets/creatures/bestia.glb web/assets/creatures/acechador.glb web/assets/creatures/soldado.glb` da 0 errores. ``

### [M17] Item 6 commits files that are already tracked [`egm-codebase-details`] - Severity: Medium
*   **Affected Scope:** A1 (164-165), item 6 (486-490)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Verified with `git ls-files`: all 4 are already in the repo.
*   ***Proposed Edit:*** Delete item 6 and renumber. A1 164-165: `Los originales ya están en assets_src/originals/ (CC0), así que el pipeline se puede reproducir.`

### [M18] The commit 3 check is stricter than the spec [`egm-implementation-readiness`] - Severity: Medium
*   **Affected Scope:** 599-600
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** `**Control del commit 3:** con el debug encendido (tecla D), y con el espejo encendido y apagado (tecla F), el roster no se pisa con el texto de estado del debug ni con #role. Los marcadores del debug y #errors pueden taparlo (ver Riesgos).`

### [N1] Wording [`egm-style`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX (only lines 404 and 431, and the hedge at 25-26) / DECLINE for the rest
*   ***Justification:*** 404 and 431 are rewritten anyway by M1/M2. The hedge is fixed by M9. The English section headings come from the EGM template, so changing them gains nothing.

### [N2] Undefined terms [`egm-comprehension`, `egm-style`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** In A2: `(la cápsula de reemplazo es la figura que se dibuja cuando falta el .glb)`. Line 336 / Future Improvements: `antes del freeze (bastante antes del 2026-11-26, fecha de la demo)`. Line 275: `las 8 piezas (4 tipos por lado)`.

### [N3] References that only make sense with the brief [`egm-comprehension`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The brief references are covered by B2. Line 276-277: `El roster no se borra, así que las piezas muertas siguen a la vista (tachadas).`

### [N4] Clutter [`egm-style`, `egm-zoom-out`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX (diagram and KB figures) / DECLINE (copied brief text)
*   ***Proposed Edit:*** Delete the diagram (291-301). A1 159-162: `El tamaño no es un riesgo: adapt ya copia el buffer binario entero, así que los datos de los 14 clips ya están en los .glb de hoy; conservarlos solo agrega entradas al JSON.`
*   ***Justification (decline):*** After M1-M12 the copied background shrinks by itself. Rewriting it adds little.

### [N5] Idle guard and `fight` lifecycle [`egm-design`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX (covered by M5 + M6)
*   ***Proposed Edit:*** A3, first bullet: add `` `death` limpia la pareja al terminar. ``

### [N6] Drift in other docs [`egm-design`, `egm-implementation-readiness`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** `dejarik_ar.md:91` says "los 5 clips". After commit 1 that is false.
*   ***Proposed Edit:*** Item 8 adds: `` *   `docs/designs/dejarik_ar.md:91`: "los 5 clips" pasa a "al menos los 5 clips del contrato". ``

### [N7] Small plan fixes [`egm-implementation-readiness`, `egm-codebase-details`] - Severity: Low
*   ***AI Suggestion:*** CONTEST (mirror key) / DECLINE (the rest)
*   ***Justification:*** The mirror key **is** F: `web/main.js:96`. The `LOOPING` / `jump_idle` issue goes away with M1 (`LOOPING = {idle, walk}`). The docstring, line-number, lint and regeneration-command issues are details the implementer sees when opening the file.

### [N8] Narrow the revert claim [`egm-implementation-readiness`] - Severity: Low
*   ***AI Suggestion:*** DECLINE
*   ***Justification:*** After M2, G7 only promises "cada commit se revierte solo". That is true for 3 independent commits.

### [N9] `BASIC` parses the URL again [`egm-implementation-readiness`] - Severity: Low
*   ***AI Suggestion:*** PROPOSE FIX (covered by M2, which deletes `BASIC`)
