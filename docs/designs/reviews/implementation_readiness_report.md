# Stage 9: Implementation Readiness Report (round 1)

- **Target:** `docs/designs/dejarik_ar.md`, DetailedRange (lines 782–1299). Lines 1–781 served as the contract.
- **Reviewers (all completed):**
  - egm-implementation-readiness, against implementation-readiness-standard;
  - egm-codebase-details, against the same standard;
  - egm-style, with no standard.
- **Goldfish context:** none. The repo has no code, so every file in the plan is new.
- **Raw findings:**
  - implementation readiness: 2 Blockers, 17 Majors, 9 Nits;
  - codebase details: 22 Majors, 6 Nits;
  - style: 10 Majors, 10 Nits.
- **After deduplication:** 2 Blockers, 28 Majors, 17 Nits.
- **Verdict:** **NOT READY.**
- **Round status:** not clean.

**Root cause of many findings:** the Stage 7 fixes changed the Technical Plan but not the file entries, tests and calendar below it (Stage 8, N1–N4). Blocker R2 and Majors R5, R6, R8 and R26 come from that. The rest of the Majors are decisions the plan leaves to the implementer, which the standard's Zero-Decision Rule forbids, or library API details that would fail on the first try.

Finding IDs: `IR-` implementation readiness, `CD-` codebase details, `ST-` style.

---

## 🔴 Blockers

### R1. The host's own browser is rejected at startup, and nobody owns the tokens
- **Lines:** 954–962, 1063, 834–845. Raised by IR-B1, CD-M10, CD-M11 and ST-M5; the token persistence part is Stage 8 N1.
- **Problem:**
  - `__main__.py` launches `--app=http://127.0.0.1:8000/?p=0` with no `host_token`, so the first launch gets a 4401.
  - It also drops the four Chrome flags from line 498.
  - No file generates the tokens or prints the remote link.
  - The doc says `chrome_path` is in the config, but `config.toml` has no such key.
  - A new `host_token` on every restart breaks the CUJ 4 auto-reconnect.
- **Fix:** In `__main__.py`:
  - generate `host_token` and `remote_token` with `secrets.token_urlsafe(16)`, and save `host_token` in `save/` so `--resume` reuses it;
  - pass both tokens to `transport`;
  - in `remote` mode print `{url}/?p=1&k={remote_token}`, and never print `host_token`;
  - launch Chrome with the full command from line 498.

  Also add `[browser] chrome_path` to `config.toml`.

### R2. The `.dj` format contradicts itself, and it freezes on day 2
- **Lines:** 943–949, 1050–1054, 1070, 1263, 1285. Raised by IR-B2, CD-M13, CD-M14 and ST-M6, plus Stage 8 N2.
- **Problem:** Four places disagree:
  - `recording.py` says frames only;
  - `fake_session.py` mixes in `state`/`events`;
  - `transport.py` records "cada mensaje";
  - Verification expects a full game with no one playing.

  Replay also publishes host messages that are already encoded, not the `frame_bus` packet shape, so `--replay --mode remote` has no 480p version and no scaled `K`.
- **Fix:** Use frames only, everywhere.
  - Line 949: write only frames.
  - Line 1070: record "cada mensaje binario `frame`".
  - Line 1285: "`--replay` muestra el video en loop con el tablero anclado y se juega una partida completa con mouse".
  - `recording.py` gets `read_dj(path) -> Iterator[(dt_ms, bytes)]`. `replay` decodes each record and publishes a packet with the same shape as `vision_loop`'s.

---

## 🟡 Majors

### Contract gaps (game and protocol)

**R3. Event schema undefined, and `turn` events are never acknowledged.** Lines 427, 1011–1021, 1125–1134. Raised by IR-M1.
- **Problem:** Nothing says which fields each event kind fills, or in what order events come. `events.js` has no handler for `turn`, so every turn stalls for the 5 s timeout.
- **Fix:**
  - Add a per-kind field table to `protocol.md`.
  - Fix the order: `attack` → `hit`? → `death`? → `win` | `turn`. A move is `move` → `turn`.
  - `turn` calls `anim_done` immediately.

**R4. The tap state machine contradicts the test.** Lines 813 vs 1236. Raised by IR-M2.
- **Problem:** The rules say an illegal tap deselects. The test says it changes nothing.
- **Fix:** Write the select/target/over state machine in item 20. Change the test to: an illegal tap in `target` deselects; in `select` it changes nothing.

