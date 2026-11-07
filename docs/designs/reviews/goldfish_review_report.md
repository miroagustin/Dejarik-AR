# Goldfish Annotated Review Report

Status: resolved. C1 was resolved with option (b), a Non-Goal. All PROPOSE FIX items are applied (51 edits). The optional turn cap was not applied. DECLINE items are recorded only.

**Target:** `docs/designs/dejarik_ar.md` (FeatureRange, lines 1–726)
**Source:** `critic_report.md` (Stage 7, round 1). Finding IDs C1–C20 and N1–N27 are the ones used in that report.

**Totals:** 1 ESCALATE, 19 PROPOSE FIX (Blocker/Major), 9 PROPOSE FIX (Nit), 18 DECLINE, 0 CONTEST.

Three fixes also touch the DetailedRange, so that both halves of the doc stay consistent. These are C3 (line 953), C12 (file 22) and C5/C18 (file 23). They are marked **[cross-range]**.

---

## ESCALATE: needs your input

### [Issue C1] [`egm-design`] - Severity: High
*   **Affected Scope:** [Lines 44, 106–112](../dejarik_ar.md#L44-L112) (The Problem, G5)
*   **Discrepancy Description:** The assignment lists 7 techniques. The design uses 4 of them; features, optical flow and segmentation are missing.
*   **Rationale:** The assignment is graded against this list. The G5 slide would have three empty rows.
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** The finding is valid either way. Which fix is right depends on a fact the reviewers could not read: did the professor say every technique must appear, or is a subset enough? Only you know that.
*   ***Proposed Edit (pick one):***
    *   **(a) If all techniques are required:** add this subsection to the Technical Plan, after "Mano y pinch":
        > ### Técnicas de clase → dónde se usan
        > | Técnica | Dónde |
        > |---|---|
        > | Calibración | `tools/calibrate.py` → `calib.npz` |
        > | ArUco | `vision`: detección del board |
        > | PnP | `vision`: `solvePnPGeneric` IPPE + LM |
        > | Homografía | `hands`: dedo → tablero |
        > | Flujo óptico | `vision`: si en un cuadro quedan < 2 marcadores, las esquinas del último cuadro bueno se siguen con `calcOpticalFlowPyrLK` hasta 0,5 s, en lugar de congelar la pose. |
        > | Segmentación | `hands`: máscara de la mano de MediaPipe, visible en el overlay de debug. |
        > | Features | overlay de debug: ORB entre el arte del tablero y el cuadro, mostrado como líneas de correspondencia. |

        Also change line 313 to: "…se siguen las esquinas con flujo óptico durante 0,5 s; después se manda `ok=false`."
    *   **(b) If a subset is enough:** add this Non-Goal:
        > **Usar todas las técnicas de clase.** El profesor confirmó el [fecha] que alcanza con calibración, ArUco, homografía y PnP. Features, flujo óptico y segmentación quedan fuera.

---

## PROPOSE FIX: Blockers and Majors

### [Issue C2] [`egm-structural`, `egm-design`] - Severity: High
*   **Affected Scope:** [Whole scope](../dejarik_ar.md#L524-L691)
*   **Discrepancy Description:** The doc has no Risks & Mitigations section. The leader as the only person who can do rendering, the asset clip names and CPU contention are never named as risks.
*   **Rationale:** The feature-spec standard requires a "Risks & Limits" section.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid. Most risks already have a mitigation somewhere in the doc, but nobody can see them in one place, and three risks have no mitigation at all.
*   ***Proposed Edit:*** Insert a new `## Risks & Mitigations` before `## Non-Functional Requirements` (line 689):
    > | Riesgo | Mitigación | Respaldo en vivo |
    > |---|---|---|
    > | El líder es el único que sabe Three.js y Blender; si se atrasa, no hay criaturas ni HUD. | Un integrante de Python trabaja con el líder en `web/` desde el día 3 (HUD y cola de eventos). Las criaturas se congelan el día 12. | Cubos con color por bando y las mismas animaciones de posición. |
    > | Los modelos descargados traen otros nombres y cantidad de clips. | Mapa de nombres por tipo de criatura en `web/`, en lugar de renombrar en Blender. | Usar `idle` para el clip que falte. |
    > | Teams, Chrome y MediaPipe compiten por la CPU del anfitrión. | Se mide el día 12 en la PC de la demo, con Teams compartiendo. Requisito: 4 núcleos y 8 GB. | `--input mouse` libera el hilo de MediaPipe. |
    > | Mala luz en la casa del anfitrión. | Exposición fija en `config.toml`, y una lámpara en el ensayo. | `L` (bloqueo de pose), y después el MP4. |
    > | El túnel no levanta o se cae. | `cloudflared` se prueba en cada ensayo. | `P` pasa a `cpu` o `local`. |
    > | La subida del anfitrión no alcanza para el remoto y Teams a la vez. | Se mide el día 12 (ver NFR). | `P` pasa a `cpu`. |
    > | Un compañero entra con el link y ocupa el lugar del jugador 1. | El link va por chat privado, y gana la primera conexión `p=1` (ver Modos). | `P` pasa a `local`. |
    > | La mano de MediaPipe no es precisa. | Se decide en el control 2 (Open Questions). | Mouse. |
    > | El rival automático no llega a ganar 1 de 5. | Los pesos están en `config.toml` y se ajustan después del primer ensayo. | Ninguno; no bloquea la demo. |

### [Issue C3] [`egm-design`, Stages 5 and 6] - Severity: Medium
*   **Affected Scope:** [Lines 163, 381–385](../dejarik_ar.md#L163-L385) (CUJ 2, Juego)
*   **Discrepancy Description:** The game actions are described three ways. CUJ 2 says a click on an illegal cell shows a warning, while the rules (line 758) say it deselects. Line 385 says input during animation is ignored, while the protocol has `denied:"animating"`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** `game.py` (line 963) already defines the simplest version, `tap`. Every other description should match it.
*   ***Proposed Edit:***
    *   Lines 381–383 → `*   Hay dos acciones: \`("tap", cell)\`, que resuelve seleccionar, mover, atacar o deseleccionar según el estado (ver Reglas definitivas), y \`("reset",)\`.`
    *   Line 385 → `*   Mientras haya eventos sin confirmar, \`transport\` no aplica la entrada y responde \`denied{reason:"animating"}\`.`
    *   Line 163 → `*   un clic en una casilla que no es legal deselecciona la pieza y no cambia el turno;`
    *   **[cross-range]** Line 953: change `("target_or_select", cell)` to `("tap", cell)`.

### [Issue C4] [`egm-design`] - Severity: Medium
*   **Affected Scope:** [Lines 199, 255, 708](../dejarik_ar.md#L199-L708)
*   **Discrepancy Description:** A classmate who clicks the link takes the remote seat away from the real player.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid. The fix needs no new key: first-connection-wins plus a private chat closes the gap.
*   ***Proposed Edit:***
    *   Line 255 → `*   Se acepta un solo \`p=1\` a la vez: gana el primero. Otro \`p=1\` se cierra con el código 4409 mientras el primero siga conectado.`
    *   Line 199 → `*   el anfitrión le pasó ese link al jugador 1 por chat privado de Teams (no el chat de la clase).`
    *   Line 708 → `…y el link solo se comparte por chat privado de Teams.`

### [Issue C5] [`egm-design`, Stage 5] - Severity: Medium
*   **Affected Scope:** [Lines 253, 709](../dejarik_ar.md#L253-L709)
*   **Discrepancy Description:** The host role depends on the absence of the `Cf-Connecting-Ip` header.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A second token uses the same mechanism as `p=1`. With it, one rule decides every role, and the code gets no longer.
*   ***Proposed Edit:***
    *   Line 253 → `*   \`?p=0&k=<host_token>\`: anfitrión. \`host_token\` es otro token al azar que se genera al arrancar y solo va en la URL \`--app\` de Chrome; nunca se imprime ni pasa por el túnel.`
    *   Line 254: add "Lo mismo vale para `p=0`" after "cierra la conexión con el código 4401".
    *   Line 231 → `ws://127.0.0.1:8000/ws?p=0&k=<host_token>`. Line 477 → `--app=http://127.0.0.1:8000/?p=0&k=<host_token>`.
    *   Line 709 → `*   el rol de anfitrión exige \`host_token\`, que no sale de la PC; sin él no se puede usar \`reset\`, \`lock\` ni \`mode\`.`
    *   **[cross-range]** File 23 (line 1008): "decide el rol según `?p` y `k`" (drop the header).

### [Issue C6] [`egm-design`, `egm-style`] - Severity: Medium
*   **Affected Scope:** [Lines 279, 283, 651, 699](../dejarik_ar.md#L279-L699)
*   **Discrepancy Description:** `cloudflared` buffers whatever the server sends, so `send` never blocks and delay piles up. The units are mixed, and the 5 Mbps budget is smaller than the remote video plus Teams.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid. The "drop instead of delay" claim only holds against a slow local socket, and the tunnel's socket is not slow.
*   ***Proposed Edit:***
    *   Line 279: append `Para el remoto esto no alcanza, porque \`cloudflared\` acepta todo y acumula en el túnel. Por eso el remoto confirma cada cuadro con \`{"type":"frame_ack","frame_id"}\`, y su tarea de envío no manda uno nuevo mientras haya 2 sin confirmar.`
    *   Line 283 → `máximo 15 fps, unos 3–5 Mbps de subida para el anfitrión;`
    *   Line 434: add `{"v":1,"type":"frame_ack","frame_id":int}` (remote only).
    *   Line 651 → `Pocos kbps en lugar de 3–5 Mbps.`
    *   Line 699 → `subida del anfitrión ≥ 8 Mbps (3–5 Mbps del video remoto más 2–3 Mbps de Teams);`

### [Issue C7] [`egm-design`] - Severity: Medium
*   **Affected Scope:** [Lines 202, 699–701](../dejarik_ar.md#L202-L701)
*   **Discrepancy Description:** The remote player downloads the GLBs and audio through the host's upload during the demo.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add to the "Modo remoto" NFR:
    > *   todo `web/` (Three.js, criaturas, sonidos) pesa ≤ 10 MB, y se mide el día 12;
    > *   el jugador remoto entra antes de empezar la demo, así la descarga no compite con Teams en vivo.

### [Issue C8] [`egm-design`, Stage 6] - Severity: Medium
*   **Affected Scope:** [Line 183](../dejarik_ar.md#L183) (CUJ 4)
*   **Discrepancy Description:** After a restart there is a new token and a new tunnel URL, so the remote player cannot reconnect on their own.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This uses the cheaper of the two options. Keeping `cloudflared` alive across restarts would mean managing a process outside Python.
*   ***Proposed Edit:*** Line 183 → `*   si Python se reinició, la partida retoma el último estado guardado y el navegador del anfitrión se reconecta solo. En modo \`remote\` hay un link nuevo: el anfitrión lo copia del HUD y se lo pasa al jugador 1, que vuelve en menos de 30 s;`

### [Issue C9] [`egm-design`, Stage 6] - Severity: Medium
*   **Affected Scope:** [Lines 34, 251, 274–275, 493](../dejarik_ar.md#L34-L493)
*   **Discrepancy Description:** `P` into `remote` without a tunnel is undefined. So is what happens to `p=1` when the mode leaves `remote`, and whether queued bot moves are cancelled.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** After line 251, add:
    > *   **Cambio de modo con `P`.**
    >     *   El ciclo es `cpu → local → remote → cpu`. `remote` solo entra en el ciclo si el programa arrancó con `--mode remote`, porque el túnel se abre solo al arrancar.
    >     *   Al salir de `remote`, la conexión `p=1` sigue conectada y mirando, pero `can_act` le da `false`.
    >     *   Cualquier cambio de modo cancela la jugada pendiente del rival automático (una sola tarea `asyncio`, que se cancela).

    Also change lines 34 and 493 to the same cycle.

### [Issue C10] [`egm-design`] - Severity: Medium
*   **Affected Scope:** [Line 477](../dejarik_ar.md#L477)
*   **Discrepancy Description:** Windows pauses a covered Chrome window, so `anim_done` stops arriving and the game stalls. The autoplay policy mutes the startup sound (N6).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Line 477: append `Chrome se lanza además con \`--disable-features=CalculateNativeWinOcclusion --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --autoplay-policy=no-user-gesture-required\`, para que no se pause cuando Teams tapa la ventana y para que suene el audio de arranque. En el ensayo se prueba tapar la ventana con Teams.`

### [Issue C11] [`egm-design`, `egm-style`] - Severity: Medium
*   **Affected Scope:** [Lines 519–520](../dejarik_ar.md#L519-L520)
*   **Discrepancy Description:** The doc states that the threads are fast enough as a fact, with no measurement behind it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Replace lines 519–520 with:
    > *   MediaPipe (15–30 ms) corre en su propio hilo. Se espera que el GIL se libere dentro de OpenCV y MediaPipe, así que dos hilos deberían alcanzar.
    > *   Se verifica el día 12 en la PC de la demo: fps de pose con y sin el hilo de manos. Si con la mano la pose baja de 30 fps, `hands` pasa a un `multiprocessing.Process`.

### [Issue C12] [`egm-design`, Stage 5] - Severity: Medium
*   **Affected Scope:** [Lines 485–486, 507](../dejarik_ar.md#L485-L507)
*   **Discrepancy Description:** `--replay` re-sends the recorded `state` and `events`, so it would fight a live `game`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Recording only the cuadros keeps the format small. It also lets the fixture do what line 507 says it is for.
*   ***Proposed Edit:***
    *   Line 485 → `| \`--replay archivo.dj\` | En lugar de la cámara, reproduce los cuadros grabados (JPEG + pose) en loop. \`game\` corre en vivo y se juega con mouse. |`
    *   Line 486 → `| \`--record archivo.dj\` | Graba los cuadros que salen hacia el anfitrión (JPEG + pose), no el estado. |`
    *   **[cross-range]** File 22: `replay` only writes to the `frame_bus`.

### [Issue C13] [`egm-design`, Stage 6] - Severity: Medium
*   **Affected Scope:** [Line 26](../dejarik_ar.md#L26) (Cómo se juega)
*   **Discrepancy Description:** The FeatureRange uses `bestia`, HP, ATK, DEF and the win condition without ever defining them.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid. This is a gap a human reader would hit, not only a zero-context reviewer. The proposed turn cap is a game-design decision, so it is listed separately; you can reject it.
*   ***Proposed Edit:*** After line 26's table (after line 32), add:
    > **Reglas en una línea.** Cada bando tiene un `guardian`, una `bestia`, un `acechador` y un `soldado`, con ATK, DEF, HP y MOV distintos. En su turno cada jugador mueve una pieza o ataca a una rival adyacente; el combate es 1d6 + ATK contra 1d6 + DEF. Gana quien elimina las 4 piezas rivales. Detalle en "Reglas definitivas".
    *   *(Optional, your decision)* Add to the rules (line 760): `Si en 80 turnos nadie gana, gana quien tenga más HP total.`

### [Issue C14] [`egm-design`, Stage 5] - Severity: Medium
*   **Affected Scope:** [After line 687](../dejarik_ar.md#L687) (Alternatives)
*   **Discrepancy Description:** Two cheaper remote designs are not considered: a 2D board that relies on the Teams share for the AR view, and WebRTC.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Add:
    > ### Alternativa R: El remoto ve la RA por Teams y su página es solo un mapa 2D para hacer clic
    > *   **Pros:** sin video por el túnel (pocos kbps), sin descargar criaturas, sin `K` escalado.
    > *   **Cons:** el remoto ve la RA con 1–2 s de demora de Teams, así que su clic va sobre una imagen vieja; mira dos ventanas a la vez.
    > *   **Motivo del rechazo:** la demora de Teams rompe la meta de < 500 ms de G7. Queda como respaldo si la medición del día 12 no alcanza (reemplaza a la mejora futura "Vista virtual").
    >
    > ### Alternativa S: Video al remoto por WebRTC (`aiortc`, H.264)
    > *   **Pros:** 3 a 5 veces menos ancho de banda que JPEG; control de congestión incluido.
    > *   **Cons:** señalización, ICE/TURN detrás del túnel y una dependencia nativa pesada.
    > *   **Motivo del rechazo:** con `frame_ack` y 480p, JPEG por WebSocket entra en la subida medida y es mucho menos código.

    Change line 722 to point at Alternativa R.

### [Issue C15] [`egm-structural`, `egm-style`, `egm-design`] - Severity: Medium
*   **Affected Scope:** [Lines 124, 536–666](../dejarik_ar.md#L124-L666)
*   **Discrepancy Description:** Every alternative is rejected with "Rechazada por el autor", and the J, K, H, I and line 124 rationales are circular once the label is removed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Delete "Rechazada por el autor. " and "Rechazado por el autor: " everywhere (16 places).
    *   Line 124 → `…y SLAM.** Duplicaría la visión y la calibración, y obligaría a sincronizar el estado entre dos PCs por internet; no entra en 24 días.`
    *   Line 605 (H) → `Con pocos píxeles por marcador la pose salta entre las dos soluciones del plano; el board de 12 marcadores evita eso y sigue anclado con la mitad tapada (G1). Se mantiene solo como respaldo (\`--single-marker\`).`
    *   Line 613 (I) → `La mayoría de las criaturas no son bípedas, así que el auto-rig no sirve; se usan modelos que ya vienen animados (Quaternius CC0, Sketchfab).`
    *   Lines 620–621 (J) → Cons: `Hay que ajustar unos 6 parámetros de ruido contra 2 de One-Euro.` Motivo: `One-Euro se valida contra el temblor de G1 (< 1 mm y 1°); si no lo cumple, se revisa.`
    *   Line 630 (K) → `Con pocos marcadores elige la pose espejada y no se recupera; IPPE devuelve las dos soluciones y permite elegir.`

### [Issue C16] [`egm-structural`, `egm-style`, `egm-design`] - Severity: Medium
*   **Affected Scope:** [Lines 94–119](../dejarik_ar.md#L94-L119)
*   **Discrepancy Description:** The goals appear in the order G1–G4, G7, G5, G6.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Moving the G7 block (lines 94–105) to after G6 keeps every ID, so nothing elsewhere in the doc needs to change.
*   ***Proposed Edit:*** Move lines 94–105 to after line 119.

### [Issue C17] [`egm-structural`, `egm-style`] - Severity: Medium
*   **Affected Scope:** [Line 197](../dejarik_ar.md#L197)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Line 197 → `*   el anfitrión arrancó con \`--mode remote\`;`

### [Issue C18] [`egm-structural`] - Severity: Medium
*   **Affected Scope:** [Lines 420–427](../dejarik_ar.md#L420-L427)
*   **Discrepancy Description:** No message carries the tunnel state or whether the remote player is connected. `denied` sits under the wrong subheading, and code 4401 is not listed in the protocol.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Replace lines 420–427 with:
    > **De Python al navegador, al conectar y cuando cambia el modo o el estado del remoto (texto JSON):**
    > ```text
    > {"v":1,"type":"hello","you":0|1,"mode":"cpu"|"local"|"remote",
    >  "remote":{"url":str|null,"tunnel":"up"|"down"|"off","connected":bool}}
    > ```
    > *   `remote` solo se le manda al anfitrión, que lo ve en su HUD.
    >
    > **De Python al navegador, en respuesta a una entrada rechazada (texto JSON):**
    > ```text
    > {"v":1,"type":"denied","reason":"not_your_turn"|"animating"}
    > ```
    > *   Códigos de cierre del WebSocket: 4401 token inválido, 4409 ya hay un jugador 1.

### [Issue C19] [`egm-style`, `egm-design`, Stages 5 and 6] - Severity: Medium
*   **Affected Scope:** [Line 93](../dejarik_ar.md#L93)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Line 93 → `*   Cada falla prevista tiene un respaldo ensayado (detalle en Risks & Mitigations):` followed by sub-bullets:
    > *   mano no responde → mouse (`--input mouse`);
    > *   remoto se cae → `local` o `cpu` (`P`);
    > *   tracking inestable → bloqueo de pose (`L`), y después `--single-marker`;
    > *   cámara muerta → `--replay`;
    > *   Python no arranca → MP4.

### [Issue C20] [`egm-style`] - Severity: Medium
*   **Affected Scope:** [Lines 89–90](../dejarik_ar.md#L89-L90)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:***
    *   Line 89 → `*   **G3 — Combate animado.** Las criaturas tienen look de holograma y los 5 clips (\`idle\`, \`walk\`, \`attack\`, \`hit\`, \`die\`), con sonido. Cada combate es una secuencia de acercarse, golpear, impacto y caída que dura entre 2 y 5 s.`
    *   Line 90 → `*   **G4 — Demo con respaldos ensayados.**`

---

## PROPOSE FIX: Nits worth fixing

| ID | Edit |
|---|---|
| N1 | Lines 180 and 189: "un integrante" → "el anfitrión". |
| N2 | Line 556: "sin ninguna ventaja frente a Three.js" → "sin una ventaja que compense el costo". |
| N3 | Lines 356–357 (correctness): `cv2.undistortPoints(pt, K, dist, P=K)`, after scaling the 640×360 landmark to 1280×720. Then `H = K·[r1 r2 t]` is right. |
| N4 | Line 388: append "Se escribe en un archivo temporal y se reemplaza con `os.replace`, para que un corte no lo deje a medias." |
| N6 | Covered by C10. |
| N10 | Line 465: append "Mientras dure, Python ignora los clics y los pinch." |
| N12 | Line 717: `### Future Improvements` → `## Future Improvements`. |
| N26 | Line 221: "hay tres procesos" → "hay dos procesos, tres en modo `remote`". Line 223: "Tiene todo lo que piensa:" → "Concentra la lógica:". |
| N27 | Line 253 is rewritten by C5. Line 472: "aplana" → "puede aplanar". |

## DECLINE: Nits recorded, not fixed

N5 (`debug` per connection), N7 (Teams audio is a rehearsal check), N8 (single-marker placement, which belongs in the DetailedRange), N9 (MJPG passthrough optimisation), N11 (version pinning needs the actual vendored release), N13 (NFR placement), N14–N16 (layout), N17–N18, N20–N25 (wording), N19 ("cruz central": the G1 metric needs the board artwork to be decided first; Stage 9 should check `make_board.py`).
