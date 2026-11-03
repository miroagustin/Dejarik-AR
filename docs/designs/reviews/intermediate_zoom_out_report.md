# Stage 8: Intermediate Zoom Out Report

- **Target:** `docs/designs/dejarik_ar.md`, full file (lines 1–1299), after the Stage 7 fixes
- **Reviewer:** egm-zoom-out
- **Standard:** zoom-out-standard
- **Prior report:** `zoom_out_report.md` (Stage 5)
- **Goldfish context:** none
- **Result:** 0 Blockers, 4 new Majors, 4 new Nits

## Limitations

- There is still no code and no root README.md or context.md, so the reuse and Project Alignment checks are limited.
- Line 819 still says the repo holds only 3 files.

## Verdict

Two of the Stage 7 additions hold up:
- `frame_ack` is needed, because `cloudflared` buffers whatever the server sends.
- The mode-switch rule closes a real gap.

**Most of the Stage 7 fixes changed only the Technical Plan (TP).** The Detailed Implementation Plan (DIP), the tests and the Verification Plan were not updated, so the contract that freezes on day 2 now contradicts itself. The four new Majors come from that: the resolution pass did not carry its changes into the DIP. The remote mode has also grown further.

---

## New findings

### N1. 🟡 Major: `host_token` breaks CUJ 4 recovery, and the DIP and tests still use the old host rule
- **Lines:** 191, 239, 265–266, 498 vs 961, 1093, 1254
- **Problem:** A restart creates a new `host_token`. The old Chrome window reconnects with the old token, gets 4401, and `net.js` (line 1093) stops retrying with "Link inválido". In the DIP:
  - `__main__.py` (line 961) still opens `?p=0` with no token;
  - `test_transport` (line 1254) still tests the `Cf-Connecting-Ip` rule.
- **Why it matters:** If the Chrome window has to be replaced, the host must start the Teams share again, which puts the 30 s recovery target at risk. P4 will build whatever the DIP says, and the DIP has the old rule.
- **Fix:**
  - Save `host_token` in `save/` and reuse it on `--resume`.
  - Add `k=<host_token>` to line 961.
  - Change the test at line 1254 to "`p=0` with a wrong or missing `host_token` → 4401".

### N2. 🟡 Major: The replay change reached only the TP
- **Lines:** 506–507, 1052–1054 vs 528, 949, 1070, 1285
- **Problem:** Three places still describe full-session replay:
  - `fake_session.py` (line 949) still writes `state`/`events` into the `.dj`;
  - `transport.py` (line 1070) still records "cada mensaje";
  - Verification (line 1285) expects a full game with animations and no one playing, which a frames-only file cannot produce.
- **Why it matters:** `session_01.dj` is frozen on day 2, so two owners would build two different formats. The integration check at line 1285 cannot pass as written.
- **Fix:**
  - Change lines 949 and 1070 to frames only.
  - Rewrite line 1285 as "`--replay` runs a full game played with the mouse over the recorded frames".
  - See Stage 5 #5: with frames only, `cv2.VideoWriter`/`VideoCapture` fits even better than base64 JSONL.

### N3. 🟡 Major: `frame_ack` and the mode-switch rule are missing from the files that implement them
- **Lines:** 263, 291, 453–456 vs 1047–1048, 1064–1068, 1090–1097, 1150–1158, 1250–1256
- **Problem:** None of the implementing files mention the new behaviour:
  - `transport.py` has no 2-unacknowledged-frame window, no `frame_ack` handling, and no AI-task cancel on `P`;
  - `parse_client` does not list `frame_ack`;
  - `net.js` and `main.js` never send it;
  - `hello_msg` has no parameters for `tunnel`/`connected`;
  - none of it has a test.
- **Why it matters:** These mitigations protect the riskiest path. If they exist only in the TP, nobody will build them.
- **Fix:**
  - Add one bullet each to files 21, 23 and 27/34.
  - Add two `test_transport` cases:
    - the remote send pauses at 2 unacknowledged frames;
    - pressing `P` during the AI's think delay applies no AI tap.

