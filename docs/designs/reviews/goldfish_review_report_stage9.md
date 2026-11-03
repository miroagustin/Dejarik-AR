# Goldfish Annotated Review Report: Stage 9

Status: resolved. All PROPOSE FIX items were applied in 65 edits, including R19 (`--single-marker` removed) and R26 (Risks table aligned with the plan). DECLINE items are recorded only.

**Target:** `docs/designs/dejarik_ar.md`, DetailedRange (lines 782–1299)
**Source:** `implementation_readiness_report.md`. Finding IDs R1–R47 are the ones used in that report. Stage 8 N5–N7 are included too, because they sit in the DetailedRange.
**Stage 7 report:** kept unchanged in `goldfish_review_report.md`.

**Totals:**

| Category | Count |
|---|---|
| ESCALATE | 0 |
| PROPOSE FIX (Blocker/Major) | 30 |
| PROPOSE FIX (Nit) | 8 |
| DECLINE | 11 |
| CONTEST | 0 |

**Two fixes are design decisions, not just text repairs. Check them before you accept:**
- **R19:** remove the `--single-marker` fallback instead of specifying it. Stages 5 and 8 also recommended removing it.
- **R26:** align the Risks table with the plan, instead of adding new work to the plan to match the table.

Five fixes also change lines 1–781 so both halves stay consistent. They are marked **[TP]**: R7 (line 285), R14 (line 765), R19 (G4, flags, Alternative H), R26 (Risks table) and R21 (line 368).

---

## 🔴 Blockers

