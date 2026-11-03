# Stage 7: Critic Review Report (round 1)

- **Target:** `docs/designs/dejarik_ar.md`, FeatureRange (lines 1–726)
- **Reviewers (all completed):**
  - egm-design, against feature-spec-standard
  - egm-structural, against feature-spec-standard
  - egm-style, with no standard
- **Goldfish context:** none
- **Raw findings:** design had 1 Blocker, 12 Majors and 12 Nits; structural had 1 Blocker, 4 Majors and 5 Nits; style had 9 Majors and 12 Nits.
- **After deduplication:** 2 Blockers, 18 Majors and 27 Nits. When reviewers disagreed on severity, the higher one is used.
- **Round status:** not clean, because there are open Blocker and Major findings.

Finding IDs use the form `<reviewer>-1-<n>`. The traceability matrix at the end maps every raw finding to a consolidated item.

---

## 🔴 Blockers

### C1. Three required class techniques are never used (features, optical flow, segmentation)
- **Lines:** 44, 106–112, 297–375, 720. Raised by design-1-B1.
- **Problem:** Line 44 lists the required techniques: calibration, ArUco, homographies, PnP, features, optical flow and segmentation. The design uses only the first four. Segmentation appears only in Future Improvements, and hand occlusion is a Non-Goal (line 127). The G5 slide that maps each class technique to its use would have three empty rows.
- **Fix:** Add a table that maps each technique to a component. For the missing three, either cite the professor's confirmation that a subset is enough, or add a cheap real use:
  - optical flow: LK on the last marker corners, to bridge frames where fewer than 2 markers are detected;
  - segmentation: the MediaPipe hand mask or an HSV skin mask in the debug overlay;
  - features: ORB on the board art as the fallback when no markers are visible.
- Stage 5 raised the same issue (Finding 1).

### C2. There is no Risks & Mitigations section, and the main risks are never named
- **Lines:** whole scope. Risk content is scattered across 58–64, 90–93, 177–184, 472, 475–497 and 706–715. Raised by structural-1-1 and design-1-M8.
- **Problem:** The standard requires constraints, failure modes, security and limits, each with a mitigation. These risks are missing or have no mitigation:
  - host upload below 5 Mbps;
  - tunnel URL rotation, rate limits or outage;
  - the remote seat being hijacked;
  - the host PC and webcam as a single point of failure;
  - MediaPipe precision, with no fallback criterion;
  - the CPU win-rate target being missed;
  - **the leader is the only person who can do rendering, shaders and assets;**
  - asset clip renaming or retargeting, which only the leader can do;
  - CPU contention from Teams, Chrome and MediaPipe on one PC, with no minimum hardware stated.
- **Fix:** Add `## Risks & Mitigations` between Alternatives and the NFRs, as a table with columns Riesgo | Tipo | Prob/impacto | Mitigación | Dueño | Respaldo/ensayo. Fold the scattered items into it and link to it from where they came from.

---

## 🟡 Majors

### C3. The action vocabulary is inconsistent, and it is part of the day-2 contract
- **Lines:** 381–383, 385, 424. Raised by design-1-N3 (partly), plus Stage 5 F3 and Stage 6 F1, F9.
- **Note:** The Stage 7 reviewers saw only lines 1–726. Stages 5 and 6 found that line 381 (`select/target`) conflicts with lines 953 and 963 (`tap`, `target_or_select`). Inside the FeatureRange, `denied` lacks an `"illegal"` reason, which CUJ 2 needs.
- **Fix:** Use one action, `("tap", cell)`, plus `("reset",)`. Add `"illegal"` to the `denied` reasons. State once whether input during `animating` is ignored or denied.

### C4. A classmate can take the remote seat during the demo
- **Lines:** 199, 255, 708. Raised by design-1-M2 and structural-1-1 (part).
- **Problem:** The link goes to the class Teams chat, and line 255 lets the newest `p=1` connection replace the old one. Any classmate who clicks it kicks the real player out.
- **Fix:**
  - Let the first `p=1` connection win, and reject later ones with code 4409.
  - Add a host key that drops the current `p=1`.
  - Send the link by private chat, and update CUJ 6 to say so.

### C5. Host authentication rests on one proxy header
- **Lines:** 253, 706–709. Raised by design-1-M1, plus Stage 5 F11.
- **Problem:** Any connection without `Cf-Connecting-Ip` becomes the host, with `reset`, `lock` and `mode`. Nothing in the spec shows that Cloudflare always adds this header.
- **Fix:** Either put the tunnel on a second loopback port and accept `p=0` only on port 8000, or give the host its own token in the `--app` URL.

