import numpy as np

from dejarik.protocol import decode_frame, encode_frame
from dejarik.recording import Recorder, read_dj
from dejarik.vision import to_view_matrix

POSE = {"ok": True, "T": [float(i) for i in range(16)], "n_markers": 12, "reproj_px": 0.4, "locked": False}
HAND = {"cell": 7, "pinch": False, "px": [10, 20]}


def test_frame_roundtrip():
    jpeg = b"\xff\xd8fake-jpeg\xff\xd9"
    header, out = decode_frame(encode_frame(3, 100, jpeg, POSE, [900, 900, 640, 360], [1280, 720], HAND))
    assert out == jpeg
    assert header == {"v": 1, "type": "frame", "frame_id": 3, "t": 100, "pose": POSE,
                      "K": [900, 900, 640, 360], "size": [1280, 720], "hand": HAND}


def test_debug_only_when_given():
    header, _ = decode_frame(encode_frame(0, 0, b"", POSE, [1, 1, 0, 0], [1, 1], HAND))
    assert "debug" not in header
    header, _ = decode_frame(encode_frame(0, 0, b"", POSE, [1, 1, 0, 0], [1, 1], HAND, debug={"ids": [1]}))
    assert header["debug"] == {"ids": [1]}


def test_dj_roundtrip(tmp_path):
    frames = [encode_frame(i, i * 33, bytes([i]) * 50, POSE, [1, 1, 0, 0], [1, 1], HAND) for i in range(3)]
    with Recorder(tmp_path / "s.dj") as rec:
        for f in frames:
            rec.write(f, 33)
    assert list(read_dj(tmp_path / "s.dj")) == [(33, f) for f in frames]


def test_view_matrix_of_identity_is_the_axis_flip():
    T = np.array(to_view_matrix([0, 0, 0], [0, 0, 0])).reshape(4, 4, order="F")
    assert np.allclose(T, np.diag([1, -1, -1, 1]))


def test_view_matrix_is_column_major():
    T = to_view_matrix([0, 0, 0], [1, 2, 3])
    assert T[12:15] == [1, -2, -3]  # la traslación va en los elementos 12–14 (Three.js)


def test_parse_client_filters():
    from dejarik.protocol import parse_client
    assert parse_client('{"v":1,"type":"click","x":0.1,"y":-0.2}')["x"] == 0.1
    assert parse_client('{"v":2,"type":"click","x":0,"y":0}') is None
    assert parse_client('{"v":1,"type":"hack"}') is None
    assert parse_client('{"v":1,"type":"click","x":"a","y":0}') is None
    assert parse_client('{"v":1,"type":"key","key":"format_c"}') is None
    assert parse_client("no es json") is None
    assert parse_client('{"v":1,"type":"anim_done","id":3}')["id"] == 3


def test_state_msg_animating_and_legal():
    import json
    from dejarik.game import apply, new_game
    from dejarik.protocol import state_msg
    s, _ = apply(new_game(0), ("tap", 13))
    m = json.loads(state_msg(s, animating=True))
    assert m["phase"] == "animating" and m["selected"] == 2 and m["legal"] == [0, 1, 2, 12]
    assert m["pieces"][0] == {"id": 0, "owner": 0, "kind": "guardian", "cell": 23, "hp": 3, "alive": True}
