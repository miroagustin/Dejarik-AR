"""Adapta un monstruo animado (Quaternius y similares) al contrato de
docs/assets_checklist.md sin abrir Blender:

    python tools/adapt_glb.py origen.glb web/assets/creatures/<kind>.glb

- renombra los clips a idle/walk/attack/hit/die (ver CLIP_NAMES) y conserva el
  resto en minúscula;
- lo escala para que entre en el círculo de 44 mm y mida como mucho 70 mm;
- lo apoya en y = 0.
No toca la geometría ni las animaciones: agrega un nodo raíz con escala y
traslación. Después corre check_glb sobre el resultado.
"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_glb import BASE_RADIUS_M, HEIGHT_M, check, posed_points, read_glb  # noqa: E402

# Nombre nuestro -> nombres posibles en el origen (lo que va después de "Armature|"), en orden de preferencia.
CLIP_NAMES = {
    "idle": ["Idle", "Flying_Idle", "Alien_Idle"],
    "walk": ["Walk", "Fast_Flying", "Alien_Walk"],
    "attack": ["Punch", "Bite_Front", "Headbutt", "Alien_Punch"],
    "hit": ["HitReact", "HitRecieve"],
    "die": ["Death", "Alien_Death"],
}
MARGIN = 0.98


def rename_clips(gltf):
    """Renombra los clips del contrato y conserva el resto en minúscula. -> clips que faltan."""
    anims = gltf.get("animations", [])
    by_short = {a["name"].split("|")[-1]: a for a in anims}
    kept, missing = [], []
    for ours, candidates in CLIP_NAMES.items():
        src = next((by_short[c] for c in candidates if c in by_short), None)
        if src is None:
            missing.append(ours)
            continue
        src["name"] = ours
        kept.append(src)
    names, used = {a["name"] for a in kept}, {id(a) for a in kept}
    for a in anims:  # los que sobran, en el orden de origen; si el nombre ya está, se saltea
        short = a["name"].split("|")[-1].lower()
        if id(a) not in used and short not in names:
            a["name"] = short
            kept.append(a)
            names.add(short)
    gltf["animations"] = kept
    return missing


def write_glb(path, gltf, binary):
    raw = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    body = struct.pack("<II", len(raw), 0x4E4F534A) + raw
    if binary:
        body += struct.pack("<II", len(binary), 0x004E4942) + binary
    Path(path).write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)


def adapt(src, dst):
    gltf, binary, _ = read_glb(src)
    missing = rename_clips(gltf)
    pts = posed_points(gltf, binary, "idle")
    radius = float(np.hypot(pts[:, 0], pts[:, 2]).max())
    height = float(pts[:, 1].max() - pts[:, 1].min())
    s = MARGIN * min(BASE_RADIUS_M / radius, HEIGHT_M[1] / height)

    scene = gltf["scenes"][gltf.get("scene", 0)]
    gltf["nodes"].append({"name": "dejarik_root", "children": scene["nodes"],
                          "scale": [s, s, s], "translation": [0.0, -float(pts[:, 1].min()) * s, 0.0]})
    scene["nodes"] = [len(gltf["nodes"]) - 1]
    write_glb(dst, gltf, binary)
    return s * height, missing


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    h, missing = adapt(sys.argv[1], sys.argv[2])
    print(f"-> {sys.argv[2]}: {h * 1000:.0f} mm de alto")
    if missing:
        print(f"Faltan clips que no tiene el original: {missing}. Hay que agregarlos en Blender.")
    errors = check(sys.argv[2])
    for e in errors:
        print(f"  - {e}")
    sys.exit(1 if errors else 0)