### C6. Slow remote links build up delay instead of dropping frames, and the bandwidth budget does not add up
- **Lines:** 279, 283, 295, 651, 699. Raised by design-1-M3 and style-1-M5.
- **Problem:** `cloudflared` accepts data quickly and buffers it upstream, so `await ws.send` never blocks. The delay piles up in the tunnel, which puts G7 at risk. The units are also mixed (MB/s and Mbps): 0.4–0.6 MB/s is 3.2–4.8 Mbps, plus Teams at about 1.5–4 Mbps, which is more than the "≥ 5 Mbps" in the NFR.
- **Fix:**
  - Have the remote acknowledge each frame with `frame_ack`, and allow at most 1–2 unacknowledged frames.
  - Use Mbps everywhere and redo the budget with Teams included.
  - Add a lower quality step (360p, q50, 10 fps).

### C7. Remote assets download through the host's upload during the demo
- **Lines:** 202, 444, 613, 699. Raised by design-1-M4.
- **Problem:** GLBs, audio and Three.js go through the tunnel. At 5 Mbps, 20 MB takes about 32 s, which breaks CUJ 6's "under 5 s" and slows the Teams share while it downloads.
- **Fix:**
  - Set an asset size budget of about 5 MB, and compress the models.
  - Send `Cache-Control` headers.
  - Have the remote player join before the demo starts.
  - Measure asset size on day 12.

### C8. A Python restart breaks the remote link, which contradicts CUJ 4
- **Lines:** 183, 254, 482, 708, 715. Raised by design-1-M5, plus Stage 6 F2.
- **Problem:** Each start creates a new token and a new quick-tunnel URL, so the remote browser keeps retrying a link that no longer exists.
- **Fix:** Either save the token and keep `cloudflared` running across `--resume`, or rewrite CUJ 4 to say the remote player gets a new link.

### C9. Mode switching with `P` is underspecified, and bot moves can race it
- **Lines:** 34, 251, 274–275, 482, 493. Raised by design-1-M6, plus Stage 6 F3.
- **Problem:** The spec leaves three things open:
  - Does `P` into `remote` start the tunnel?
  - What happens to a connected `p=1` when the mode leaves `remote`?
  - Are queued bot taps cancelled on a mode change, or can a stale bot move land in `local`?
- **Fix:** Add a transition table covering the tunnel, `p=1` and pending bot work. A mode change cancels the single bot `asyncio.Task`. Write out the full cycle.

### C10. Chrome stops rendering when its window is covered, which stalls the game
- **Lines:** 230, 285, 387, 477. Raised by design-1-M7.
- **Problem:** Windows native occlusion pauses a covered Chrome window. Then `anim_done` never arrives, every event waits out the 5 s timeout, and the window can freeze in the Teams share.
- **Fix:** Add the launch flags `--disable-features=CalculateNativeWinOcclusion --disable-renderer-backgrounding --disable-backgrounding-occluded-windows`. Add "cover Chrome with Teams" to the rehearsal checks.

### C11. The claim that threads are enough is stated without evidence
- **Lines:** 287–295, 518–520. Raised by design-1-M9 and style-1-M9.
- **Problem:** "El GIL se libera … los hilos alcanzan" and "MediaPipe nunca frena la pose" are stated as fact. The Python code around those calls holds the GIL, and the 480p encode has no thread assigned.
- **Fix:** Reword it as an expectation. Add a check: measure pose fps with the hand thread on and off, on the demo PC, by a named day. Name the fallback (a separate process, a lower MediaPipe rate, or `--input mouse`). Assign the encode to a thread.

### C12. What replay means is ambiguous, and it is frozen on day 2
- **Lines:** 119, 485–486, 507. Raised by design-1-M10, plus Stage 5 F5.
- **Problem:** `--replay` re-sends the recorded `state` and `events`, but the fixture's job is to let `game` run without a camera. Two state streams would conflict. A replay you cannot play duplicates the MP4.
- **Fix:** Make `--replay` replace only the camera input while `game` runs live, and leave canned full playback to the MP4. Freeze this in `docs/protocol.md`.

### C13. The game rules and the length goal are not defined in the FeatureRange
- **Lines:** 26, 86, 89, 271–272, 389–393. Raised by design-1-M11, plus Stage 6 F6.
- **Problem:** The text uses `bestia`, HP, ATK, DEF and the win condition without defining them. G2's "6–8 min" has no basis, and nothing stops a game from stalling forever.
- **Fix:** Add a one-paragraph rules summary to "Cómo se juega" with a forward reference to "Reglas definitivas". Add a turn cap or a sudden-death rule.

