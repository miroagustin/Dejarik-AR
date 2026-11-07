import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from check_glb import CLIPS, check  # noqa: E402


def make_glb(path, size_mm=(20, 60, 20), node=None, clips=CLIPS, extensions=()):
    """Un .glb mínimo: una caja (solo el accessor con min/max) y clips vacíos de datos."""
    sx, sy, sz = (v / 1000 for v in size_mm)
    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, **(node or {})}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [{"componentType": 5126, "count": 2, "type": "VEC3",
                       "min": [-sx / 2, 0, -sz / 2], "max": [sx / 2, sy, sz / 2]}],
        "animations": [{"name": c, "channels": [{"sampler": 0, "target": {"node": 0, "path": "scale"}}],
                        "samplers": [{}]} for c in clips],
    }
    if extensions:
        gltf["extensionsUsed"] = list(extensions)
    raw = json.dumps(gltf).encode()
    raw += b" " * (-len(raw) % 4)
    body = struct.pack("<II", len(raw), 0x4E4F534A) + raw
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body)
    return path


def test_valid_creature_passes(tmp_path):
    assert check(make_glb(tmp_path / "ok.glb")) == []


def test_missing_clip_is_reported(tmp_path):
    errors = check(make_glb(tmp_path / "a.glb", clips=["idle", "Walk", "attack", "hit", "die"]))
    assert len(errors) == 1 and "walk" in errors[0]


def test_wide_base_fails_and_suggests_the_scale(tmp_path):
    # caja de 40 x 40: las esquinas quedan a 28,3 mm del origen (> 22 mm)
    errors = check(make_glb(tmp_path / "a.glb", size_mm=(40, 60, 40)))
    assert len(errors) == 1 and "44 mm" in errors[0] and "0.778" in errors[0]


def test_short_creature_is_fine_down_to_30_mm(tmp_path):
    assert check(make_glb(tmp_path / "a.glb", size_mm=(20, 32, 20))) == []
    assert any("30 y 70" in e for e in check(make_glb(tmp_path / "b.glb", size_mm=(20, 25, 20))))


def test_fbx_scale_is_caught_through_node_transform(tmp_path):
    # la caja mide 6 m sin escalar; con la escala 0,01 del nodo queda en 60 mm
    ok = make_glb(tmp_path / "ok.glb", size_mm=(2000, 6000, 2000), node={"scale": [0.01, 0.01, 0.01]})
    assert check(ok) == []
    bad = make_glb(tmp_path / "bad.glb", size_mm=(2000, 6000, 2000))
    assert any("alto" in e for e in check(bad))


def test_origin_must_be_at_the_base(tmp_path):
    errors = check(make_glb(tmp_path / "a.glb", node={"translation": [0, 0.03, 0]}))
    assert any("base" in e for e in errors)


def test_draco_is_rejected(tmp_path):
    errors = check(make_glb(tmp_path / "a.glb", extensions=["KHR_draco_mesh_compression"]))
    assert any("Draco" in e for e in errors)


def test_adapt_renames_scales_and_grounds(tmp_path):
    from adapt_glb import adapt
    from check_glb import posed_points, read_glb

    src = make_glb(tmp_path / "src.glb", size_mm=(600, 1500, 600), node={"translation": [0, 3, 0]},
                   clips=["Armature|Idle", "Armature|Walk", "Armature|Bite_Front", "Armature|HitRecieve",
                          "Armature|Death", "Armature|Dance"])
    height, missing = adapt(src, tmp_path / "out.glb")
    assert missing == []
    assert check(tmp_path / "out.glb") == []
    gltf, binary, _ = read_glb(tmp_path / "out.glb")
    assert [a["name"] for a in gltf["animations"]] == CLIPS + ["dance"]  # el resto se conserva
    pts = posed_points(gltf, binary)
    assert abs(pts[:, 1].min()) < 1e-6
    assert 0.030 <= height <= 0.070


def test_adapt_keeps_extra_clips(tmp_path):
    from adapt_glb import adapt
    from check_glb import read_glb

    src = make_glb(tmp_path / "src.glb", clips=["A|Idle", "A|Walk", "A|Punch", "A|HitReact", "A|Death",
                                                "A|Wave", "A|Yes"])
    adapt(src, tmp_path / "out.glb")
    gltf, _, _ = read_glb(tmp_path / "out.glb")
    assert [a["name"] for a in gltf["animations"]] == CLIPS + ["wave", "yes"]
    assert check(tmp_path / "out.glb") == []


def test_adapt_reports_missing_clip(tmp_path):
    from adapt_glb import adapt

    src = make_glb(tmp_path / "src.glb", clips=["A|Idle", "A|Walk", "A|Punch", "A|Death"])
    _, missing = adapt(src, tmp_path / "out.glb")
    assert missing == ["hit"]
