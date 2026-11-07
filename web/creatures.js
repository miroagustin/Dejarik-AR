// Criaturas: carga un .glb por tipo, clona con su esqueleto y reproduce clips.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";
import { makeHologramMaterial, SIDE_COLORS } from "./hologram.js";
import { boardToLocal, cellCenter } from "./scene.js";

export const KINDS = ["guardian", "bestia", "acechador", "soldado"];
const LOOPING = new Set(["idle", "walk"]);
const FADE = 0.2;
const WALK_SPEED = 0.06; // m/s
// Gesto de victoria (wave o yes, se elige en el visor). null = sin gesto.
const WIN_CLIP = "yes";
// Stop-motion: la pose y el desplazamiento avanzan de a pasos de STEP s, todos con el mismo reloj.
const STEP = 1 / 12;
export const stepTime = () => Math.floor(performance.now() / 1000 / STEP) * STEP;
const warned = new Set();

// Si falta el .glb, una cápsula con los mismos clips para no frenar el desarrollo.
function placeholder() {
  const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.012, 0.02, 4, 12), new THREE.MeshBasicMaterial());
  mesh.position.y = 0.022;
  const root = new THREE.Group();
  root.add(mesh);
  const track = (name, times, values) => new THREE.AnimationClip(name, -1,
    [new THREE.VectorKeyframeTrack(".scale", times, values)]);
  const animations = [
    track("idle", [0, 1, 2], [1, 1, 1, 1, 1.06, 1, 1, 1, 1]),
    track("walk", [0, 0.25, 0.5], [1, 1, 1, 1.05, 0.95, 1.05, 1, 1, 1]),
    track("attack", [0, 0.2, 0.6], [1, 1, 1, 1.3, 0.8, 1.3, 1, 1, 1]),
    track("hit", [0, 0.15, 0.5], [1, 1, 1, 0.8, 1.2, 0.8, 1, 1, 1]),
    track("die", [0, 0.8], [1, 1, 1, 0.01, 0.01, 0.01]),
  ];
  return { scene: root, animations };
}

export async function loadKinds() {
  const loader = new GLTFLoader();
  const out = {};
  await Promise.all(KINDS.map(async kind => {
    try {
      out[kind] = await loader.loadAsync(`assets/creatures/${kind}.glb`);
    } catch (e) {
      console.warn(`Sin modelo para ${kind}, uso cápsula`, e);
      out[kind] = placeholder();
    }
  }));
  return out;
}

class Creature {
  constructor(gltf, owner) {
    this.root = SkeletonUtils.clone(gltf.scene);
    this.owner = owner;
    this.materials = [];
    this.baseOpacity = 1; // la escriben el tracking (main.js) y la muerte (events.js)
    this.pass = 0;        // 0..1, "se deja atravesar" por la mano
    this.root.traverse(o => {
      if (o.isMesh) {
        o.material = makeHologramMaterial(SIDE_COLORS[owner]);
        o.frustumCulled = false; // el skinning mueve vértices fuera de la caja original
        this.materials.push(o.material);
      }
    });
    this.mixer = new THREE.AnimationMixer(this.root);
    this.actions = {};
    for (const clip of gltf.animations) {
      const name = clip.name;
      const a = this.mixer.clipAction(clip);
      if (!LOOPING.has(name)) { a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; }
      this.actions[name] = a;
    }
    this.current = null;
    this.play("idle");
  }

  // Devuelve una promesa que se resuelve cuando termina el clip (los loops, al terminar el fundido).
  play(name) {
    const next = this.actions[name];
    if (!next) {
      if (!warned.has(name)) { warned.add(name); console.warn(`Sin clip "${name}", sigo sin animar`); }
      return Promise.resolve();
    }
    next.reset().play();
    if (this.current && this.current !== next) this.current.crossFadeTo(next, FADE, false);
    this.current = next;
    if (LOOPING.has(name)) return new Promise(r => setTimeout(r, FADE * 1000));
    return new Promise(resolve => {
      // Respaldo por tiempo: si el clip se interrumpe o el mixer deja de actualizarse,
      // "finished" no llega nunca y la cola de eventos quedaría colgada para siempre.
      const timer = setTimeout(() => finish(), (next.getClip().duration + FADE) * 1000 + 500);
      const finish = () => {
        clearTimeout(timer);
        this.mixer.removeEventListener("finished", done);
        resolve();
      };
      const done = e => { if (e.action === next) finish(); };
      this.mixer.addEventListener("finished", done);
    });
  }

