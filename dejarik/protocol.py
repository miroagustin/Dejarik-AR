"""Protocolo WebSocket v1 (ver docs/protocol.md).

Días 1–2: solo el mensaje binario de cuadro. state/events/hello/denied y
parse_client llegan en los días 3–5.
"""
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