**R5. `phase:"animating"` cannot come from a pure `game`, and the source of `legal` is not stated.** Lines 425, 1014. Raised by IR-M3, plus Stage 8 N8.
- **Fix:** `game` phases are `select|target|over`. `protocol.state_msg(state, animating)` sets the `animating` phase. `legal` = `legal_targets(state, selected)`.

**R6. `KINDS` is placed in a file that is not planned, and `game` has no way to reach the spec.** Lines 801 vs 1015. Raised by IR-M4, CD-M12 and ST-M2.
- **Fix:**
  - Line 801: `KINDS` lives in `dejarik/game.py`.
  - `game.py` loads `board.load_spec()` once into `_SPEC`.
  - Piece ids are 0–3 for player 0 and 4–7 for player 1, in table order.

**R7. `ai.py` is called "pure" but uses the game RNG; the weights have no config keys; the distance is ambiguous.** Lines 283–285, 740, 843, 1023–1029. Raised by IR-M13, CD-M12, plus Stage 8 N4.
- **Fix:**
  - Break ties deterministically on the lowest `(piece_id, cell)`, with no RNG.
  - Either add `[ai]` weight keys or change line 740 to say the weights are constants in `ai.py`.
  - Distance = BFS over `adjacency`, ignoring which cells are occupied.

**R8. `hello_msg` cannot express `tunnel`/`connected`, and nothing watches the tunnel.** Lines 434, 518, 1047. Raised by IR-M8 and CD-N5.
- **Fix:**
  - Signature `hello_msg(you, mode, remote=None)`, with `remote` sent to the host only.
  - Add `tunnel.alive()`, polled every 2 s.
  - Add "Túnel no disponible" to `hud.js`.

**R9. `debug` payload has no schema.** Lines 416, 1140–1148. Raised by IR-M16.
- **Fix:** Define `{"corners", "ids", "T_raw", "ms":{read,detect,pnp,filter,jpeg}, "pinch_ratio"}`.

**R10. CUJ 3's "cell under the finger is highlighted" is not implemented.** Line 182. Raised by IR-M17.
- **Fix:** `main.js` highlights `frame.hand.cell` with a hover style.

### Transport and server

**R11. `transport.py` is missing behaviours the contract requires.** Lines 1057–1070. Raised by IR-M5, CD-M6, CD-M7, plus Stage 8 N3.
- **Missing:**
  - the `frame_ack` window (at most 2 unacknowledged frames, accepted only from `p=1`, and listed in `parse_client`);
  - ignoring input while `pose.ok=false`;
  - cancelling the AI task on a mode change;
  - re-sending `hello` when `p=1` or the tunnel changes;
  - timeout semantics (the timer resets on each `anim_done`; when it expires, all pending ids are cleared);
  - a definition of the roles.
- **Fix:** Add each of these as a bullet in item 23. Use `serve(..., max_size=1024, compression=None)` instead of a custom size check; JPEG gains nothing from deflate.

**R12. A test checks the `Cf-Connecting-Ip` rule, which no longer exists.** Line 1254. Raised by IR-M6 and CD-M5.
- **Fix:** Replace the test with "`p=0` with a wrong or missing `host_token` → 4401".

**R13. Close codes 4401/4409 cannot be sent from `process_request`.** Lines 1063, 1093. Raised by CD-M4.
- **Problem:** Rejecting before the handshake gives the browser an HTTP error and close code 1006, so the client retries forever.
- **Fix:** `process_request` returns `None` for `/ws`. The handler validates the token with `secrets.compare_digest`, then calls `await connection.close(4401|4409)`.

**R14. The static file server is underspecified and its traversal guard is weak.** Line 1062. Raised by CD-M3, plus Stage 5 #6.
- **Problem:**
  - the code needs `websockets.http11.Response` with headers;
  - the query string has to be stripped;
  - the Windows registry maps `.js` to `text/plain`, which breaks ES modules;
  - a `..` substring check misses `%2e%2e`.
