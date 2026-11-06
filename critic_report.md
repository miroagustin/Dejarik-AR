# Stage 7: Critic Review

Target: `docs/designs/hand_interaction.md`, FeatureRange (lines 1-507). Standard: feature-spec-standard (design, structural). Goldfish context: none.
Reviewers: egm-design (completed), egm-structural (completed), egm-style (completed). One round, uninterrupted mode. No fixes applied.

## Totals

| Reviewer | 🔴 | 🟡 | 🟢 |
|---|---|---|---|
| design | 2 | 7 | 9 |
| structural | 1 | 4 | 7 |
| style | 0 | 6 | 8 |

The design reviewer checked the doc's code claims against the repo and they all match: hands.py:76/92, vision.py:183/206-207, `encode_remote`, main.js:88/102, events.js:51, scene.js:54-58, config.toml, concepts_brief.md:328, and the OQ4 cell sizes.

## 🔴 Blockers

- **D-B1. The cancel radius is measured from the cell centre** (L70-71, 132-137, 222).
  - Cell 0 has a radius of about 34.6 mm. Outer-cell corners are about 30 mm from the centre, and interior-cell corners about 23 mm.
  - A legitimate lock in those regions is already more than 20 mm out, so it cancels on the next frame. Because the fingers are still together, it re-locks at once, which gives an endless tic/cancel loop and no confirmation.
  - Fix: measure from the `xy` recorded at lock start.
- **D-B2 / S-1. There is no Risks & Mitigations section**, which the standard requires (whole range).
  - Risks are scattered across OQ1, D, F and H.
  - Never addressed: open-hand false positives, world-landmark depth accuracy, re-arm semantics, the 15 fps remote, dwell usability, old `.dj` compatibility, the fallback if E1 shows no separation, and security of the new fields reaching the remote and recordings.

## 🟡 Major

- **D-M1. The `touch` thresholds treat almost every hand with the middle finger extended as "closed"** (L191, 282-285, 377-384).
  - on = 0.35 × ~9 cm ≈ 3.2 cm. Two relaxed extended fingers sit 1.5-2.5 cm apart, so a hovering hand starts the gesture.
  - Fix: E1 should report the separation between pointing, joined and open-relaxed hands. Add "open hand hovering over a valid destination" to the G2 test.
- **D-M2. It is unproven that 3D world landmarks fix the line-of-sight ambiguity** (L68-70, 179-185, 369-375). Their z is inferred by the same model from the same crop. Log both the 2D and 3D ratios in E1 and keep the 2D metric selectable.
- **D-M3. Re-arm after a cancel or a fire is undefined** (L74, 218-226).
  - Sliding with the fingers closed re-locks a new cell. Leaving the radius at `hold = 1` allows a second confirmation.
  - Fix: require an explicit open (metric > off, or the hand lost), define "intento", and add tests. (Same issue as Stage 6 #1.)
- **D-M4. Cancel is inferred from sampled `hold` dropping to 0** (L250-253). This is fragile on the 15 fps remote, which skips frames. Add an explicit `result` field or an attempt counter.
- **D-M5. The `dwell` plan B was never analysed** (L138-140, 163, 193, 386-392).
  - It is active whenever a hand is present, and it taps any cell after a 1 s pause.
  - It needs its own re-arm rule and an acceptance criterion.
- **D-M6. The locked cell can differ from the highlighted cell** (L220-221, 236-242). The highlight is debounced but the lock takes the raw cell, so at a boundary the ring jumps to the neighbour. Lock the cell that is shown.
- **D-M7 / S-3. Rejection rationales attribute decisions to the author instead of giving a trade-off** (L354-479).
  - C rests only on "pidió medirlo en 3D".
  - G is a deferral condition, not a rejection reason.
  - K-N say "(aprobó el Technical Plan)" but link no approval.
- **S-2. Additional Resources and Cambios respecto del brief are H3s nested under Alternatives** (L485, 492). Promote both to H2.
- **S-4 / ST-M4. Open Questions contradict the decision sections** (L130-138 vs 460-470, 500-502).
  - OQ3 is "Falta confirmar" but treated as decided.
  - OQ4 and OQ5 are "propuesto" but used as settled.
  - OQ1 is "resuelta" but still listed.
- **S-5. No Markdown links to sources**: the brief, `concepts_brief.md:328`, and Additional Resources.
- **ST-M1. The Problem section uses the "~4 cm" cell size that OQ4 rejects** (L43 vs 133-136). Restate it with 37 mm radial and 28 mm arc.
- **ST-M2. G3 and G4 criteria are subjective** (L75-88). There is no tester count or pass threshold, and the eyes-off claim in G3's title is not tested.
- **ST-M3. G7 asks for one phrase for the gesture, but the doc uses five** (L96-98, 327-329, 392). Also, `hand.pinch` keeps its name but changes meaning.
- **ST-M4. "El control", E1-E3 and "16-18/11" are undefined** (L59, 27, 129, …). Add a milestones line in the Overview.
- **ST-M5. Estimates are presented as facts**: ~1.25 (L198), 3-4 cm (L41), +10-20 ms (L421).
- **ST-M6. "Sin bajar el brillo" contradicts the opacity drop to 0.35** (L305-307). The flicker change is also not quantified.

## 🟢 Nits

- **D-N1.** Jargon (E0-E4, control, brief, Alternatives Weighed) is undefined. The "contra E0" baseline plays no role in criteria that are absolute.
- **D-N2.** `baseOpacity` is still written by both the tracking fade and death, so "se componen" is overstated.
- **D-N3.** Larger flicker amplitude dims the average brightness (`hologram.js:36`). `uPass` must be a per-material uniform, because `holoUniforms` is shared.
- **D-N4.** The browser needs defaults for missing `hold`/`box` in old `.dj` recordings. The doc doesn't say what values are used when the old keys are present.
- **D-N5.** The creature-root projection is not "la misma cuenta que `project`": the frames differ. A tall creature whose base sits outside the box is a limit to accept.
- **D-N6.** Landmark 8 sits 5-8 mm above the pad, so "no hay error de altura" overstates it.
- **D-N7.** It is unspecified which component owns the `extended_on/off` hysteresis.
- **D-N8.** `hold` reads `Pinch` internals (`closed_since`, `min_s`).
- **D-N9.** There is no frame-time budget for the hand thread.
- **S-6.** The pseudocode and the prose disagree on `xy None`. `min_s` is undefined, and the mm/m conversion is not stated.
- **S-7.** The `json` block (L246-248) doesn't parse.
- **S-8.** "Dónde vive cada cosa" is unnumbered.
- **S-9 / ST-N8.** L85 runs past the wrap width.
- **S-10.** Open Questions comes before the Technical Plan but keeps referring forward to it.
- **S-11 / ST-N7.** E is "No se descarta" under a "Reason for Rejection" label. Relabel it as plan B.
- **S-12.** Horizontal rules are used inconsistently.
- **ST-N1.** English mixed into Spanish prose: goal, draft, design, look, debounce.
- **ST-N2.** "corrido" has three meanings.
- **ST-N3.** The distance-ratio notation varies across sections.
- **ST-N4.** "un radio" in G2 doesn't say which radius.
- **ST-N5.** Vague words: "mucho trabajo", "se explica fácil", "mucho más cerca", and others.
- **ST-N6.** Rhetorical sentences in the Problem section (L38, L49, L11).
- **ST-N7.** "Rechazado por el autor" is repeated about 12 times. State it once at L344.
- **ST-N8.** The `hand.px` remote bug is assumed known (L262). "Entrada segura" is ambiguous.
