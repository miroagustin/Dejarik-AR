# Comprehension Test: criaturas_canon.md (Stage 6)

**Target:** `docs/designs/criaturas_canon.md` (FeatureRange 1-428, DetailedRange 429-673)
**Reviewer:** `egm-comprehension` (completed). It read only the target document; no standard was applied.

## What this proposes

The design has two independent parts, and each can be reverted on its own.

**Part A (clips):**
- The asset tool currently keeps 5 of the 14 animations in the Quaternius models. It will now keep all 14.
- A single `MOMENTS` table in the client maps each "canon moment" (idle, walk, attack, hit, die, win) to a clip.
- The design adds a victory gesture (Wave or Yes, not yet chosen):
  - the survivor of every fatal fight plays it, without blocking input;
  - every living piece of the winning side plays it at game end.
- It fixes the `counter` animation so the defender, not the attacker, is shown striking.
- It quantizes the animation mixer and the walk tween to about 12 fps so movement looks like stop-motion.
- A `?clips=basic` URL flag turns off the gesture and the stepping without a redeploy. It does not undo the counter fix.

**Part B ("life label"):** a one-line CSS change moves the `#roster` HP list from top-left, where debug text overlaps it, to bottom-left.

An optional fourth commit adds Run for 2-square moves (routed through the middle square) and possibly Weapon as the soldier's attack.

## How the existing system works, per this document

- A Python game engine (`dejarik/game.py`) resolves attacks into outcomes (`hit`, `counter`, `tie`) and emits ordered events (`attack`, `hit`, `death`, `win`).
- A JS web client (`events.js`) plays these events through a queue. It animates `Creature` objects (owned by an `Army`) with a three.js-style mixer at 60 fps.
- The server waits up to 5 s per event for the client. The client has its own 8 s timeout.
- An asset pipeline adapts the 4 original GLB files:
  - `adapt_glb.py` renames and keeps 5 contract clips and drops the rest.
  - `check_glb.py` validates the result.
- The HUD shows `#role`, `#roster`, `#combat`, `#hint` and other elements outside a mirrorable `#stage`.
- A debug overlay draws status text in the top-left.
- Pieces are selected through hand tracking with a hold/"waiting ring".
- An in-browser viewer (`?viewer=<kind>`) previews one creature's clips.

## Findings

No section was impossible to paraphrase, so there are no Blockers.

### 1. Major: the project itself is never introduced (Overview, lines 9-32)
- The document never says what a "dejarik" is: the Star Wars holographic chess game.
- It never describes the product: a Python game server, a web client with a 3D board, hand tracking with a mirrored camera image, a live demo with an operator and an audience.
- A reader has to piece this together from file paths, `#stage.mirror`, "tracking" and "operador".
- The base design is linked at line 417, but the doc relies on it without a one-sentence summary.

### 2. Major: Run and Weapon have no stated status in the feature section (lines 84-86, 153-156, 344, 403-404)
- Non-Goals list the deliberately unused clips (Duck, No, Jump*, the losing Wave/Yes). Run and Weapon are not on that list.
- They are also not in `MOMENTS` (line 174) and are never assigned a moment in the Technical Plan.
- The NFR at line 404 then mentions a "Run/Weapon" commit that is only defined in the Detailed Plan (lines 602-654).
- Line 91 rejects Weapon-by-margin, but nothing in lines 1-428 says Weapon may still be used another way.
- A reader of the feature range cannot tell whether these two clips are unused, deferred or planned.

### 3. Major: `anim_done` and the 5 s server wait are not explained (lines 72-75, 211-216, 355)
- G5 and the no-`await` decision depend on a handshake: the server sends an event, the client plays it and replies `anim_done`, and the server waits up to 5 s. Input stays blocked ("Esperá…") until then.
- The doc never describes this handshake. `anim_done` appears once (line 212) without a definition.
- It also never says what happens when the 5 s or 8 s limits are exceeded.

### 4. Major: the timing math contradicts the stated concurrency (lines 211-216, 354-355)
- The gesture "arranca al mismo tiempo que el fade". If you awaited it, the handler would end 1.67 s after the fade starts, so the cost would be about +1.07 s.
- The 3.2 s total and the "+1.7 s" add the gesture after the fade, as if it ran sequentially.
- Either the gesture would start after the fade in Alternative E, or the numbers are wrong. Alternative E's rejection relies on these numbers.

### 5. Major: "hit" means three different things (lines 113-114, 197, 226, 63-64)
- `hit` is a combat outcome ("sale `hit`", line 113), an event in the queue (line 197) and a clip/moment (line 114, `MOMENTS.hit`).
- The outcome values are never listed or defined together. `counter` is explained (line 42); `tie` only as "el empate" (line 94); `pass` (line 380) not at all.
- The CUJs and the A3 diagram are hard to read without a short glossary of outcomes vs events vs clips.

### 6. Major: the title and Part B name promise a label that does not exist (title line 1, lines 21, 260-261)
- "Etiqueta de vida" suggests an HP label. The chosen option adds no label; it moves the existing roster list.
- Line 260 says so, but the title, Overview and G4 still frame it as a label.

### 7. Nit: undefined project terms
- "cápsula de reemplazo" (lines 183, 467, 613): presumably a fallback mesh used when a GLB is missing.
- `hold`, "anillo de espera" and "dwell" (lines 89, 319, 379): hand-tracking selection mechanics.
- "freeze" (lines 336, 425, 605): which date or event?
- "operador" and "demo" (lines 56, 137).
- "8 piezas" (lines 275, 299): it is never said that this means 4 kinds per side.
- The `?viewer=<kind>&still` parameter `still` (line 522).

### 8. Nit: alternative labels are confusing (lines 307-350, 362-394)
- The clip alternatives are A, C, D, E. The chosen design is the implicit "B", never labeled, yet C is defined as "B + salto" (line 324).
- The label alternatives use lowercase a/b/c, so "B" is ambiguous.
- Line 418 cites "G3" of another document, which collides with this doc's G3.

### 9. Nit: references to decisions that live only in the brief
- "brief, etapa 1" (line 346) and "brief, decisión 2" (line 357).
- "La pregunta de dónde queda el resumen de piezas muertas" (line 277) refers to a question never posed in this doc.
- The brief is linked (line 413), but each decision's content should be stated inline.

### 10. Nit: the original clip names are unexplained
- Contract `attack` apparently comes from "Punch" (lines 617, 653), `hit` from "HitReact" and `die` from "Death" (line 455).
- The feature section never gives this mapping. "Punch" first appears in the Detailed Plan.
- The `<kind>_<Monstruo>.glb` naming (line 481) is unexplained; the kind-to-model mapping is not given.

### 11. Nit: vague instruction (lines 554-555)
"Hay que cuidar que el tween y el mixer usen el mismo reloj" does not say which clock, or what goes wrong if they differ. In line 240, `secs` (the walk duration) is used without definition.

### 12. Nit: the 2-square move rule is assumed (lines 632-639)
Commit 4 assumes the reader knows that some pieces (the acechador?) can move 2 squares, and that the engine's BFS skips occupied squares. These game rules are not stated anywhere in the doc.