- **Fix:**
  - `mimetypes.add_type("text/javascript", ".js")` and `mimetypes.add_type("model/gltf-binary", ".glb")`.
  - Resolve the file with `(WEB_ROOT / unquote(urlsplit(path).path).lstrip("/")).resolve()` plus `is_relative_to(WEB_ROOT)`; anything else returns 404.
  - Map `/` to `index.html`.
  - Add a `%2e%2e` test.

**R15. Reading cloudflared's stderr will deadlock, and the 20 s timeout cannot work.** Lines 1032–1039. Raised by CD-M9.
- **Problem:** Nobody drains stderr after the URL is found, so the pipe fills and the tunnel stalls mid-demo. A blocking `readline` cannot honour a timeout.
- **Fix:** A daemon thread drains stderr for the life of the process, matches the URL and sets an `Event`; `start()` waits with `event.wait(20)`. Launch with `--no-autoupdate`.

**R16. The thread-to-asyncio handoff is unspecified.** Lines 987, 1002–1008, 1060. Raised by IR-M7 and CD-M8.
- **Fix:**
  - Packet = `{frame_id, bgr, host_msg, remote_msg|None, pose}`.
  - A `Flags` object holds the `threading.Event`s `remote_connected`, `debug_on` and `lock_toggle`.
  - Pinches go through `loop.call_soon_threadsafe(transport.on_host_tap, cell)`.
  - Send tasks are woken by `call_soon_threadsafe(event.set)`.
  - Hands writes to `hands_box`, and is off under `--replay`.

### Vision and dependencies

**R17. `requirements.txt` is not pinned, and the `websockets` version does not have the API the plan uses.** Lines 823–832. Raised by IR-M9, CD-M1, CD-M2 and ST-M4.
- **Problem:** `websockets.asyncio.server` needs version ≥ 13 (≥ 14 for it to be the default). mediapipe 0.10 needs `numpy<2`. Pillow is used by `make_board.py` but not listed.
- **Fix:** Pin exact versions (`websockets==15.0.1`, `numpy==1.26.4`, one exact OpenCV and mediapipe pair, `pillow`, `pytest`). On day 1, install into a clean venv, import everything, and commit the output of `pip freeze`.

**R18. `board_spec.json` has no values.** Lines 848–860. Raised by IR-M10.
- **Fix:** Fix the numbers that fit A3:
  - r0 = 0.035, r1 = 0.075, r2 = 0.115;
  - 12 markers of 0.025 m on radius 0.130;
  - IDs 0–11;
  - `sector_offset_deg` = 0;
  - define what `rotation_deg` means;
  - note that the `adjacency` keys are strings.

**R19. The single-marker fallback has no spec, and `min_markers=2` rejects it.** Lines 839, 988. Raised by IR-M11, plus Stage 5 #4.
- **Fix:** Either add `board_spec_single.json` (ID, size, offset) with `min_markers=1`, or drop `--single-marker` as Stage 5 recommended.

**R20. Pose metrics and filter parameters are undefined.** Lines 326, 839–840, 985. Raised by IR-M12, CD-M21, IR-N2 and ST-M8.
- **Fix:**
  - Use the `reprojectionError` that `solvePnPGeneric` returns (RMS) to choose between solutions, and recompute it with `projectPoints` after LM.
  - Continuity = the angle of `Rodrigues(R_prevᵀ R_i)`.
  - Lock is stable when Δt < 2 mm and Δrot < 0.5° throughout 2 s.
  - Separate One-Euro parameters for translation and rotation (`[filter.t]`, `[filter.r]`), with starting values.

**R21. MediaPipe VIDEO-mode details are missing.** Lines 1000–1004. Raised by CD-M20.
- **Problem:**
  - timestamps must strictly increase (skip a frame whose `frame_id` repeats);
  - input must be SRGB converted with `cvtColor`;
  - landmarks are normalised, so full-resolution pixels are `x*1280, y*720`. The wording at line 368 ("se escala de 640×360") should say so.
- **Fix:** Write these into item 19, and add the model URL to file 37.

### Browser (Three.js)

**R22. The Three.js vendor layout breaks relative imports, and the version is not pinned.** Lines 465, 1076. Raised by CD-M15.
- **Fix:**
  - Pin r169.
  - Mirror the upstream `build/` and `examples/jsm/` layout.
  - Use the import map `three` / `three/addons/`.
  - `import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js'`.

