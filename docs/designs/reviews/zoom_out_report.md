# Stage 5: Initial Zoom Out Report

- **Target:** `docs/designs/dejarik_ar.md`, full file (lines 1–1244)
- **Reviewer:** egm-zoom-out
- **Standard:** zoom-out-standard
- **Goldfish context:** none (the doc has no markdown links)

## Limitations

- The "Project Alignment" check could not be done. The repo has no root README.md or context.md, and the brief PDF was not supplied as context.
- The codebase-reuse search came back empty because there is no code yet. Reuse suggestions point to platform features and libraries instead.
- Line 764 says the repo holds only the brief PDF, `concepts_brief.md` and this document. `design_draft.md` also exists.

## Verdict

The context is sufficient: the objective and motivation are clear (lines 9–78). There are **0 Blockers, 7 Majors and 4 Nits**. The scope is too large for 5 people in 24 days, and the same detail is repeated across sections.

## Findings

### 1. 🟡 Major: Class techniques not covered (features, optical flow, segmentation)
- **Lines:** 44, 112, 354–360, 720
- **Problem:** The Problem lists "calibración, ArUco, homografías, PnP, features, flujo óptico y segmentación" as the required techniques. The design never uses features or optical flow, and segmentation appears only in Future Improvements (line 720). G5 still promises a slide that maps each class technique to where it is used, so three of its rows would be empty.
- **Why it matters:** This is the graded root requirement. The design neither covers these techniques nor declares them out of scope. If the brief requires every technique, this becomes a Blocker.
- **Suggested change:** Either add a Non-Goal backed by the professor's confirmation that a subset is enough, or add one small, visible use of each technique and list the mapping in G5:
  - **Optical flow:** run LK (`calcOpticalFlowPyrLK`) on the last good marker corners to bridge occlusions. This replaces the blind 0.5 s hold at line 313.
  - **Segmentation:** use a MediaPipe hand mask or an HSV skin mask, shown in the debug overlay.
  - **Features:** use ORB matching on the board artwork as the `--single-marker` fallback (see Finding 4).

### 2. 🟡 Major: The remote mode has no motivation in The Problem, yet adds the most code and the most failure points
- **Lines:** 26–34, 58–64, 94–105, 194–205, 234–236, 249–264, 277–285, 668–677, 706–711, 977–985, 1002–1015
- **Problem:** The Problem never asks for a second human player. Supporting one still requires all of the following:
  - a public cloudflared tunnel with tokens;
  - roles detected from the `Cf-Connecting-Ip` header;
  - a second 480p encode with per-connection send tasks;
  - the `hello`/`denied` messages and the `can_act` matrix;
  - static file serving exposed to the internet, plus a whole security section.

  Problem 2 lists the tunnel as a demo risk, but that risk only exists because of this design.
- **Why it matters:** It is speculative scope against a 24-day budget. It sits on the riskiest path of a live demo, and it is the only reason the system has an internet-facing attack surface. `cpu` plus `local` already shows a full game with turns (G2) on one machine.
- **Suggested change:** Choose one:
  - Add the motivation to The Problem.
  - Make remote a stretch goal gated on the day-12 control. Today the schedule (line 1218) treats it as committed.

  If remote stays, make `cpu` the main demo path and remote a bonus segment instead of the opener (line 864).

### 3. 🟡 Major: The "actions" interface is described three ways, and it is the contract that freezes on day 2
- **Lines:** 380–387, 415, 953, 962–963, 1011–1013
- **Problem:** The three descriptions disagree:
  - the Technical Plan has `select(cell)` / `target(cell)`;
  - `game.py` has `("tap", cell)` / `("reset",)`;
  - `hands.py` queues `("target_or_select", cell)`.

  It is also unclear who owns the animation lock. It sits under "Juego (autoridad)", but `transport` ignores input, and `phase:"animating"` is a game state in the protocol.
- **Why it matters:** G6 freezes these interfaces on day 2 so that P2, P3 and P4 can work in parallel. Three different versions will produce mismatched code at integration on day 10.
- **Suggested change:**
  - Use one action, `("tap", cell)`, in all three places.
  - Decide whether `animating` is a game phase or a transport lock, and state it once.
  - Remove `select/target` from lines 381–383.

### 4. 🟡 Major: The fallback chain is longer than the team can build and rehearse, and parts of it do not fit together
- **Lines:** 93, 314, 484–488, 496, 605, 877, 933
- **Problem:** Line 93 lists 7 rehearsed fallbacks.
  - Remote is not a fallback for mouse input.
  - `--single-marker` needs a second spec, a second PDF and a second code path. The 12-marker board with a ≥2-marker threshold already handles partial occlusion, and the doc never says what failure a single big marker solves that the board does not.
  - Pose lock `L`, replay and the MP4 overlap.
