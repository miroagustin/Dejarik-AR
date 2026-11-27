// HUD en HTML sobre el canvas.

const NAMES = { guardian: "Guardián", bestia: "Bestia", acechador: "Acechador", soldado: "Soldado" };
const SIDES = ["AZUL", "ROJO"];
// El nombre del gesto (G7): la misma frase va en el README, docs/rules.md y el guion.
export const HINT = "Apoyá el índice en una casilla y sostené";

const FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];
const ROLL_MS = 800;     // cuánto giran los dados (el sonido del dado dura ~550 ms)
const COMBAT_MS = 4000;  // cuánto queda el resultado en pantalla después de caer

const $ = id => document.getElementById(id);

// Dónde poner el panel de combate para no pisar el tablero.
// b: rectángulo del tablero en px de ventana {x0, y0, x1, y1}; W×H ventana; w×h panel.
// Devuelve la esquina {x, y}, centrada en la franja libre más holgada. Se prefieren los
// costados; arriba y abajo descuentan el turno (arriba) y el hint (abajo), que nunca se tapan.
// Si no entra en ningún lado, va pegado al costado más holgado: pisa el borde del tablero,
// no el centro donde están las criaturas.
export function combatSpot(b, W, H, w, h, M = 16) {
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const midY = clamp((b.y0 + b.y1) / 2 - h / 2, M, H - h - M);
  const midX = clamp((b.x0 + b.x1) / 2 - w / 2, M, W - w - M);
  const TOP = 60, BOTTOM = 96;
  const sides = [
    { slack: W - b.x1 - w - 2 * M, x: b.x1 + (W - b.x1 - w) / 2, y: midY },
    { slack: b.x0 - w - 2 * M, x: (b.x0 - w) / 2, y: midY },
    { slack: b.y0 - TOP - h - 2 * M, x: midX, y: TOP + (b.y0 - TOP - h) / 2 },
    { slack: H - BOTTOM - b.y1 - h - 2 * M, x: midX, y: b.y1 + (H - BOTTOM - b.y1 - h) / 2 },
  ];
  // Un costado que entra gana sobre arriba/abajo; si ninguno entra, el de más holgura.
  const side = sides[0].slack >= sides[1].slack ? sides[0] : sides[1];
  const vert = sides[2].slack >= sides[3].slack ? sides[2] : sides[3];
  const best = side.slack >= 0 ? side : vert.slack >= 0 ? vert : side;
  return { x: clamp(best.x, M, W - w - M), y: clamp(best.y, TOP, H - BOTTOM - h) };
}