### C14. A simpler remote design is missing from Alternatives
- **Lines:** 32, 277–285, 648–656. Raised by design-1-M12, plus Stage 5 F2.
- **Problem:** The remote player already sees the AR through the Teams share. A 2D SVG board with a HUD and clicks would remove the video stream (C6), the asset downloads (C7) and the remote 3D rendering. WebRTC/aiortc is not mentioned either.
- **Fix:** Add both as alternatives with honest trade-offs, for example Teams adds about 1–2 s of latency. Consider the 2D board as the fallback when bandwidth is short.

### C15. Every alternative is rejected with "Rechazada por el autor"
- **Lines:** 124, 536–666. Raised by structural-1-2, style-1-N4 and design-1-N8.
- **Problem:** The standard forbids attributing a rejection to a person without a link to where it was decided. Without the label, several rationales are weak or circular:
  - J, "One-Euro alcanza";
  - K, which restates the design;
  - H and I;
  - the Non-Goal at line 124.
- **Fix:** Drop the label everywhere, or use "Decisión mecánica de diseño" as P and Q do. Rewrite J, K, H, I and line 124 as concrete trade-offs. For J, cite the G1 jitter measurement.

### C16. Goal IDs are out of order (G1–G4, G7, G5, G6)
- **Lines:** 80–119. Raised by structural-1-3, style-1-M3, design-1-N6, plus Stage 5 F12 and Stage 6 F17.
- **Fix:** Renumber the goals in reading order, and update the references at lines 1183 and 1192.

### C17. CUJ 6 uses a flag that does not exist (`--remote`)
- **Line:** 197. Raised by structural-1-4 and style-1-M4, plus Stage 6 F4.
- **Fix:** Change it to "arrancó con `--mode remote` (o cambió con `P`)".

### C18. The protocol cannot carry status the HUD has to show
- **Lines:** 254, 264, 420–427, 471, 497. Raised by structural-1-5.
- **Problem:** No server-to-browser message carries the remote player's connection state or "Túnel no disponible". `remote_url: null` cannot tell "tunnel down" apart from "not in remote mode". `denied` is filed under the wrong subheading, and close code 4401 is not listed in the protocol block.
- **Fix:** Add `"remote":{"tunnel":"up|down|off","connected":bool}`, or a separate `status` message. Move `denied` under "en respuesta a una entrada rechazada". Document 4401.

### C19. The fallback chain mixes unrelated layers
- **Line:** 93. Raised by style-1-M7 and design-1-N7, plus Stage 5 F4 and Stage 6 F5.
- **Problem:** The chain puts input, mode, tracking and media fallbacks in one sequence. "Remoto" is not a fallback for the mouse, and `cpu` is missing.
- **Fix:** Split the chain by failure type, as a small table.

### C20. G3 and G4 are subjective or overclaimed
- **Lines:** 89, 90. Raised by style-1-M1 and style-1-M2.
- **Fix:**
  - G4: change the title to "Demo con respaldos ensayados".
  - G3: drop "vistoso" and add a check, for example: the 5 clips play in every fight, with sound, within X–Y seconds.

---

## 🟢 Nits

