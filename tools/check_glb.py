"""Verifica que una criatura .glb cumpla el contrato de docs/assets_checklist.md.

    python tools/check_glb.py web/assets/creatures/bestia.glb [otro.glb ...]

Termina con código 1 si algo falla. Los mensajes están pensados para pegárselos
tal cual a la IA que opera Blender. Mide el modelo en reposo (sin animar),
transformando las cajas de cada malla por la jerarquía de nodos.
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
COMPONENTS = {"SCALAR": 1, "VEC3": 3, "MAT4": 16}


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


def read_floats(gltf, binary, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    n = COMPONENTS[acc["type"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return np.frombuffer(binary, "<f4", acc["count"] * n, start).reshape(acc["count"], n)


def local_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4, order="F")
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = R * np.array(node.get("scale", [1, 1, 1]))
    M[:3, 3] = node.get("translation", [0, 0, 0])
    return M


def world_matrices(gltf):
    nodes, world = gltf.get("nodes", []), {}

    def visit(i, parent):
        world[i] = parent @ local_matrix(nodes[i])
        for c in nodes[i].get("children", []):
            visit(c, world[i])

    scene = gltf.get("scenes", [{}])[gltf.get("scene", 0)]
    for root in scene.get("nodes", []):
        visit(root, np.eye(4))
    return world


def bounds(gltf, binary):
    """(min xyz, max xyz) del modelo en reposo, en metros."""
    world, pts = world_matrices(gltf), []
    for i, node in enumerate(gltf.get("nodes", [])):
        if "mesh" not in node or i not in world:
            continue
        M = world[i]
        if "skin" in node:  # en reposo: mundo del primer hueso x su inverse bind matrix
            skin = gltf["skins"][node["skin"]]
            M = world[skin["joints"][0]]
            if "inverseBindMatrices" in skin:
                M = M @ read_floats(gltf, binary, skin["inverseBindMatrices"])[0].reshape(4, 4, order="F")
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            lo, hi = acc["min"], acc["max"]
            for cx in (lo[0], hi[0]):
                for cy in (lo[1], hi[1]):
                    for cz in (lo[2], hi[2]):
                        pts.append((M @ [cx, cy, cz, 1])[:3])
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
    if len(gltf.get("skins", [])) > 1:
        errors.append(f"Tiene {len(gltf['skins'])} esqueletos; tiene que tener uno solo (o ninguno).")

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