### N4. 🟡 Major: The new Risks table contradicts the plan
- **Lines:** 732–733, 740 vs 475, 906, 1115–1123, 1175, 1272–1275, 843
- **Problem:** Four mitigations do not match what the plan builds:
  - **Clip-name map:** the TP (line 475), the asset contract (line 906) and `check_glb.py` (line 1175) still require exact clip names, and `creatures.js` has no map.
  - **Creature freeze:** the table says creatures freeze on day 12, but the calendar has real creatures on days 11–16 and the art freeze on day 18.
  - **Helper on `web/`:** the table says a Python member helps from day 3, but `hud.js`/`events.js` are owned by L alone, on days 6–10.
  - **AI weights:** the table says the weights live in `config.toml`, but `[ai]` (line 843) holds only the delays.
- **Why it matters:** These mitigations describe work that is not in the plan.
- **Fix:**
  - Adopt the clip-name map (Stage 5 #7): add it to `creatures.js`, drop exact names from the contract and from `check_glb.py`.
  - Name a Python co-owner for `hud.js`/`events.js` from day 3.
  - Line up the creature freeze date with the calendar.
  - Either add `[ai] weights` to `config.toml` or remove the claim from the table.

### N5. 🟢 Nit: Three different fallbacks for "not enough upload bandwidth"
- **Lines:** 717, 737, 777
- **Problem:** Alternative R is a day-12 fallback, the Risks table says `P` → `cpu`, and Future Improvements lists R or N.
- **Fix:** Keep `P` → `cpu`, which needs no code. Drop the contingency sentence from Alternative R and the line 777 entry.

### N6. 🟢 Nit: The demo script can't reach `remote` the way it describes
- **Lines:** 261, 503, 919
- **Problem:** `remote` is in the `P` cycle only when the program starts with `--mode remote`, and then `remote` is already the starting mode. The script's "arranque contra la PC → cambio a remoto" does not work as written.
- **Fix:** Either have the script start with `--mode remote` and press `P` to reach `cpu`, or add a separate `--tunnel` flag for opening the tunnel.

### N7. 🟢 Nit: The live-fallback chains disagree
- **Lines:** 98, 735
- **Problem:** G4 says `L` → `--single-marker`, while the Risks table says `L` → MP4.
- **Fix:** Use one chain. Dropping `--single-marker` (Stage 5 #4) solves it.

### N8. 🟢 Nit: Leftovers from the edits
- **Lines:** 957, 1281 vs 499–508; 425
- **Problem:** `--no-browser` is used in the DIP but is missing from the TP flag table. The animation lock now belongs to `transport`, but `phase:"animating"` is still a game phase.
- **Fix:** Add `--no-browser` to the flag table. Remove `animating` from `phase`, or say that `transport` sets it.

---

## Stage 5 findings status

| # | Finding | Status |
|---|---|---|
| 1 | Class techniques | ✅ Resolved by the Non-Goal at line 132 |
| 2 | Remote mode has no motivation and is the largest scope | 🔺 Open and **worse**: it gained the host token, `frame_ack`, 4409, mode rules, Alternatives R and S, and 3 Risks rows. `cpu` is now the opener (partial improvement). |
| 3 | Actions interface | ✅ Mostly resolved; the leftover is N8 |
| 4 | Fallback chain too long | ⏳ Open: `--single-marker` remains everywhere |
| 5 | Custom `.dj` format | ⏳ Open, partly improved (frames only). Still base64 JSONL, and it still skips vision. N2 follows from it. |
| 6 | Hand-written static server | ⏳ Open (lines 765, 1062) |
| 7 | Asset pipeline | ⏳ Open: file 35 still starts with AI generation, and the day-7 control is circular |
| 8 | Repeated numbers | 🔺 Open and **worse**: the AI weights claim is wrong (N4) |
| 9 | Protocol versioning | ⏳ Open |
| 10 | Hologram `ShaderMaterial` | ⏳ Open |
| 11 | Host role from a missing header | ✅ Resolved in the TP; the DIP and tests still need it (N1) |
| 12 | Goal order and duplicated test | ✅ Goal order resolved; ⏳ the duplicated G2 test is still open |
