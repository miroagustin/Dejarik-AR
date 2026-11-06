import * as THREE from "three";
import { connect } from "./net.js";
import { createScene, cellCenter } from "./scene.js";
import { Army, Creature, KINDS, loadKinds } from "./creatures.js";
import { holoUniforms } from "./hologram.js";
import { createEventQueue } from "./events.js";
import { createHud } from "./hud.js";
import { createDebug } from "./debug.js";
import { createAudio } from "./audio.js";

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
  // Igual que board.load_spec: los radios se corrigen por lo que mide la regla impresa.
  for (const k in spec.radii_m) spec.radii_m[k] *= spec.print_scale_measured / 100;
  const view = createScene(glCanvas, spec);
  const models = await loadKinds();
  const army = new Army(view.boardY, models, spec);
  const hud = createHud();
  const debug = createDebug(document.getElementById("debug"));
  const audio = createAudio();

  let you = 0, isRemote = false, lastHeader = null, legal = [], selectedCell = null, selectedId = null, poseAlpha = 1, aspect = 16 / 9;
  let booted = false, net = null;
  const events = createEventQueue({
    army, spec, hud, audio,
    onDone: id => { if (!isRemote) net.send({ type: "anim_done", id }); },
  });

  layout(view.renderer, aspect);
  addEventListener("resize", () => layout(view.renderer, aspect));

  net = connect({
    hello(msg) { you = msg.you; isRemote = msg.role === "remote"; hud.hello(msg); },
    state(msg) {
      army.sync(msg.pieces, !events.busy);
      if (!events.busy) army.snap(msg.pieces);
      hud.state(msg);
      if (msg.winner == null) hud.clearWin(); else hud.win(msg.winner);
      legal = msg.legal ?? [];
      selectedCell = msg.pieces.find(p => p.id === msg.selected)?.cell ?? null;
      if (msg.selected != null && msg.selected !== selectedId) audio.play("select");
      selectedId = msg.selected;
    },
    events(msg) { events.push(msg.events); },
    denied(msg) { audio.play("denied"); hud.notice(msg.reason === "not_your_turn" ? "No es tu turno" : "Esperá a que termine la animación"); },
    async frame(header, jpeg) {
      await view.setFrame(header, jpeg);
      lastHeader = header;
      if (!booted && header.pose.ok) { booted = true; audio.play("boot"); audio.startHum(); }
      const a = header.size[0] / header.size[1];
      if (Math.abs(a - aspect) > 1e-3) { aspect = a; layout(view.renderer, aspect); }
      if (isRemote) net.send({ type: "frame_ack", frame_id: header.frame_id });
    },
    onStatus(text) { hud.notice(text, text === "conectado" ? 1000 : 0); },
  });

  // Espejo (tecla F): solo visual. Se guarda en el navegador.
  let mirror = localStorage.getItem("mirror") === "1";
  const setMirror = m => { mirror = m; stage.classList.toggle("mirror", m); debug.setMirror(m); localStorage.setItem("mirror", m ? "1" : "0"); };
  setMirror(mirror);

  addEventListener("pointerdown", () => audio.unlock());
  glCanvas.addEventListener("click", ev => {
    const r = glCanvas.getBoundingClientRect();
    const x = mirror ? r.left + r.right - ev.clientX : ev.clientX;
    const p = view.boardPointFromClick(x, ev.clientY);
    if (p) net.send({ type: "click", x: p.x, y: p.y });
  });

  addEventListener("keydown", ev => {
    audio.unlock();
    if (ev.key.toLowerCase() === "m") { hud.notice(audio.toggleMute() ? "Sonido apagado" : "Sonido encendido"); return; }
    if (ev.key.toLowerCase() === "f") { setMirror(!mirror); hud.notice(mirror ? "Espejo activado" : "Espejo desactivado"); return; }
    const key = { d: "debug", l: "lock", r: "reset", p: "mode" }[ev.key.toLowerCase()];
    if (!key) return;
    if (key === "debug") debug.toggle();
    net.send({ type: "key", key });
  });

  // Punto en coordenadas de cámara (mundo) -> [u, v] en píxeles del cuadro, o null.
  const toPx = v => {
    if (!lastHeader) return null;
    v.applyMatrix4(view.camera.projectionMatrix);
    const [w, h] = lastHeader.size;
    return [(v.x + 1) / 2 * w, (1 - v.y) / 2 * h];
  };
  const project = (x, y, z) => toPx(new THREE.Vector3(x, y, z).applyMatrix4(view.board.matrix));

  // Gesto de la mano: anillo de carga, sonidos y pista. Todo sale de header.hand.
  const ring = document.getElementById("hold-ring");
  const tmp = new THREE.Vector3();
  let prevHold = 0, prevHint = false;
  function drawHand(h) {
    const hold = h?.hold ?? 0;
    if (isRemote) { ring.style.display = "none"; prevHold = hold; return; } // lo produce la mano del anfitrión
    if (prevHold < 0.15 && hold >= 0.15) audio.play("holdStart");
    if (prevHold >= 0.15 && prevHold < 1 && hold === 0) audio.play("holdCancel");
    prevHold = hold;
    const c = hold > 0 && h.cell != null && lastHeader.pose.ok ? project(...cellCenter(spec, h.cell), 0) : null;
    if (c) {
      const s = stage.clientWidth / lastHeader.size[0];
      Object.assign(ring.style, { display: "block", left: `${c[0] * s + 40 - 22}px`, top: `${c[1] * s - 40 - 22}px` });
      ring.style.setProperty("--p", hold);
    } else ring.style.display = "none";
    const show = h?.px != null;
    if (show !== prevHint) { hud.hint(show); prevHint = show; }
  }

  // "Se deja atravesar": las criaturas cuya raíz cae en la caja de la mano se vuelven translúcidas.
  function passThrough(h, dt) {
    const box = lastHeader?.pose.ok ? h?.box : null;
    army.byId.forEach(c => {
      let target = 0;
      if (box) {
        const p = toPx(c.root.getWorldPosition(tmp));
        if (p && p[0] >= box[0] && p[0] <= box[2] && p[1] >= box[1] && p[1] <= box[3]) target = 1;
      }
      if (Math.abs(c.pass - target) > 1e-3) c.setPass(c.pass + (target - c.pass) * Math.min(1, dt / 0.05));
      else if (c.pass !== target) c.setPass(target);
    });
  }

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

    const hand = lastHeader?.hand;
    passThrough(hand, dt);
    if (lastHeader) drawHand(hand);

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

// ?soundcheck: renderiza cada sonido sin parlantes y muestra su pico. Si alguno da 0, está roto.
async function runSoundcheck() {
  const out = [];
  for (const name of createAudio(new OfflineAudioContext(1, 48000, 48000)).names) {
    const ctx = new OfflineAudioContext(1, 48000 * 2, 48000);
    createAudio(ctx).play(name);
    const data = (await ctx.startRendering()).getChannelData(0);
    let peak = 0;
    for (const v of data) peak = Math.max(peak, Math.abs(v));
    out.push(`${name.padEnd(8)} pico ${peak.toFixed(3)} ${peak > 0.01 ? "OK" : "MUDO"}`);
  }
  document.getElementById("errors").style.color = "#7fffb0";
  document.getElementById("errors").textContent = out.join("\n");
}

if (params.has("viewer")) runViewer(params.get("viewer"));
else if (params.has("soundcheck")) runSoundcheck();
else runGame();