| ID | Lines | Finding | Fix |
|---|---|---|---|
| N1 | 179–180, 189 | CUJ 4 and 5 say "un integrante" presses the key, but only the host can (style-1-M6, downgraded) | Say "el anfitrión" |
| N2 | 551 vs 556 | Alternative C says "sin ninguna ventaja", but its own Pros list one (style-1-M8, design-1-N8) | "sin una ventaja que compense el costo" |
| N3 | 356–357 | `undistortPoints` without `P` returns normalized coordinates, so `K·[r1 r2 t]` is wrong. The landmark scale-up is not stated (design-1-N1) | Use `P=K` or drop `K`, and scale 640×360 to 1280×720 |
| N4 | 388 | `save/state.json` can be corrupted if Python crashes mid-write (design-1-N2) | Write to a temp file, then `os.replace` |
| N5 | 434 | Unclear whether `key:"debug"` applies to one connection or to all (design-1-N3) | Make it per connection |
| N6 | 149, 457 | Chrome autoplay policy mutes the startup sound (design-1-N4) | `--autoplay-policy=no-user-gesture-required` |
| N7 | 152 | Teams may not share system audio for a single window (design-1-N5) | Rehearse it, with full-screen sharing as the fallback |
| N8 | 484 | The single marker's position in board coordinates is undefined (design-1-N9) | Define it in `board_spec.json` |
| N9 | 513–516 | Decoding and re-encoding the JPEG costs about 5 ms (design-1-N10) | Forward the camera's MJPG bytes as they are |
| N10 | 465 | Clicks are accepted while `pose.ok=false` (design-1-N11) | Ignore clicks while tracking is lost |
| N11 | 444 | "Three.js r16x" is not a version (design-1-N12, style-1-N12) | Pin the exact release |
| N12 | 717 | Future Improvements is nested under the NFRs (structural-1-6) | Promote it to H2 |
| N13 | 689–691, 725 | NFRs come after Alternatives, and horizontal rules are used inconsistently (structural-1-7) | Move the NFRs earlier, and keep only two rules |
| N14 | 256–264, 478–489 | Tables split their parent bullet lists (structural-1-8) | Use an H4 or a paragraph as the lead-in |
| N15 | 437–440 | A stray blank line splits the protocol notes, and the general rules sit in the wrong block (structural-1-9) | Add "Reglas generales del protocolo" |
| N16 | 67–78 | "Solución propuesta" sits inside The Problem (structural-1-10) | Move it to the Technical Plan or the Overview |
| N17 | 541–542, 551, 565–566 | Subjective judgments: "estable", "maduro", "se ve pobre" (style-1-N1) | Replace with concrete facts |
| N18 | 98, 685, 687 | "se ve tonto" / "se ve razonable" (style-1-N2) | State the behaviour |
| N19 | 82 | "cruz central" is undefined (style-1-N3) | Define it and add it to `board_spec.json` |
| N20 | 30–31 | Redundant parentheticals "(vos mismo)" and "(contra la PC)" (style-1-N5) | Remove them |
| N21 | 620–621 | Alternative J states speculation as fact (style-1-N6) | Calibrate it and cite G1 |
| N22 | 572 | "la única opción todo-Python" is absolute (style-1-N7) | "la única de las evaluadas" |
| N23 | 532 | Hyperbole: "todo lo que el equipo sabe hacer" (style-1-N8) | "toda la visión y la lógica" |
| N24 | 576, 586, 610 | "bastante más", "justamente", "Animaciones gratis" (style-1-N9) | Quantify, delete, or reword |
| N25 | 345 | Mixed verbs with different subjects (style-1-N10) | Split the sentence |
| N26 | 172, 221, 229 | "unos 0,5 s", "Tiene todo lo que piensa", "tres procesos" (style-1-N11) | Use exact wording |
| N27 | 253, 472 | `Cf-Connecting-Ip` is added by Cloudflare's edge, not by cloudflared, and the Teams compression claim is presented as observed (style-1-N12) | Reword both |

---

## Traceability Matrix

| Raw finding | → Consolidated |
|---|---|
| design-1-B1 | C1 |
| design-1-M1 | C5 |
| design-1-M2 | C4 |
| design-1-M3 | C6 |
| design-1-M4 | C7 |
| design-1-M5 | C8 |
| design-1-M6 | C9 |
| design-1-M7 | C10 |
| design-1-M8 | C2 |
| design-1-M9 | C11 |
| design-1-M10 | C12 |
| design-1-M11 | C13 |
| design-1-M12 | C14 |
| design-1-N1 | N3 |
| design-1-N2 | N4 |
| design-1-N3 | C3 (`illegal`), N5 (`debug`) |
| design-1-N4 | N6 |
| design-1-N5 | N7 |
| design-1-N6 | C16 |
| design-1-N7 | C19 |
| design-1-N8 | C15, N2 |
| design-1-N9 | N8 |
| design-1-N10 | N9 |
| design-1-N11 | N10 |
| design-1-N12 | N11 |
| structural-1-1 | C2 |
| structural-1-2 | C15 |
| structural-1-3 | C16 |
| structural-1-4 | C17 |
| structural-1-5 | C18 |
| structural-1-6 | N12 |
| structural-1-7 | N13 |
| structural-1-8 | N14 |
| structural-1-9 | N15 |
| structural-1-10 | N16 |
| style-1-M1 | C20 |
| style-1-M2 | C20 |
| style-1-M3 | C16 |
| style-1-M4 | C17 |
| style-1-M5 | C6 |
| style-1-M6 | N1 |
| style-1-M7 | C19 |
| style-1-M8 | N2 |
| style-1-M9 | C11 |
| style-1-N1 | N17 |
| style-1-N2 | N18 |
| style-1-N3 | N19 |
| style-1-N4 | C15 |
| style-1-N5 | N20 |
| style-1-N6 | N21 |
| style-1-N7 | N22 |
| style-1-N8 | N23 |
| style-1-N9 | N24 |
| style-1-N10 | N25 |
| style-1-N11 | N26 |
| style-1-N12 | N11, N27 |

**Cross-stage overlap:** C1, C3, C8, C9, C12, C13, C14, C16, C17 and C19 were also raised in Stage 5 (`zoom_out_report.md`) or Stage 6 (`comprehension_report.md`).