  // Gesto de victoria sin promesa: nadie lo espera. Si ya lo está haciendo, no lo reinicia
  // (win llega justo después del death que lo arrancó). Vuelve a idle solo si nadie lo pisó.
  celebrate() {
    const a = this.actions[WIN_CLIP];
    if (!a || this.current === a) return;
    this.play(WIN_CLIP).then(() => { if (this.current === a) this.play("idle"); });
  }

  face(x, y) {
    const d = boardToLocal(x, y).sub(this.root.position);
    if (d.lengthSq() > 1e-8) this.root.rotation.y = Math.atan2(d.x, d.z);
  }

  async walkTo(x, y) {
    const from = this.root.position.clone(), to = boardToLocal(x, y);
    const secs = Math.max(0.3, from.distanceTo(to) / WALK_SPEED);
    this.face(x, y);
    this.play("walk");
    await tween(secs, t => this.root.position.lerpVectors(from, to, t), stepTime);
    await this.play("idle");
  }

  setOpacity(o) { this.baseOpacity = o; this.applyOpacity(); }
  setPass(p) {
    this.pass = p;
    this.materials.forEach(m => { m.userData.pass.value = p; });
    this.applyOpacity();
  }
  applyOpacity() {
    const o = this.baseOpacity * (1 - 0.65 * this.pass);
    this.materials.forEach(m => { m.opacity = o; });
  }
  setFlash(f) { this.materials.forEach(m => { m.userData.flash.value = f; }); }
}

// clock en segundos; walkTo le pasa stepTime para que el desplazamiento salte junto con la pose.
export function tween(secs, step, clock = () => performance.now() / 1000) {
  return new Promise(resolve => {
    const t0 = clock();
    (function frame() {
      const t = Math.min(1, (clock() - t0) / secs);
      step(t);
      if (t < 1) requestAnimationFrame(frame); else resolve();
    })();
  });
}

export class Army {
  constructor(parent, models, spec) {
    this.parent = parent; this.models = models; this.spec = spec;
    this.byId = new Map();
  }

  get(id) { return this.byId.get(id); }

  // Pone cada pieza viva en su casilla (al conectar o reconectar, o si algo quedó desfasado).
  // removeDead = false mientras se animan eventos: la criatura muerta la saca el evento
  // death al terminar su animación (si se saca antes, su clip no termina nunca).
  sync(pieces, removeDead = true) {
    for (const p of pieces) {
      let c = this.byId.get(p.id);
      if (!p.alive) {
        if (c && removeDead) { this.parent.remove(c.root); this.byId.delete(p.id); }
        continue;
      }
      if (!c) {
        c = new Creature(this.models[p.kind], p.owner);
        this.byId.set(p.id, c);
        this.parent.add(c.root);
        // Hechas para el tablero A2 (escala 100); en uno impreso achicado, se achican igual.
        c.root.scale.multiplyScalar(this.spec.print_scale_measured / 100);
        const [x, y] = cellCenter(this.spec, p.cell);
        c.root.position.copy(boardToLocal(x, y));
        c.face(0, 0); // al empezar, todas miran al centro
      }
      c.cell = p.cell;
    }
  }

  // Corrige posiciones sin animar (solo cuando no hay eventos en curso).
  snap(pieces) {
    for (const p of pieces) {
      const c = this.byId.get(p.id);
      if (!c || !p.alive) continue;
      const [x, y] = cellCenter(this.spec, p.cell);
      c.root.position.copy(boardToLocal(x, y));
    }
  }

  // Todas las criaturas cambian de pose en el mismo cuadro, solo cuando el reloj de pasos avanza.
  update() {
    const t = stepTime();
    if (t === this.lastStep) return;
    const dt = t - (this.lastStep ?? t);
    this.lastStep = t;
    this.byId.forEach(c => c.mixer.update(dt));
  }
}

export { Creature };