### [R1] Host browser rejected; tokens have no owner. PROPOSE FIX
*   **Scope:** [954–962](docs/designs/dejarik_ar.md#L954-L962), [834–845](docs/designs/dejarik_ar.md#L834-L845)
*   **Edit:** In item 14, replace the `tunnel.start()` and Chrome bullets with:
    > *   genera `host_token` y `remote_token` con `secrets.token_urlsafe(16)`. `host_token` se guarda en `save/host_token` y `--resume` lo reutiliza, para que la ventana de Chrome ya abierta se reconecte sola;
    > *   en modo `remote` llama a `tunnel.start()` e imprime `<url>/?p=1&k=<remote_token>`. `host_token` nunca se imprime;
    > *   abre Chrome (`[browser] chrome_path`) con `--app=http://127.0.0.1:8000/?p=0&k=<host_token>` y los flags del Technical Plan (`--disable-features=CalculateNativeWinOcclusion --disable-renderer-backgrounding --disable-backgrounding-occluded-windows --autoplay-policy=no-user-gesture-required`). Con `--resume`, si la ventana ya existe, no abre otra;
    > *   pasa los dos tokens a `transport.serve(...)`;
*   Add `[browser]: chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"` to `config.toml`.

### [R2] The `.dj` format contradicts itself. PROPOSE FIX (frames only)
*   **Scope:** 949, 1052–1054, 1070, 1263, 1285
*   **Edit:**
    *   Line 949 → `*   no genera \`state\` ni \`events\`: el \`.dj\` solo tiene cuadros.`
    *   Item 22:
        *   add `read_dj(path) -> Iterator[(dt_ms, bytes)]`;
        *   change `replay` to: "decodifica cada cuadro con `decode_frame` y publica en el `frame_bus` un paquete con la misma forma que `vision_loop` (JPEG de 720p, pose del header y, si hay remoto, el de 480p recodificado)".
    *   Line 1070 → `*   si se pidió \`--record\`, graba cada mensaje binario \`frame\` que sale hacia el anfitrión.`
    *   Line 1285 → `*   **Integración:** \`python -m dejarik --replay fixtures/session_01.dj\` muestra el video en loop con el tablero anclado, y se juega una partida completa con mouse.`
    *   Line 1263 → `*   \`read_dj\` sobre un \`.dj\` recién grabado devuelve los mismos bytes.`

---

## 🟡 Majors

| ID | Edit (summary; exact text applied on accept) |
|---|---|
| R3 | Item 7 adds an event table and a fixed order: `move{piece,from,to}`, `attack{piece,to,result{atk_roll,def_roll,outcome}}`, `hit{piece,result{hp}}`, `death{piece,from}`, `turn{result{turn}}`, `win{result{winner}}`. The order is `attack` → `hit` (if not a tie) → `death` (if hp 0) → `win` or `turn`; a move is `move` → `turn`. Item 31 adds `turn`, which updates the HUD and sends `anim_done` immediately. |
| R4 | Item 20 adds the `tap` state machine (see R5 for the phases). Line 1236 → "`tap` en una casilla ilegal: en fase `target` solo deselecciona; en fase `select` no cambia nada". |
| R5 | Item 20: `State.phase ∈ {select, target, over}`. Item 21: `state_msg(state, animating)` sends `phase:"animating"` while `transport` has events waiting for `anim_done`; `legal` is the result of `legal_targets(state, selected)`, or `[]`. |
| R6 | Line 801: `rules.py` → `dejarik/game.py`. Item 20: `game.py` loads `board.load_spec()` once; piece ids are 0–3 for player 0 and 4–7 for player 1, in table order. |
| R7 | Item 20b: `choose(state)` breaks ties by the lowest `(piece_id, cell)`, with no RNG. It is pure and repeatable. The weights are constants at the top of `ai.py`. Distance is BFS over `adjacency`, ignoring which cells are occupied. **[TP]** Line 285: replace "con el RNG de la partida" with "por el menor `(piece_id, casilla)`". Risks row: "constantes en `ai.py`". |
| R8 | Item 21: `hello_msg(you, mode, remote=None)`, where `remote` (`url`, `tunnel`, `connected`) goes to the host only. Item 20c adds `alive() -> bool`; `transport` polls it every 2 s and sends `hello` to the host when it changes. Item 32 adds "Túnel no disponible". |
| R9 | Item 7 defines `debug = {"corners":[[[u,v]×4]], "ids":[int], "T_raw":[16], "ms":{"read","detect","pnp","filter","jpeg"}, "pinch_ratio":float|null}`. |
| R10 | Item 34: `frame.hand.cell` is highlighted with a hover style (CUJ 3). |
| R11 | Item 23 adds: a `frame_ack` window of at most 2 unacknowledged frames, accepted only from `p=1` and listed in `parse_client`; clicks and pinches are ignored while `pose.ok=false`; any mode change cancels the AI task; `hello` goes to the host when `p=1` or the tunnel changes; the 5 s timer restarts on each `anim_done` or new batch, and when it expires it clears every pending id; `serve(..., max_size=1024, compression=None)`. Roles are `{host, remote}`. Line 1253: "3 modos × 2 roles × 2 turnos". |
| R12 | Line 1254 → "`p=0` sin `host_token` o con uno equivocado se cierra con 4401; `p=1` con un token equivocado, con 4401; un segundo `p=1`, con 4409". |
| R13 | Item 23: `process_request` returns `None` for `/ws`. The handler checks `p`/`k` with `secrets.compare_digest`, then `await connection.close(4401 \| 4409)`. Item 27: 4409 shows "Ya hay un jugador 1" and does not retry. |
| R14 | Item 23: at import, `mimetypes.add_type("text/javascript", ".js")` and `mimetypes.add_type("model/gltf-binary", ".glb")`. The path is `(WEB / unquote(urlsplit(path).path).lstrip("/")).resolve()`; anything not `is_relative_to(WEB)` and an existing file returns 404. `/` serves `index.html`. The response is `websockets.http11.Response` with `Content-Type`. Line 1255 adds a `/%2e%2e/` case. **[TP]** Line 765: "solo sirve archivos que, ya resueltos, quedan dentro de `web/`". |
| R15 | Item 20c: a daemon thread reads stderr for the life of the process, finds the URL, sets an `Event`, and writes everything to `recordings/cloudflared.log`. `start()` waits with `event.wait(20)`. cloudflared is launched with `--no-autoupdate`. |
| R16 | New paragraph after item 23, "Hilos y datos compartidos": the packet is `{frame_id, t, bgr, host_msg, remote_msg\|None, pose}`; `Flags` holds the `threading.Event`s `remote_connected`, `debug_on` and `lock_toggle`; hands writes to `hands_box`; a pinch goes through `loop.call_soon_threadsafe(transport.on_host_tap, cell)` and gets the same checks as a click; send tasks wake via `call_soon_threadsafe(event.set)`; there is no hands thread under `--replay`. Lines 987 and 1002/1007 point to this paragraph. |
| R17 | Item 1: exact pins (`==`). Starting set: `opencv-contrib-python==4.10.0.84`, `mediapipe==0.10.14`, `numpy==1.26.4`, `websockets==15.0.1`, `pillow==10.4.0`, `pytest==8.3.3`. On day 1, install them in a clean venv and check that `cv2.aruco` and `mediapipe.tasks` import. If one fails, change that pin and record it. `websockets` must be ≥ 14 for `websockets.asyncio.server`. |
| R18 | Item 3 sets initial values that fit A3 with margins: `r0=0.035`, `r1=0.072`, `r2=0.110`; 12 markers of `0.022` m on radius `0.125`, at the centre of each sector; IDs 0–11 (sector k → ID k−1); `sector_offset_deg=0`; `rotation_deg` is the angle of the marker's top edge, counter-clockwise from +X, with the top edge facing outward. `adjacency` keys are strings. |
| R19 | **Decision:** remove `--single-marker`. Remove it from G4, the flag table, Alternative H, item 11, item 14 and item 17. Alternative H's rationale becomes: "No se usa ni como respaldo: el board ya tolera la mitad de marcadores tapados y `L` cubre el resto". This also fixes Stage 8 N7. |
| R20 | Item 17: choose the solution by the `reprojectionError` (RMS) that `solvePnPGeneric` returns; after LM, recompute it with `projectPoints`; continuity is the angle of `Rodrigues(R_prevᵀ·R_i)`. `[pose]` adds `lock_max_dt_mm = 2` and `lock_max_drot_deg = 0.5`. `[filter]` becomes `[filter.t]` (1.0 / 0.5 / 1.0) and `[filter.r]` (1.0 / 0.05 / 1.0). Line 1223: "menos de 10 muestras a 30 Hz". |
| R21 | Item 19: skip a frame whose `frame_id` repeats; `timestamp_ms = t` of the frame; `mp.Image(SRGB, cvtColor(BGR2RGB))`; landmarks are normalised, so pixels are `x·1280, y·720`. Item 37 adds the official URL. **[TP]** Line 368: "se pasa a píxeles de 1280×720 (MediaPipe da coordenadas normalizadas)". |
| R22 | Item 24: Three.js r169, with the upstream layout `build/three.module.js` and `examples/jsm/{loaders,utils}/`. Import map: `three` and `three/addons/`. **[TP]** Line 465: "r16x" → "r169". |
| R23 | Item 28: the projection formula; `board.matrixWorldNeedsUpdate = true` after each pose; the background uses `createImageBitmap(blob, {imageOrientation:"flipY"})` on a single reused texture, and `close()`s the previous bitmap; the click is computed against the letterboxed content rect. |
| R24 | Item 29: `MeshBasicMaterial` with `onBeforeCompile` (which brings skinning) instead of a full `ShaderMaterial`. `transparent`, `AdditiveBlending`, `depthWrite:false`. Item 30: each clone gets its own material. **[TP]** Line 476 to match. |
| R25 | Item 30: one-shot clips use `LoopOnce` + `clampWhenFinished` and resolve on the mixer's `finished` event for that action; `reset().play()` before `crossFadeTo`; loops resolve after the fade. |
| R26 | **[TP]** Risks table, aligned with the plan: clips → "se renombran al importar en Blender y `check_glb.py` lo verifica"; leader → "P4 opera la generación de criaturas (archivo 35), así el líder solo hace `web/`", with no day-3 helper and no day-12 freeze; AI → "constantes en `ai.py`". |
| R27 | Line 814: the combat rule written inline (1d6+ATK against 1d6+DEF; higher → defender −1 HP `hit`; lower → attacker −1 HP `counter`; tie → nothing). Delete "Si un jugador no tiene ninguna acción legal, pasa el turno" and the test at line 1235: with 4 pieces it cannot happen. |
| R28 | Line 1244: "`p_hit ≥ 0,5`". Line 1238: drop the G2 timing (it stays in `test_ai`). Lines 1238 and 1247: "G2 (partida de 6 a 8 minutos)". Line 1248: seeds 0–199. Line 1215: synthetic pose at 0.6 m with 40° tilt. Line 1282: add `ai` and `transport`. Calendar: `protocol.encode_frame/decode_frame` move to days 1–2 (P4). |
| R29 | Lines 1244–1248 and 1293: "la IA" / "la PC" (the opponent) → "el rival automático". Line 1276: "desde la PC apagada" → "con la PC del anfitrión apagada". "IA" is now used only for Blender. |
| R30 | Item 20: `to_json` turns `rng_state` into lists and `from_json` turns it back into tuples. `reset` uses `seed + 1`. |

## 🟢 Nits: PROPOSE FIX

| ID | Edit |
|---|---|
| R31 | Item 17 `open_camera`: set `CAP_PROP_FOURCC` before width and height, then `CAP_PROP_AUTOFOCUS/FOCUS/AUTO_EXPOSURE/EXPOSURE/AUTO_WB/WB_TEMPERATURE`. |
| R36 | Covered by R13. |
| R37 | Item 31: on the first `pose.ok` it plays the "encendido" animation and `boot`. Item 32: player 0 is blue, player 1 is red. |
| R38 | Item 14: `--input hand` ignores the host's clicks; `mouse` turns off the hands thread. |
| R39 | Line 1283 → "Lint: no se exige; el tiempo va a tests y ensayos." |
| R41 | Line 832: "los dos paquetes instalan el módulo `cv2` y uno pisa al otro, y se pierde `aruco`". |
| R47 | Line 1292: "recibe cierre 4401 y ningún cuadro". Line 1271: "se usan modelos ya animados (fuente 1 de `docs/assets_checklist.md`)". |
| S8-N6 | Line 919: "arranque con `--mode remote` y `P` hasta `cpu` → partida contra la PC → `P` dos veces para volver a `remote` con un integrante desde su casa → …". |

## DECLINE (recorded, not fixed)

R32 (chessboard square size), R33 (`check_glb` TRS), R34 (rvec↔quat in numpy), R35 (covered by R14), R40, R42, R43, R44, R45, R46 (wording and layout), S8-N5 (three fallbacks for bandwidth).
