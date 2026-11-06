// HUD en HTML sobre el canvas.

const NAMES = { guardian: "Guardián", bestia: "Bestia", acechador: "Acechador", soldado: "Soldado" };
const SIDES = ["AZUL", "ROJO"];
// El nombre del gesto (G7): la misma frase va en el README, docs/rules.md y el guion.
export const HINT = "Apuntá con el índice y juntá dos dedos";

const $ = id => document.getElementById(id);

export function createHud() {
  let you = 0, mode = "local", turn = 0, pieces = [];
  let noticeTimer = null;

  function turnText() {
    if (mode === "cpu" && turn === 1) return "La PC está pensando…";
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
    combat(e) {
      const atk = pieces.find(p => p.id === e.piece);
      const def = pieces.find(p => p.cell === e.to && p.alive);
      const r = e.result;
      const word = { hit: "golpe", counter: "contragolpe", tie: "empate" }[r.outcome];
      // Solo las tiradas del dado: ATK/DEF viven en game.py y no se duplican acá.
      const a = `${atk ? NAMES[atk.kind] : "?"} saca ${r.atk_roll}`;
      const d = `${def ? NAMES[def.kind] : "?"} saca ${r.def_roll}`;
      const el = $("combat");
      el.textContent = `${a} vs ${d} → ${word}`;
      el.className = `p${atk?.owner ?? 0}`;
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
