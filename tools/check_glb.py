"""Verifica que una criatura .glb cumpla el contrato de docs/assets_checklist.md.

    python tools/check_glb.py web/assets/creatures/bestia.glb [otro.glb ...]

Termina con código 1 si algo falla. Los mensajes están pensados para pegárselos
tal cual a la IA que opera Blender. Mide el modelo en el primer cuadro de `idle`
(la pose que se ve en el tablero), deformando las mallas con su esqueleto.
"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

CLIPS = ["idle", "walk", "attack", "hit", "die"]
MAX_BYTES = 5 * 1024 * 1024
HEIGHT_M = (0.05, 0.07)
BASE_HALF_M = 0.0125      # la base entra en un cuadrado de 25 x 25 mm centrado en el origen
ORIGIN_TOL_M = 0.005      # el punto más bajo tiene que estar a ±5 mm de y = 0
DRACO = "KHR_draco_mesh_compression"
COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path):
    data = Path(path).read_bytes()
    magic, version, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError("no es un .glb (glTF 2.0 binario)")
    gltf, binary, off = None, b"", 12
    while off < len(data):
        length, kind = struct.unpack_from("<II", data, off)
        chunk = data[off + 8:off + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        off += 8 + length
    return gltf, binary, len(data)


DTYPES = {5126: "<f4", 5121: "u1", 5123: "<u2", 5125: "<u4"}


def read_accessor(gltf, binary, index):
    """Accessor -> array (count, componentes) de floats. Respeta byteStride y normalized."""
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    dt, n = np.dtype(DTYPES[acc["componentType"]]), COMPONENTS[acc["type"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", dt.itemsize * n)
    raw = np.lib.stride_tricks.as_strided(
        np.frombuffer(binary, dt, offset=start, count=(acc["count"] - 1) * stride // dt.itemsize + n),
        shape=(acc["count"], n), strides=(stride, dt.itemsize))
    out = raw.astype(float)
    if acc.get("normalized"):
        out /= np.iinfo(dt).max
    return out


def local_matrix(node, override=None):
    if "matrix" in node and not override:
        return np.array(node["matrix"], dtype=float).reshape(4, 4, order="F")
    trs = {**node, **(override or {})}
    x, y, z, w = trs.get("rotation", [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R * np.array(trs.get("scale", [1, 1, 1]))
    M[:3, 3] = trs.get("translation", [0, 0, 0])
    return M


def clip_first_frame(gltf, binary, clip):
    """{nodo: {"translation"|"rotation"|"scale": valor}} en el primer cuadro del clip."""
    anim = next((a for a in gltf.get("animations", []) if a.get("name") == clip), None)
    pose = {}
    for ch in (anim or {}).get("channels", []):
        target, sampler = ch["target"], anim["samplers"][ch["sampler"]]
        if target.get("path") in ("translation", "rotation", "scale") and "output" in sampler:
            pose.setdefault(target["node"], {})[target["path"]] = read_accessor(gltf, binary, sampler["output"])[0].tolist()
    return pose


def world_matrices(gltf, pose=None):
    nodes, world, pose = gltf.get("nodes", []), {}, pose or {}

    def visit(i, parent):
        world[i] = parent @ local_matrix(nodes[i], pose.get(i))
        for c in nodes[i].get("children", []):
            visit(c, world[i])

    scene = gltf.get("scenes", [{}])[gltf.get("scene", 0)]
    for root in scene.get("nodes", []):
        visit(root, np.eye(4))
    return world


def bounds(gltf, binary, clip="idle"):
    """(min xyz, max xyz) en metros, en el primer cuadro de `clip` (o en reposo si
    no existe). Las mallas con esqueleto se deforman de verdad, vértice por
    vértice: la pose de bind suele ser con los brazos abiertos y no es la que se ve."""
    world, pts = world_matrices(gltf, clip_first_frame(gltf, binary, clip)), []
    for i, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node or i not in world:
            continue
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            attrs = prim["attributes"]
            if "skin" in node and "JOINTS_0" in attrs:
                skin = gltf["skins"][node["skin"]]
                ibm = (read_accessor(gltf, binary, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
                       if "inverseBindMatrices" in skin else np.tile(np.eye(4), (len(skin["joints"]), 1, 1)))
                J = np.array([world[j] for j in skin["joints"]]) @ ibm
                v = np.c_[read_accessor(gltf, binary, attrs["POSITION"]), np.ones(gltf["accessors"][attrs["POSITION"]]["count"])]
                joints = read_accessor(gltf, binary, attrs["JOINTS_0"]).astype(int)
                weights = read_accessor(gltf, binary, attrs["WEIGHTS_0"])
                skin_m = np.einsum("vk,vkab->vab", weights, J[joints])
                pts.extend(np.einsum("vab,vb->va", skin_m, v)[:, :3])
            else:
                acc = gltf["accessors"][attrs["POSITION"]]
                lo, hi = acc["min"], acc["max"]
                for corner in np.array(np.meshgrid(*zip(lo, hi))).reshape(3, -1).T:
                    pts.append((world[i] @ [*corner, 1])[:3])
    if not pts:
        return None
    pts = np.array(pts)
    return pts.min(axis=0), pts.max(axis=0)


def check(path):
    """-> lista de errores (vacía si cumple el contrato)."""
    try:
        gltf, binary, size = read_glb(path)
    except (OSError, ValueError, struct.error) as e:
        return [f"No se pudo leer el archivo: {e}"]
    errors = []
    if size >= MAX_BYTES:
        errors.append(f"Pesa {size / 1e6:.1f} MB; tiene que pesar menos de 5 MB (reducir texturas o polígonos).")
    if DRACO in gltf.get("extensionsUsed", []) + gltf.get("extensionsRequired", []):
        errors.append("Usa compresión Draco; exportar sin Draco.")

    anims = {a.get("name"): a for a in gltf.get("animations", [])}
    missing = [c for c in CLIPS if c not in anims]
    if missing:
        errors.append(f"Faltan los clips {missing}; hay {sorted(n for n in anims if n)}. "
                      f"Los nombres tienen que ser exactamente {CLIPS}.")
    empty = [c for c in CLIPS if c in anims and not anims[c].get("channels")]
    if empty:
        errors.append(f"Los clips {empty} existen pero no animan nada.")
    # Varias mallas (cuerpo, ojos) pueden tener su propio "skin" sobre el mismo
    # esqueleto. Lo que se cuenta son las raíces de esqueleto distintas.
    roots = {s.get("skeleton", min(s["joints"])) for s in gltf.get("skins", [])}
    if len(roots) > 1:
        errors.append(f"Tiene {len(roots)} esqueletos distintos; tiene que tener uno solo (o ninguno).")

    b = bounds(gltf, binary)
    if b is None:
        return errors + ["No tiene ninguna malla."]
    lo, hi = b
    height = hi[1] - lo[1]
    if not HEIGHT_M[0] <= height <= HEIGHT_M[1]:
        errors.append(f"Mide {height * 1000:.1f} mm de alto; tiene que medir entre 50 y 70 mm (+Y hacia arriba, 1 unidad = 1 m).")
    if abs(lo[1]) > ORIGIN_TOL_M:
        errors.append(f"El punto más bajo está en y = {lo[1] * 1000:.1f} mm; el origen tiene que estar en la base (y = 0).")
    over = max(abs(lo[0]), abs(hi[0]), abs(lo[2]), abs(hi[2]))
    if over > BASE_HALF_M:
        errors.append(f"La base mide {(hi[0] - lo[0]) * 1000:.0f} x {(hi[2] - lo[2]) * 1000:.0f} mm (X x Z) "
                      f"y llega a {over * 1000:.1f} mm del origen; tiene que entrar en un cuadrado de 25 x 25 mm "
                      "centrado en el origen. Hacer la criatura más compacta, no más chica.")
    return errors


def main(paths):
    failed = False
    for p in paths:
        errors = check(p)
        print(f"{'OK ' if not errors else 'MAL'} {p}")
        for e in errors:
            print(f"  - {e}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
