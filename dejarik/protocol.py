"""Protocolo WebSocket v1 (ver docs/protocol.md)."""
import json
import struct

VERSION = 1


def encode_frame(frame_id, t, jpeg_bytes, pose, K, size, hand, debug=None):
    """[uint32 BE: largo N del header][N bytes: header JSON UTF-8][JPEG]."""
    header = {"v": VERSION, "type": "frame", "frame_id": frame_id, "t": t,
              "pose": pose, "K": list(K), "size": list(size), "hand": hand}
    if debug is not None:
        header["debug"] = debug
    raw = json.dumps(header, separators=(",", ":")).encode("utf-8")
    return struct.pack(">I", len(raw)) + raw + bytes(jpeg_bytes)


def decode_frame(data):
    """-> (header dict, jpeg bytes)."""
    (n,) = struct.unpack_from(">I", data, 0)
    header = json.loads(data[4:4 + n].decode("utf-8"))
    return header, bytes(data[4 + n:])


def _text(obj):
    return json.dumps({"v": VERSION, **obj}, separators=(",", ":"))


def state_msg(state, animating=False):
    """phase "animating" mientras transport tiene eventos sin anim_done."""
    from dejarik.game import legal_cells
    return _text({"type": "state", "turn": state.turn, "phase": "animating" if animating else state.phase,
                  "pieces": [p.__dict__ for p in state.pieces], "selected": state.selected,
                  "legal": legal_cells(state, state.selected) if state.selected is not None else [],
                  "winner": state.winner})


def events_msg(events):
    return _text({"type": "events", "events": events})


def hello_msg(you, mode, remote=None, role="host"):
    """you: el bando del que recibe (0 azul, 1 rojo). role: "host" o "remote"."""
    return _text({"type": "hello", "you": you, "mode": mode, "remote": remote, "role": role})


def denied_msg(reason):
    return _text({"type": "denied", "reason": reason})


CLIENT_TYPES = {"click": ("x", "y"), "anim_done": ("id",), "key": ("key",), "frame_ack": ("frame_id",)}
KEYS = {"reset", "debug", "lock", "mode"}


def parse_client(text):
    """-> dict validado, o None si no es v1, el tipo es desconocido o faltan campos."""
    try:
        msg = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(msg, dict) or msg.get("v") != VERSION or msg.get("type") not in CLIENT_TYPES:
        return None
    fields = CLIENT_TYPES[msg["type"]]
    if any(f not in msg for f in fields):
        return None
    if msg["type"] == "click" and not all(isinstance(msg[f], (int, float)) for f in fields):
        return None
    if msg["type"] == "key" and msg["key"] not in KEYS:
        return None
    return msg
