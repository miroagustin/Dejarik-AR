// Cola de eventos: se reproducen de a uno y en orden. Al terminar cada uno, el
// anfitrión manda anim_done (el remoto solo mira).
import { cellCenter } from "./scene.js";
import { tween } from "./creatures.js";

export function createEventQueue({ army, spec, hud, onDone }) {
  const queue = [];
  let running = false;

  const handlers = {
    async move(e) {
      const c = army.get(e.piece);
      if (!c) return;
      await c.walkTo(...cellCenter(spec, e.to));
      c.cell = e.to;
    },

    async attack(e) {
      const c = army.get(e.piece);
      hud.combat(e);
      if (!c) return;
      c.face(...cellCenter(spec, e.to));
      // el defensor mira al atacante
      const target = [...army.byId.values()].find(o => o.cell === e.to);
      target?.face(...cellCenter(spec, c.cell));
      await c.play("attack");
      c.play("idle");
    },

    async hit(e) {
      const c = army.get(e.piece);
      hud.hp(e.piece, e.result.hp);
      if (!c) return;
      const anim = c.play("hit");
      await tween(0.35, t => c.setFlash(t < 0.3 ? t / 0.3 : (1 - t) / 0.7));
      c.setFlash(0);
      await anim;
      if (e.result.hp > 0) c.play("idle");
    },

    async death(e) {
      const c = army.get(e.piece);
      if (!c) return;
      await c.play("die");
      await tween(0.6, t => c.setOpacity(1 - t));
      army.parent.remove(c.root);
      army.byId.delete(e.piece);
    },

    async turn(e) { hud.turn(e.result.turn); },

    async win(e) { hud.win(e.result.winner); },
  };

  async function pump() {
    if (running) return;
    running = true;
    while (queue.length) {
      const e = queue.shift();
      try {
        await (handlers[e.kind] ?? (async () => {}))(e);
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