**R23. Projection and background rendering will fail silently.** Lines 1095, 1099–1109. Raised by IR-M15, CD-M16 and CD-M17.
- **Fix:**
  - Write the projection matrix formula into item 28.
  - `board.matrixWorldNeedsUpdate = true` after `fromArray`.
  - `createImageBitmap(blob, {imageOrientation:"flipY"})`; reuse one texture and `close()` the old bitmap.
  - Compute click NDC against the letterboxed content rect.

**R24. The hologram `ShaderMaterial` skinning setup is incomplete, and clones share materials.** Line 1113. Raised by CD-M18, plus Stage 5 #10.
- **Fix:** Either list the exact skinning and normal chunks, or (simpler) extend `MeshBasicMaterial` via `onBeforeCompile`. Give each clone its own material. Use `AdditiveBlending, transparent, depthWrite:false`.

**R25. The `play() -> Promise` contract with `AnimationMixer` is underspecified.** Line 1121. Raised by CD-M19.
- **Fix:** One-shot clips use `LoopOnce` + `clampWhenFinished` and resolve on the mixer's `finished` event, filtered by action. Run `reset().play()` before `crossFadeTo`. Looping clips resolve after the fade.

### Plan consistency and writing

**R26. The Risks table contradicts the plan.** Lines 732–740 vs 475, 906, 1115–1123, 1175, 1272–1275. Raised by Stage 8 N4 and IR-N7.
- **Problem:** The table promises a clip-name map (the plan enforces exact names), a creature freeze on day 12 (the calendar says day 18), and a Python helper on `web/` from day 3 (`hud.js`/`events.js` belong to L alone).
- **Fix:** Add the clip-name map to `creatures.js` and drop exact names from `check_glb`. Name the co-owner. Line up the dates.

**R27. Rules meant for `docs/rules.md` are incomplete.** Lines 784, 814–815. Raised by ST-M3 and IR-N1.
- **Problem:** Combat points back to the Technical Plan. The outcomes `hit|counter|tie` are undefined. The "no legal action" rule cannot happen in a legal state.
- **Fix:** Put the combat rule inline. Drop the impossible rule and its test, or note that the test uses an artificial fixture.

**R28. Tests and verification are not measurable or not complete.** Lines 1223–1224, 1238, 1244, 1247–1248, 1282, 1265–1270. Raised by ST-M7, ST-M8, ST-M9, IR-M14, IR-N6 and CD-N6, plus Stage 5 #12.
- **Problem:**
  - N is undefined in the One-Euro test;
  - "buena probabilidad" has no threshold;
  - G2 is not explained;
  - `ai`/`transport` are missing from the coverage list;
  - the duplicate G2 timing check is still there;
  - the 80% test has no fixed seeds;
  - the synthetic pose for the jitter test is undefined;
  - `fake_session` is scheduled for days 1–2, before the `protocol` code it imports (days 3–5).
- **Fix:**
  - Give the numbers: N = 10 samples at 30 Hz, `p_hit ≥ 0,5`, a pose at 0.6 m and 40° tilt, fixed seeds.
  - Add `ai`/`transport` to the coverage list.
  - Keep the G2 timing check in `test_ai` only.
  - Move `protocol.encode/decode_frame` to days 1–2.

**R29. "la IA" and "la PC" each mean two things.** Lines 900–914, 1023–1030, 1160–1166, 1244–1248, 1271–1276, 1293. Raised by ST-M1.
- **Fix:** Use "IA generativa" for the Blender pipeline and "rival automático" / `ai.py` for the opponent. Use "PC del anfitrión" for the hardware.

**R30. `rng_state` does not survive the JSON round trip.** Lines 1020, 1237. Raised by CD-M22 and IR-N3.
- **Problem:** `getstate()` returns tuples, JSON gives back lists, and `setstate` rejects lists.
- **Fix:** Convert lists ↔ tuples in `to_json`/`from_json`. State the seed used by `reset`.

---

## 🟢 Nits

