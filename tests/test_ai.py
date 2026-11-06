import random
import statistics

from dejarik.ai import choose, win_prob
from dejarik.game import apply, legal_targets, new_game


def test_win_prob_by_hand():
    # 1d6+3 vs 1d6+1: gana si a - d > -2. Pierde con d - a >= 3: (1,4)(1,5)(1,6)(2,5)(2,6)(3,6) = 6;
    # empata con d - a = 2: 4 casos. Gana 26.
    assert win_prob(3, 1) == (26 / 36, 6 / 36)


def test_attacks_weak_adjacent():
    s = new_game(0)
    s.turn = 1
    s.pieces[1].cell, s.pieces[1].hp = 6, 1   # bestia azul con 1 HP junto a la bestia roja (18 -> 6)
    assert choose(s) == [("tap", 18), ("tap", 6)]


def test_approaches_when_nothing_near():
    s = new_game(0)
    s.turn = 1
    taps = choose(s)
    p = next(q for q in s.pieces if q.cell == taps[0][1])
    assert taps[1][1] in legal_targets(s, p.id)["moves"]


def play(seed, players):
    rng = random.Random(seed)
    s, n = new_game(seed), 0
    while s.phase != "over" and n < 2000:
        if players[s.turn] == "ai":
            taps = choose(s)
        else:
            own = [p for p in s.pieces if p.alive and p.owner == s.turn]
            opts = [(p.cell, c) for p in own for c in sum(legal_targets(s, p.id).values(), [])]
            a, b = rng.choice(opts)
            taps = [("tap", a), ("tap", b)]
        for t in taps:
            s, _ = apply(s, t)
        n += 1
    return s, n


def test_choose_always_legal():
    rng = random.Random(1)
    for seed in range(200):
        s = new_game(seed)
        for _ in range(rng.randint(0, 30)):
            if s.phase == "over":
                break
            for t in choose(s):
                s, _ = apply(s, t)
        if s.phase == "over":
            continue
        taps = choose(s)
        s1, _ = apply(s, taps[0])
        assert s1.phase == "target"
        _, ev = apply(s1, taps[1])
        assert ev, "la segunda acción tiene que hacer algo"


def test_ai_vs_ai_finishes():
    turns = [play(seed, {0: "ai", 1: "ai"})[1] for seed in range(200)]
    print(f"\nIA vs IA: mediana {statistics.median(turns)} turnos, máx {max(turns)}")
    assert max(turns) < 2000


def test_ai_beats_random():
    # El diseño pedía > 80%; con esta heurística y estos dados da ~60% (medido),
    # y se aceptó así. El test cuida que no empeore.
    wins = sum(play(seed, {0: "rand", 1: "ai"})[0].winner == 1 for seed in range(200))
    assert wins > 110, wins