export function createHud({ boardRect } = {}) {
  let you = 0, mode = "local", turn = 0, pieces = [];
  let noticeTimer = null, combatTimer = null;

  function turnText() {
    if (mode === "cpu" && turn !== you) return "La PC está pensando…";
    if (mode === "remote" && turn !== you) return `Turno del rival (${SIDES[turn]})`;
    return `Turno ${SIDES[turn]}`;
  }

  function render() {
    const t = $("turn");
    t.textContent = turnText();
    t.className = `p${turn}`;
    $("roster").innerHTML = pieces.map(p =>
      `<div class="p${p.owner} ${p.alive ? "" : "dead"}">${NAMES[p.kind] ?? p.kind}` +
      `<span class="hp" style="width:${(p.alive ? p.hp : 0) * 14}px"></span></div>`).join("");
  }

  return {
    hello(msg) {
      you = msg.you; mode = msg.mode;
      const r = $("role");
      r.className = `p${you}`;
      r.textContent = `Sos el jugador ${you} (${SIDES[you].toLowerCase()}) · modo ${mode}`;
      const remote = $("remote");
      if (msg.remote && mode === "remote") {
        const { url, tunnel, connected } = msg.remote;
        remote.innerHTML = tunnel === "up"
          ? `Remoto: ${connected ? "conectado" : "esperando"}<br>${url}<button id="copy">copiar</button>`
          : "Túnel no disponible";
        $("copy")?.addEventListener("click", () => navigator.clipboard.writeText(url));
      } else remote.textContent = "";
      render();
    },
    state(msg) { turn = msg.turn; pieces = msg.pieces; render(); },
    turn(t) { turn = t; render(); },
    hp(id, hp) { const p = pieces.find(q => q.id === id); if (p) { p.hp = hp; p.alive = hp > 0; } render(); },
    // Panel de combate: los dos dados giran, caen en la tirada, se ve la cuenta y quién pierde vida.
    // Devuelve una promesa que se cumple cuando caen los dados (la cola espera eso).
    combat(e) {
      const atk = pieces.find(p => p.id === e.piece);
      const def = pieces.find(p => p.cell === e.to && p.alive);
      const r = e.result;
      // "Bestia" es la única criatura femenina: Bestia roja, Soldado rojo.
      const name = p => p ? `${NAMES[p.kind]} ${p.owner ? (p.kind === "bestia" ? "roja" : "rojo") : "azul"}` : "?";
      // atk/def vienen en el evento (game.py es la autoridad); un .dj viejo no los trae.
      const side = (p, label, roll, bonus) => `<div class="side p${p?.owner ?? 0}">
        <div class="who">${name(p)}</div><div class="die">${FACES[0]}</div>
        <div class="sum">${roll}${bonus == null ? "" : ` + ${label} ${bonus} = <b>${roll + bonus}</b>`}</div></div>`;
      const el = $("combat");
      clearTimeout(combatTimer);
      el.className = "on rolling";
      el.innerHTML = `<div class="sides">${side(atk, "ATK", r.atk_roll, r.atk)}<div class="vs">vs</div>` +
        `${side(def, "DEF", r.def_roll, r.def)}</div><div class="outcome"></div>`;
      // Sin pose (o sin boardRect) queda donde dice el CSS: a la derecha, a media altura.
      el.removeAttribute("style");
      const b = boardRect?.();
      if (b) {
        const { x, y } = combatSpot(b, innerWidth, innerHeight, el.offsetWidth, el.offsetHeight);
        Object.assign(el.style, { left: `${x}px`, top: `${y}px`, right: "auto", transform: "none" });
      }
      const dice = el.querySelectorAll(".die");
      const spin = setInterval(() => dice.forEach(d => { d.textContent = FACES[Math.floor(Math.random() * 6)]; }), 70);
      return new Promise(done => setTimeout(() => {
        clearInterval(spin);
        dice[0].textContent = FACES[r.atk_roll - 1];
        dice[1].textContent = FACES[r.def_roll - 1];
        const loser = { hit: def, counter: atk }[r.outcome];
        const word = { hit: "¡GOLPE!", counter: "¡CONTRAGOLPE!", tie: "EMPATE" }[r.outcome];
        const out = el.querySelector(".outcome");
        out.innerHTML = `<div class="word">${word}</div>` + (loser
          ? `<div class="loss p${loser.owner}">${name(loser)} pierde 1 vida</div>`
          : `<div class="loss">Nadie pierde vida</div>`);
        // El que pierde se apaga (sin cambiar tamaños, así nada se corre de lugar).
        if (loser) el.querySelectorAll(".side")[loser === atk ? 0 : 1].classList.add("lost");
        el.className = "on";
        combatTimer = setTimeout(() => { el.className = ""; }, COMBAT_MS);
        done();
      }, ROLL_MS));
    },
    notice(text, ms = 1500) {
      const n = $("notice");
      n.textContent = text;
      clearTimeout(noticeTimer);
      if (ms) noticeTimer = setTimeout(() => { n.textContent = ""; }, ms);
    },
    win(w) {
      const b = $("banner");
      b.textContent = `GANA ${SIDES[w]}`;
      b.className = `on p${w}`;
    },
    clearWin() { $("banner").className = ""; },
    hint(show) { $("hint").textContent = show ? HINT : ""; },
  };
}