| ID | Lines | Finding | Source |
|---|---|---|---|
| R31 | 982, 311 | Set `CAP_PROP_FOURCC` before width/height on DSHOW, and name the exposure/WB/focus properties | CD-N1 |
| R32 | 939 | "9×6" means inner corners; give the printed square size | CD-N2 |
| R33 | 1171–1177 | `check_glb` height ignores node TRS; give the Draco and skins checks | CD-N3 |
| R34 | 995 | rvec↔quat is a few lines of numpy | CD-N4 |
| R35 | 1062 | Give the MIME map, or use `mimetypes` (covered by R14) | IR-N4 |
| R36 | 1093, 445 | `net.js` handles 4401 but not 4409 | IR-N5 |
| R37 | — | The "encendido" boot animation and sound, and the player colours, have no owner in `web/` | IR-N8 |
| R38 | 388 | What `--input hand` does to host clicks is never stated | IR-N9 |
| R39 | 1283 | The lint rationale is an opinion | ST-M10 (downgraded) |
| R40 | 914 | "lo que peor le sale" is unsupported | ST-N1 |
| R41 | 832 | "se rompe `cv2`" is vague | ST-N2 |
| R42 | 823–1263 | English template labels; "Cambios" for new files | ST-N3 |
| R43 | 1168, 1181 | 35b and 35c are filed under the wrong section heading | ST-N4 |
| R44 | 1060, 1063 | "el paquete" is ambiguous; inconsistent `?p`/`k` notation | ST-N5, ST-N6 |
| R45 | 1064, 1067 | Values written in prose instead of naming the config keys | ST-N7 |
| R46 | 1138 | `hud.js` is one dense paragraph | ST-N8 |
| R47 | 1009, 1166, 1271, 1292 | Small wording fixes, and a reference to plan history | ST-N9, ST-N10 |

---

## Traceability Matrix

| Raw finding | → Consolidated |
|---|---|
| IR-B1 | R1 |
| IR-B2 | R2 |
| IR-M1 | R3 |
| IR-M2 | R4 |
| IR-M3 | R5 |
| IR-M4 | R6 |
| IR-M5 | R11 |
| IR-M6 | R12 |
| IR-M7 | R16 |
| IR-M8 | R8 |
| IR-M9 | R17 |
| IR-M10 | R18 |
| IR-M11 | R19 |
| IR-M12 | R20 |
| IR-M13 | R7 |
| IR-M14 | R28 |
| IR-M15 | R23 |
| IR-M16 | R9 |
| IR-M17 | R10 |
| IR-N1 | R27 |
| IR-N2 | R20 |
| IR-N3 | R30 |
| IR-N4 | R35 |
| IR-N5 | R36 |
| IR-N6 | R28 |
| IR-N7 | R26 |
| IR-N8 | R37 |
| IR-N9 | R38 |
| CD-M1 | R17 |
| CD-M2 | R17 |
| CD-M3 | R14 |
| CD-M4 | R13 |
| CD-M5 | R12 |
| CD-M6 | R11 |
| CD-M7 | R11 |
| CD-M8 | R16 |
| CD-M9 | R15 |
| CD-M10 | R1 |
| CD-M11 | R1 |
| CD-M12 | R6, R7 |
| CD-M13 | R2 |
| CD-M14 | R2 |
| CD-M15 | R22 |
| CD-M16 | R23 |
| CD-M17 | R23 |
| CD-M18 | R24 |
| CD-M19 | R25 |
| CD-M20 | R21 |
| CD-M21 | R20 |
| CD-M22 | R30 |
| CD-N1 | R31 |
| CD-N2 | R32 |
| CD-N3 | R33 |
| CD-N4 | R34 |
| CD-N5 | R8 |
| CD-N6 | R28 |
| ST-M1 | R29 |
| ST-M2 | R6 |
| ST-M3 | R27 |
| ST-M4 | R17 |
| ST-M5 | R1 |
| ST-M6 | R2 |
| ST-M7 | R28 |
| ST-M8 | R20, R28 |
| ST-M9 | R28 |
| ST-M10 | R39 |
| ST-N1 | R40 |
| ST-N2 | R41 |
| ST-N3 | R42 |
| ST-N4 | R43 |
| ST-N5 | R44 |
| ST-N6 | R44 |
| ST-N7 | R45 |
| ST-N8 | R46 |
| ST-N9 | R47 |
| ST-N10 | R47 |

**Cross-stage overlap:**
- Stage 8: N1 → R1, N2 → R2, N3 → R11, N4 → R26 and R7, N8 → R5.
- Stage 5: #4 → R19, #6 → R14, #10 → R24, #12 → R28.