- **Why it matters:** Each fallback costs code and rehearsal time (lines 1221, 1240), and an unrehearsed fallback does not help in a live demo.
- **Suggested change:** Reduce the chain to mouse → local/cpu → recorded MP4. Drop `--single-marker`, or replace it with a feature-based fallback that also addresses Finding 1. Keep `L` only if the day-12 test shows that hand occlusion breaks the pose.

### 5. 🟡 Major: A custom recording format and replay engine where a video file would do
- **Lines:** 485–486, 507, 888–895, 995–1000, 1142, 1208, 1230
- **Problem:** The `.dj` format stores every outgoing message as JSONL with base64-encoded 720p JPEGs. That is about 4 MB/s, or 1.5–2 GB for a 7-minute game. Line 486 and line 997 also disagree on the format. Replay re-sends recorded output, so it never exercises the vision pipeline, which is the graded part.
- **Why it matters:** It is a custom format with a custom player, and it duplicates the MP4 fallback (line 496).
- **Suggested change:**
  - Record the raw camera with `cv2.VideoWriter`, plus a small action log `[(t, "tap", cell)]`.
  - To replay, open the file with `cv2.VideoCapture(path)` instead of a camera index, and feed the action log through the normal `transport` input path.
  - Have `fake_session.py` write a synthetic MP4 the same way.

  Replay then runs the real pipeline end to end, and the base64 bloat goes away.

### 6. 🟡 Major: The internet-facing static file server is written from scratch
- **Lines:** 229, 710, 1007, 1200
- **Problem:** `process_request` resolves arbitrary paths under `web/`, assigns MIME types by extension, and relies on rejecting `..` for safety. All of it is reachable through the tunnel.
- **Why it matters:** This is security at a trust boundary. A substring check on `..` is a weak defence against path traversal, for example through encoded or alternate separators.
- **Suggested change:** At startup, walk `web/` once into a dict `{url_path: (path, mime)}` using stdlib `mimetypes`. Serve exact matches only and return 404 for anything else. Alternatively, use aiohttp `add_static`, at the cost of a new dependency.

### 7. 🟡 Major: The asset pipeline contradicts Alternative I and starts with the expensive path
- **Lines:** 126, 613, 843–859, 1105–1128, 1216
- **Problem:** Alternative I says the project uses pre-animated models (Quaternius CC0, Sketchfab). File 35 instead generates the creatures with AI through the Blender MCP, with a contract doc, prompts, a `.glb` checker, `assets_src/`, a viewer mode and a day-7 go/no-go. The doc itself admits that non-humanoid rigging is what the AI does worst.
- **Why it matters:** It builds a generation pipeline before checking whether existing animated models are good enough.
- **Suggested change:**
  - Make pre-animated CC0 models the default.
  - Map clip names per creature kind in `creatures.js`, for example `{idle: "Idle_Loop"}`.
  - Use the Blender MCP only to fill a specific gap after day 7.
  - Shrink `check_glb.py` to size and clip checks, or drop it.

### 8. 🟡 Major: Implementation detail in the Technical Plan, and the same numbers repeated in several places
- **Lines:** 269–275 vs 788, 971–973; 307–318 vs 784, 930; 371–374 vs 786; 328 vs 1048; 455 vs 1058
- **Problem:** Several values appear in two or three places:
  - the AI score weights and delays;
  - the IPPE 20% tie rule, 3 px and 0.5 s;
  - the pinch values 0.25/0.35/300 ms;
  - the `updateProjectionMatrix` note.
- **Why it matters:** The doc is meant to freeze as a contract (G6). Values kept in three places will drift apart, and readers cannot tell which copy is authoritative.
- **Suggested change:** The Technical Plan describes behaviour and interfaces only. The numbers live only in `config.toml` (file 2), and the file entries point to it.

### 9. 🟢 Nit: Protocol versioning is not needed
- **Lines:** 402, 439–440, 993, 1207
- **Problem:** Both ends ship from the same repo, in the same commit, served by the same process. The version mismatch these checks guard against cannot happen.
- **Suggested change:** Drop the `v` field, the "ignore unknown fields" rule and the `v ≠ 1` test.

### 10. 🟢 Nit: The hologram shader is a full `ShaderMaterial` with skinning wired by hand
- **Lines:** 455, 1058
- **Suggested change:** Extend `MeshBasicMaterial` through `onBeforeCompile`, which provides skinning, and inject the fresnel, scanline and flicker code there.

### 11. 🟢 Nit: The host role is inferred from a missing header
- **Lines:** 253, 1008
- **Problem:** The host is whoever connects without `Cf-Connecting-Ip`, so the rule depends on how the tunnel behaves.
- **Suggested change:** Give the host its own token in the local Chrome `--app` URL. Then the token alone decides the role for everyone.

### 12. 🟢 Nit: Goal order and a duplicated test
- **Lines:** 94, 106; 1183 vs 1192
- **Problem:** G7 sits between G4 and G5. G2's game-length measurement appears in both `test_game` and `test_ai`.
- **Suggested change:** Reorder the goals, and keep the G2 duration check in `test_ai` only.
