// Cola de eventos: se reproducen de a uno y en orden. Al terminar cada uno, el
// anfitrión manda anim_done (el remoto solo mira).
import { cellCenter } from "./scene.js";
import { tween } from "./creatures.js";

export function createEventQueue({ army, spec, hud, audio, onDone }) {
  const queue = [];
  let running = false;
  let fight = null; // { atk, def } de la última pelea, para saber quién sobrevive en death

  const handlers = {
    async move(e) {
      const c = army.get(e.piece);
      if (!c) return;
      const steps = setInterval(() => audio.play("step"), 260);
      try { await c.walkTo(...cellCenter(spec, e.to)); } finally { clearInterval(steps); }
      c.cell = e.to;
    },

    async attack(e) {
      const c = army.get(e.piece);
      audio.play("dice");
      await new Promise(r => setTimeout(r, 550)); // que se escuche el dado antes del resultado
      hud.combat(e);
      if (!c) return;
      c.face(...cellCenter(spec, e.to));
      // el defensor mira al atacante
      const target = [...army.byId.values()].find(o => o.cell === e.to);
      target?.face(...cellCenter(spec, c.cell));
      fight = { atk: c, def: target };
      // En counter el motor le resta vida al atacante: el que pega es el defensor.
      const striker = e.result.outcome === "counter" && target ? target : c;
      audio.play("attack");
      await striker.play("attack");
      striker.play("idle");
    },

    async hit(e) {
      const c = army.get(e.piece);
      hud.hp(e.piece, e.result.hp);
      audio.play("hit");
      if (!c) return;
      const anim = c.play("hit");
      await tween(0.35, t => c.setFlash(t < 0.3 ? t / 0.3 : (1 - t) / 0.7));
      c.setFlash(0);
      await anim;
      if (e.result.hp > 0) c.play("idle");
    },

    async death(e) {
      const c = army.get(e.piece);
      audio.play("death");
      if (!c) return;
      await c.play("die");
      // El sobreviviente festeja junto con el fade, sin esperarlo.
      const survivor = fight && [fight.atk, fight.def].find(o => o && o !== c);
      if (survivor && [...army.byId.values()].includes(survivor)) survivor.celebrate();
      await tween(0.6, t => c.setOpacity(1 - t));
      army.parent.remove(c.root);
      army.byId.delete(e.piece);
      fight = null;
    },

    async turn(e) { hud.turn(e.result.turn); audio.play("turn"); },

    async win(e) {
      army.byId.forEach(c => { if (c.owner === e.result.winner) c.celebrate(); });
      hud.win(e.result.winner);
      audio.play("win");
    },
  };

  async function pump() {
    if (running) return;
    running = true;
    while (queue.length) {
      const e = queue.shift();
      try {
        // Ningún evento puede trabar la cola: si una animación no termina en 8 s, se sigue.
        const stuck = new Promise(r => setTimeout(() => r("stuck"), 8000));
        if (await Promise.race([(handlers[e.kind] ?? (async () => {}))(e), stuck]) === "stuck")
          console.warn("evento sin terminar en 8 s, sigo", e);
      } catch (err) {
        console.error("evento", e, err);
      }
      onDone(e.id);
    }
    running = false;
  }

  return {
    push(events) { queue.push(...events); pump(); },
    get busy() { return running || queue.length > 0; },
  };
}
