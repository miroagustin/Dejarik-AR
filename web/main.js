import * as THREE from "three";
import { connect } from "./net.js";
import { createScene } from "./scene.js";
import { Army, Creature, KINDS, loadKinds } from "./creatures.js";
import { holoUniforms } from "./hologram.js";
import { createEventQueue } from "./events.js";
import { createHud } from "./hud.js";
import { createDebug } from "./debug.js";

const params = new URLSearchParams(location.search);
const glCanvas = document.getElementById("gl");
const stage = document.getElementById("stage");

// Encaja el canvas en la ventana con el aspecto del cuadro (bandas negras, sin recortar).
function layout(renderer, aspect) {
  const W = innerWidth, H = innerHeight;
  const [w, h] = W / H > aspect ? [H * aspect, H] : [W, W / aspect];
  Object.assign(stage.style, { width: `${w}px`, height: `${h}px`, left: `${(W - w) / 2}px`, top: `${(H - h) / 2}px` });
  renderer.setSize(w, h, false);
}

async function runGame() {
  const spec = await (await fetch("board_spec.json")).json();
  const view = createScene(glCanvas, spec);
  const models = await loadKinds();
  const army = new Army(view.boardY, models, spec);
  const hud = createHud();
  const debug = createDebug(document.getElementById("debug"));

  let you = 0, lastHeader = null, legal = [], selectedCell = null, poseAlpha = 1, aspect = 16 / 9;
  let net = null;
  const events = createEventQueue({
    army, spec, hud,
    onDone: id => { if (you === 0) net.send({ type: "anim_done", id }); },
  });

  layout(view.renderer, aspect);
  addEventListener("resize", () => layout(view.renderer, aspect));

  net = connect({
    hello(msg) { you = msg.you; hud.hello(msg); },
    state(msg) {
      army.sync(msg.pieces);
      if (!events.busy) army.snap(msg.pieces);
      hud.state(msg);
      if (msg.winner == null) hud.clearWin(); else hud.win(msg.winner);
      legal = msg.legal ?? [];
      selectedCell = msg.pieces.find(p => p.id === msg.selected)?.cell ?? null;
    },
    events(msg) { events.push(msg.events); },
    denied(msg) { hud.notice(msg.reason === "not_your_turn" ? "No es tu turno" : "Esperá a que termine la animación"); },
    async frame(header, jpeg) {
      await view.setFrame(header, jpeg);
      lastHeader = header;
      const a = header.size[0] / header.size[1];
      if (Math.abs(a - aspect) > 1e-3) { aspect = a; layout(view.renderer, aspect); }
      if (you === 1) net.send({ type: "frame_ack", frame_id: header.frame_id });
    },
    onStatus(text) { hud.notice(text, text === "conectado" ? 1000 : 0); },
  });

  glCanvas.addEventListener("click", ev => {
    const p = view.boardPointFromClick(ev.clientX, ev.clientY);
    if (p) net.send({ type: "click", x: p.x, y: p.y });
  });

  addEventListener("keydown", ev => {
    const key = { d: "debug", l: "lock", r: "reset", p: "mode" }[ev.key.toLowerCase()];
    if (!key) return;
    if (key === "debug") debug.toggle();
    net.send({ type: "key", key });
  });

  const project = (x, y, z) => {
    const v = new THREE.Vector3(x, y, z).applyMatrix4(view.board.matrix).applyMatrix4(view.camera.projectionMatrix);
    if (!lastHeader) return null;
    const [w, h] = lastHeader.size;
    return [(v.x + 1) / 2 * w, (1 - v.y) / 2 * h];
  };

  const clock = new THREE.Clock();
  view.renderer.setAnimationLoop(() => {
    const dt = clock.getDelta();
    holoUniforms.uTime.value = clock.elapsedTime;
    army.update(dt);

    // Pérdida de tracking: las criaturas se desvanecen en ~300 ms.
    const ok = lastHeader?.pose.ok ?? false;
    const target = ok ? 1 : 0.2;
    if (Math.abs(poseAlpha - target) > 0.01) {
      poseAlpha += (target - poseAlpha) * Math.min(1, dt / 0.1);
      army.byId.forEach(c => c.setOpacity(poseAlpha));
    }
    if (lastHeader && !ok) hud.notice("Tracking perdido", 0);
    else if (lastHeader && ok && document.getElementById("notice").textContent === "Tracking perdido") hud.notice("", 1);

    view.highlight(legal, lastHeader?.hand?.cell ?? null, selectedCell);
    view.render();
    debug.draw(lastHeader, project);
  });
}

// ?viewer=<tipo>: una criatura sola, girando, con un botón por clip. Para revisar modelos.
async function runViewer(kind) {
  const renderer = new THREE.WebGLRenderer({ canvas: glCanvas, antialias: true });
  layout(renderer, innerWidth / innerHeight);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.005, 5);
  camera.position.set(0, 0.04, 0.16);
  camera.lookAt(0, 0.022, 0);

  const models = await loadKinds();
  const owner = params.get("side") === "1" ? 1 : 0;
  const creature = new Creature(models[kind] ?? models[KINDS[0]], owner);
  scene.add(creature.root);

  // Disco de referencia: la casilla interna mide 40 mm; el contrato pide un círculo de 44 mm.
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.0215, 0.022, 64),
    new THREE.MeshBasicMaterial({ color: 0x4cc9ff, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2;
  scene.add(ring);

  const ui = document.getElementById("viewer-ui");
  ["idle", "walk", "attack", "hit", "die"].forEach(name => {
    const b = document.createElement("button");
    b.textContent = name;
    b.onclick = () => creature.play(name);
    ui.appendChild(b);
  });
  document.getElementById("role").textContent = `visor: ${kind}`;

  const clock = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const dt = clock.getDelta();
    holoUniforms.uTime.value = clock.elapsedTime;
    creature.mixer.update(dt);
    if (!params.has("still")) creature.root.rotation.y += dt * 0.6;
    renderer.render(scene, camera);
  });
}

if (params.has("viewer")) runViewer(params.get("viewer"));
else runGame();
