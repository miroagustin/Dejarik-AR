"""Rival automático (modo cpu). Función pura: choose(state) -> [("tap", pieza), ("tap", destino)].

Pone un puntaje a cada acción legal y elige la mejor; los empates se rompen por el
menor (piece_id, casilla), así que es determinista y no usa el RNG.
"""
from collections import deque
from functools import lru_cache

from dejarik.game import ADJ, KINDS, legal_targets, piece_at

W_HIT = 10            # × probabilidad de ganar la tirada
W_FINISH = 15         # el defensor tiene 1 HP
W_COUNTER_RISK = 6    # × probabilidad de contragolpe, si el atacante tiene 1 HP
W_APPROACH = 2        # × pasos que se acerca al rival más cercano
W_BESTIA_RISK = 1     # destino junto a una bestia rival, con 1 HP (con 4, dos bestias de 1 HP se esquivan para siempre)


@lru_cache(maxsize=None)
def win_prob(atk, dfn):
    """-> (p_hit, p_counter) recorriendo las 36 combinaciones de 1d6 contra 1d6."""
    hit = sum(a + atk > d + dfn for a in range(1, 7) for d in range(1, 7))
    counter = sum(a + atk < d + dfn for a in range(1, 7) for d in range(1, 7))
    return hit / 36, counter / 36


@lru_cache(maxsize=None)
def _dist_from(cell):
    """Distancias en el grafo de adyacencias, sin mirar las casillas ocupadas."""
    dist, todo = {cell: 0}, deque([cell])
    while todo:
        c = todo.popleft()
        for n in ADJ[c]:
            if n not in dist:
                dist[n] = dist[c] + 1
                todo.append(n)
    return dist


def score(state, piece, kind, cell):
    """kind: "attack" o "move"."""
    st = KINDS[piece.kind]
    if kind == "attack":
        target = piece_at(state, cell)
        p_hit, p_counter = win_prob(st["atk"], KINDS[target.kind]["def"])
        s = p_hit * W_HIT
        if target.hp == 1:
            s += W_FINISH
        if piece.hp == 1:
            s -= p_counter * W_COUNTER_RISK
        return s
    rivals = [p.cell for p in state.pieces if p.alive and p.owner != piece.owner]
    before = min(_dist_from(piece.cell)[r] for r in rivals)
    after = min(_dist_from(cell)[r] for r in rivals)
    s = (before - after) * W_APPROACH
    if piece.hp == 1 and any((q := piece_at(state, n)) and q.owner != piece.owner and q.kind == "bestia"
                             for n in ADJ[cell]):
        s -= W_BESTIA_RISK
    return s


def choose(state):
    best = None
    for p in state.pieces:
        if not (p.alive and p.owner == state.turn):
            continue
        t = legal_targets(state, p.id)
        for kind, cells in (("attack", t["attacks"]), ("move", t["moves"])):
            for c in cells:
                key = (-score(state, p, kind, c), p.id, c)
                if best is None or key < best:
                    best = key
    if best is None:
        return []
    _, pid, cell = best
    return [("tap", state.pieces[pid].cell), ("tap", cell)]
