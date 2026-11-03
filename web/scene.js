// Escena: video de fondo, cámara virtual con la K real, y el tablero anclado a la pose.
// Convención (docs/protocol.md): `board` recibe T (ya en ejes de Three.js) y está en
// el sistema del tablero (Z hacia arriba). `boardY` lo rota para que los glTF (Y hacia
// arriba) queden parados sobre el tablero.
import * as THREE from "three";

const NEAR = 0.01, FAR = 10;
// Brillo del video de fondo (1 = original). Oscurecerlo hace resaltar los hologramas.
export const BACKGROUND_DIM = 0.6;
const BLUE = new THREE.Color(0x4cc9ff);

export function cellCenter(spec, cell) {
  if (cell === 0) return [0, 0];
  const { r0, r1, r2 } = spec.radii_m;
  const r = cell <= 12 ? (r0 + r1) / 2 : (r1 + r2) / 2;
  const a = THREE.MathUtils.degToRad(spec.sector_offset_deg + (((cell - 1) % 12)) * 30);
  return [r * Math.cos(a), r * Math.sin(a)];
}

// Punto del tablero (x, y) -> coordenadas locales de boardY (donde viven las criaturas).
export function boardToLocal(x, y) {
  return new THREE.Vector3(x, 0, -y);
}

export function createScene(canvas, spec) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.autoClear = false;
  renderer.setPixelRatio(window.devicePixelRatio);

  // Fondo: un quad a pantalla completa con la textura del cuadro.
  const bgTexture = new THREE.Texture();
  bgTexture.colorSpace = THREE.SRGBColorSpace;
  bgTexture.flipY = false; // el ImageBitmap ya viene volteado (imageOrientation: "flipY")
  const bgScene = new THREE.Scene();
  const bgCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  bgScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2),
    new THREE.MeshBasicMaterial({ map: bgTexture, depthTest: false, depthWrite: false,
      color: new THREE.Color(BACKGROUND_DIM, BACKGROUND_DIM, BACKGROUND_DIM) })));
  let lastBitmap = null;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera();
  camera.matrixAutoUpdate = false; // fija en el origen, mirando a -Z (cámara de OpenCV con y/z invertidos)

  const board = new THREE.Group();
  board.matrixAutoUpdate = false;
  scene.add(board);
  const boardY = new THREE.Group();
  boardY.rotation.x = Math.PI / 2; // +Y del glTF -> +Z del tablero
  board.add(boardY);

  const { r0, r1, r2 } = spec.radii_m;

  // Disco que solo escribe profundidad: tapa lo que quedaría debajo del tablero.
  const occluder = new THREE.Mesh(new THREE.CircleGeometry(r2 * 1.05, 96),
    new THREE.MeshBasicMaterial({ colorWrite: false }));
  occluder.renderOrder = -1;
  board.add(occluder);

  // Anillos y divisiones, en azul holograma.
  const lineMat = new THREE.LineBasicMaterial({ color: BLUE, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false });
  const pts = [];
  for (const r of [r0, r1, r2]) {
    for (let i = 0; i < 128; i++) {
      const a0 = (i / 128) * Math.PI * 2, a1 = ((i + 1) / 128) * Math.PI * 2;
      pts.push(r * Math.cos(a0), r * Math.sin(a0), 0.0005, r * Math.cos(a1), r * Math.sin(a1), 0.0005);
    }
  }
  for (let k = 0; k < 12; k++) {
    const a = THREE.MathUtils.degToRad(spec.sector_offset_deg + k * 30 + 15);
    pts.push(r0 * Math.cos(a), r0 * Math.sin(a), 0.0005, r2 * Math.cos(a), r2 * Math.sin(a), 0.0005);
  }
  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  board.add(new THREE.LineSegments(lineGeo, lineMat));

  // Una pieza de superficie por casilla, para iluminar las legales y la del dedo.
  const cells = [];
  for (let c = 0; c < 25; c++) {
    let geo;
    if (c === 0) geo = new THREE.CircleGeometry(r0 * 0.97, 48);
    else {
      const [inner, outer] = c <= 12 ? [r0, r1] : [r1, r2];
      const start = THREE.MathUtils.degToRad(spec.sector_offset_deg + ((c - 1) % 12) * 30 - 15);
      geo = new THREE.RingGeometry(inner * 1.01, outer * 0.99, 12, 1, start + 0.01, THREE.MathUtils.degToRad(30) - 0.02);
    }
    const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      color: BLUE, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
    mesh.position.z = 0.0003;
    board.add(mesh);
    cells.push(mesh);
  }

  let K = null, size = null;
  const clock = new THREE.Clock();

  function setProjection(k, sz) {
    const [fx, fy, cx, cy] = k, [w, h] = sz;
    camera.projectionMatrix.set(
      2 * fx / w, 0, 1 - 2 * cx / w, 0,
      0, 2 * fy / h, 2 * cy / h - 1, 0,
      0, 0, -(FAR + NEAR) / (FAR - NEAR), -2 * FAR * NEAR / (FAR - NEAR),
      0, 0, -1, 0);
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
  }

  return {
    renderer, scene, camera, board, boardY,

    get size() { return size; },

    async setFrame(header, jpegBlob) {
      if (!K || header.K.join() !== K.join() || header.size.join() !== size.join()) {
        K = header.K; size = header.size;
        setProjection(K, size);
      }
      const bitmap = await createImageBitmap(jpegBlob, { imageOrientation: "flipY" });
      bgTexture.image = bitmap;
      bgTexture.needsUpdate = true;
      lastBitmap?.close?.();
      lastBitmap = bitmap;
      if (header.pose.ok) {
        board.matrix.fromArray(header.pose.T);
        board.matrixWorldNeedsUpdate = true;
      }
    },

    // legal: casillas iluminadas; hover: la casilla bajo el dedo (o null).
    highlight(legal = [], hover = null, selectedCell = null) {
      const t = clock.getElapsedTime();
      cells.forEach((m, c) => {
        let o = 0;
        if (legal.includes(c)) o = 0.18 + 0.08 * Math.sin(t * 4);
        if (c === selectedCell) o = 0.35;
        if (c === hover) o = Math.max(o, 0.45);
        m.material.opacity = o;
      });
    },

    // Clic en el canvas (coordenadas CSS) -> punto (x, y) del tablero, o null.
    boardPointFromClick(clientX, clientY) {
      if (!K) return null;
      const rect = canvas.getBoundingClientRect();
      const ndc = new THREE.Vector3(((clientX - rect.left) / rect.width) * 2 - 1,
        -((clientY - rect.top) / rect.height) * 2 + 1, 0.5);
      const dir = ndc.unproject(camera).normalize(); // cámara en el origen: el punto ya es una dirección
      const toBoard = board.matrix.clone().invert();
      const o = new THREE.Vector3(0, 0, 0).applyMatrix4(toBoard);
      const d = dir.transformDirection(toBoard);
      if (Math.abs(d.z) < 1e-6) return null;
      const s = -o.z / d.z;
      if (s <= 0) return null;
      return { x: o.x + s * d.x, y: o.y + s * d.y };
    },

    render() {
      renderer.clear();
      renderer.render(bgScene, bgCamera);
      renderer.clearDepth();
      renderer.render(scene, camera);
    },
  };
}
