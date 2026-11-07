// Overlay de debug (tecla D): muestra lo que hace la visión. Se dibuja en 2D
// sobre el canvas, en píxeles del cuadro.

export function createDebug(canvas) {
  const ctx = canvas.getContext("2d");
  let on = false, frames = 0, fps = 0, last = performance.now(), mx = false, my = false, W = 0, H = 0;

  // Con el espejo (#stage.mirror-x / mirror-y) el canvas se ve dado vuelta: el texto se
  // dibuja espejado otra vez en los mismos ejes para que se lea. (x, y) es la posición en el cuadro.
  function textAt(fn, x, y) {
    if (!mx && !my) return fn(x, y);
    ctx.save();
    ctx.setTransform(mx ? -1 : 1, 0, 0, my ? -1 : 1, mx ? W : 0, my ? H : 0);
    fn(mx ? W - x : x, my ? H - y : y);
    ctx.restore();
  }

  function line(text, y) {
    // Arriba a la izquierda de la pantalla, con o sin espejo.
    textAt((x, y) => {
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(x - 5, y - 16, ctx.measureText(text).width + 10, 21);
      ctx.fillStyle = "#7fffb0";
      ctx.fillText(text, x, y);
    }, mx ? W - 13 : 13, my ? H - y : y);
  }

  return {
    setMirror(x, y) { mx = x; my = y; },
    toggle() { on = !on; canvas.classList.toggle("on", on); return on; },
    get on() { return on; },

    // header: el del último cuadro; project(x, y, z) -> [u, v] en píxeles del cuadro, o null.
    draw(header, project) {
      frames++;
      const now = performance.now();
      if (now - last > 500) { fps = (frames * 1000) / (now - last); frames = 0; last = now; }
      if (!on || !header) return;
      const [w, h] = header.size;
      W = w; H = h;
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      ctx.clearRect(0, 0, w, h);
      ctx.font = "15px Consolas, monospace";
      ctx.lineWidth = 2;

      const dbg = header.debug;
      if (dbg?.corners) {
        ctx.strokeStyle = "#7fffb0";
        dbg.corners.forEach((quad, i) => {
          ctx.beginPath();
          quad.forEach(([u, v], j) => (j ? ctx.lineTo(u, v) : ctx.moveTo(u, v)));
          ctx.closePath();
          ctx.stroke();
          ctx.fillStyle = "#7fffb0";
          textAt((x, y) => ctx.fillText(String(dbg.ids[i]), x, y), quad[0][0], quad[0][1] - 4);
        });
      }

      if (header.pose.ok) {
        const o = project(0, 0, 0);
        [[0.05, 0, 0, "#ff4040"], [0, 0.05, 0, "#40ff40"], [0, 0, 0.05, "#4080ff"]].forEach(([x, y, z, c]) => {
          const p = project(x, y, z);
          if (!o || !p) return;
          ctx.strokeStyle = c;
          ctx.beginPath(); ctx.moveTo(...o); ctx.lineTo(...p); ctx.stroke();
        });
      }

      const hand = header.hand;
      if (hand?.px) {
        ctx.fillStyle = hand.pinch ? "#ffd36b" : "#ffffff";
        ctx.beginPath(); ctx.arc(hand.px[0], hand.px[1], 7, 0, Math.PI * 2); ctx.fill();
      }
      if (hand?.box) {
        const [u0, v0, u1, v1] = hand.box;
        ctx.strokeStyle = "rgba(255,255,255,0.5)";
        ctx.strokeRect(u0, v0, u1 - u0, v1 - v0);
      }

      const p = header.pose;
      let y = 24;
      line(`render ${fps.toFixed(0)} fps · cuadro ${header.frame_id}`, y); y += 24;
      line(`pose ${p.ok ? "ok" : "PERDIDA"} · marcadores ${p.n_markers} · reproyección ${p.reproj_px.toFixed(2)} px${p.locked ? " · BLOQUEADA" : ""}`, y); y += 24;
      if (dbg?.ms) { line("ms " + Object.entries(dbg.ms).map(([k, v]) => `${k} ${(+v).toFixed(1)}`).join(" · "), y); y += 24; }
      const hd = dbg?.hand;
      if (hd) {
        const f = v => (v == null ? "—" : v.toFixed(2));
        line(`mano ${f(hd.metric)} (2D ${f(hd.metric2d)}) · medio ${f(hd.ext)} ${hd.extended ? "estirado" : "doblado"} · ` +
             `hold ${f(hd.hold)} · fijada ${hd.lock_cell ?? "—"} · dist ${hd.dist_mm == null ? "—" : hd.dist_mm.toFixed(0) + " mm"} · ${hd.reason || "ok"} · ${hd.ms ?? "—"} ms`, y);
      }
    },
  };
}
