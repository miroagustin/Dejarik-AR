"""Reglas (docs/rules.md). Python puro, sin cv2 ni I/O: apply(state, action) -> (state, events)."""
import copy
import json
import random
from collections import deque
from dataclasses import asdict, dataclass, field

from dejarik.board import load_spec

# Se ajustan después de los ensayos (objetivo G2: partida de 6 a 8 minutos).
KINDS = {
    "guardian": {"atk": 1, "def": 3, "hp": 3, "mov": 1},
    "bestia": {"atk": 3, "def": 1, "hp": 2, "mov": 1},
    "acechador": {"atk": 2, "def": 1, "hp": 2, "mov": 2},
    "soldado": {"atk": 2, "def": 2, "hp": 2, "mov": 1},
}
ORDER = ["guardian", "bestia", "acechador", "soldado"]
INITIAL = {0: [23, 24, 13, 14], 1: [17, 18, 19, 20]}

ADJ = {int(k): v for k, v in load_spec()["adjacency"].items()}


@dataclass
class Piece:
    id: int
    owner: int
    kind: str
    cell: int
    hp: int
    alive: bool = True


@dataclass
class State:
    turn: int = 0
    phase: str = "select"  # select | target | over
    pieces: list = field(default_factory=list)
    selected: int | None = None
    winner: int | None = None
    rng_state: tuple = None
    next_event_id: int = 1
    seed: int = 0


def new_game(seed=0):
    pieces = [Piece(owner * 4 + i, owner, kind, INITIAL[owner][i], KINDS[kind]["hp"])
              for owner in (0, 1) for i, kind in enumerate(ORDER)]
    return State(pieces=pieces, rng_state=random.Random(seed).getstate(), seed=seed)


def piece_at(state, cell):
    return next((p for p in state.pieces if p.alive and p.cell == cell), None)


def legal_targets(state, piece_id):
    """{"moves": casillas vacías a <= MOV pasos sin atravesar ocupadas, "attacks": rivales adyacentes}."""
    p = state.pieces[piece_id]
    if not p.alive:
        return {"moves": [], "attacks": []}
    busy = {q.cell for q in state.pieces if q.alive}
    dist, todo = {p.cell: 0}, deque([p.cell])
    while todo:
        c = todo.popleft()
        if dist[c] == KINDS[p.kind]["mov"]:
            continue
        for n in ADJ[c]:
            if n not in dist and n not in busy:
                dist[n] = dist[c] + 1
                todo.append(n)
    moves = sorted(c for c in dist if c != p.cell)
    attacks = sorted(n for n in ADJ[p.cell] if (q := piece_at(state, n)) and q.owner != p.owner)
    return {"moves": moves, "attacks": attacks}


def legal_cells(state, piece_id):
    t = legal_targets(state, piece_id)
    return sorted(t["moves"] + t["attacks"])


def has_action(state, owner):
    return any(legal_cells(state, p.id) for p in state.pieces if p.alive and p.owner == owner)


def apply(state, action):
    """-> (nuevo State, lista de eventos). No modifica `state`."""
    if action[0] == "reset":
        return new_game(state.seed + 1), []
    cell = action[1]
    s = copy.deepcopy(state)
    if s.phase == "over":
        return s, []
    here = piece_at(s, cell) if cell is not None else None
    if s.phase == "select":
        if here and here.owner == s.turn:
            s.selected, s.phase = here.id, "target"
        return s, []
    # target
    if here and here.owner == s.turn:
        s.selected = here.id
        return s, []
    t = legal_targets(s, s.selected)
    me = s.pieces[s.selected]
    events = []

    def ev(kind, **kw):
        events.append({"id": s.next_event_id, "kind": kind, **kw})
        s.next_event_id += 1

    if cell in t["moves"]:
        ev("move", piece=me.id, **{"from": me.cell}, to=cell)
        me.cell = cell
    elif cell in t["attacks"]:
        rng = random.Random()
        rng.setstate(s.rng_state)
        a, d = rng.randint(1, 6), rng.randint(1, 6)
        s.rng_state = rng.getstate()
        outcome = "hit" if a + KINDS[me.kind]["atk"] > d + KINDS[here.kind]["def"] else \
            "counter" if a + KINDS[me.kind]["atk"] < d + KINDS[here.kind]["def"] else "tie"
        ev("attack", piece=me.id, to=cell, result={"atk_roll": a, "def_roll": d, "outcome": outcome})
        loser = {"hit": here, "counter": me}.get(outcome)
        if loser:
            loser.hp -= 1
            ev("hit", piece=loser.id, result={"hp": loser.hp})
            if loser.hp == 0:
                loser.alive = False
                ev("death", piece=loser.id, **{"from": loser.cell})
    else:
        s.selected, s.phase = None, "select"
        return s, []

    s.selected, s.phase = None, "select"
    for owner in (0, 1):
        if not any(p.alive and p.owner == owner for p in s.pieces):
            s.winner, s.phase = 1 - owner, "over"
            ev("win", result={"winner": s.winner})
            return s, events
    s.turn = 1 - s.turn
    if not has_action(s, s.turn):  # rodeado sin salida (raro con pocas piezas): pierde el turno
        s.turn = 1 - s.turn
    ev("turn", result={"turn": s.turn})
    return s, events


def to_json(state):
    d = asdict(state)
    v, internal, gauss = state.rng_state
    d["rng_state"] = [v, list(internal), gauss]
    return json.dumps(d)


def from_json(text):
    d = json.loads(text)
    v, internal, gauss = d["rng_state"]
    d["rng_state"] = (v, tuple(internal), gauss)
    d["pieces"] = [Piece(**p) for p in d["pieces"]]
    return State(**d)
