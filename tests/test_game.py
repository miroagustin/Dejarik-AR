import random

from dejarik.game import KINDS, apply, from_json, legal_targets, new_game, to_json


def tap(s, cell):
    return apply(s, ("tap", cell))


def test_initial_position():
    s = new_game(0)
    assert [(p.id, p.owner, p.kind, p.cell, p.hp) for p in s.pieces] == [
        (0, 0, "guardian", 23, 3), (1, 0, "bestia", 24, 2), (2, 0, "acechador", 13, 2), (3, 0, "soldado", 14, 2),
        (4, 1, "guardian", 17, 3), (5, 1, "bestia", 18, 2), (6, 1, "acechador", 19, 2), (7, 1, "soldado", 20, 2)]
    assert s.turn == 0 and s.phase == "select"


def test_mov2_does_not_pass_through_occupied():
    s = new_game(0)
    # acechador (13, MOV 2): vecinas 14 (ocupada), 24 (ocupada), 1. Por 1 llega a 0, 2, 12.
    assert legal_targets(s, 2)["moves"] == [0, 1, 2, 12]
    s.pieces[3].cell, s.pieces[0].cell = 1, 14  # 1, 14 y 24 ocupadas: no puede salir
    assert legal_targets(s, 2)["moves"] == []


def test_attack_only_adjacent():
    s = new_game(0)
    assert legal_targets(s, 2)["attacks"] == []
    s.pieces[6].cell = 1  # acechador rival al lado
    assert legal_targets(s, 2)["attacks"] == [1]


def find_seed(outcome):
    for seed in range(100):
        s = new_game(seed)
        s.pieces[5].cell = 12  # bestia roja junto a la bestia azul (24)
        s, _ = tap(s, 24)
        s2, ev = tap(s, 12)
        if ev[0]["result"]["outcome"] == outcome:
            return s, s2, ev
    raise AssertionError(outcome)


def test_combat_outcomes():
    for outcome in ("hit", "counter", "tie"):
        s, s2, ev = find_seed(outcome)
        r = ev[0]["result"]
        a, d = r["atk_roll"] + KINDS["bestia"]["atk"], r["def_roll"] + KINDS["bestia"]["def"]
        assert (a > d, a < d, a == d)[("hit", "counter", "tie").index(outcome)]
        kinds = [e["kind"] for e in ev]
        if outcome == "tie":
            assert kinds == ["attack", "turn"]
        else:
            assert kinds == ["attack", "hit", "turn"]
            loser = 5 if outcome == "hit" else 1
            assert s2.pieces[loser].hp == 1 and ev[1]["piece"] == loser
        assert s2.pieces[1].cell == 24  # el atacante no se mueve


def test_same_seed_same_rolls():
    _, a, ea = find_seed("hit")
    _, b, eb = find_seed("hit")
    assert ea == eb and to_json(a) == to_json(b)


def test_death_and_win():
    s = new_game(0)
    for p in s.pieces[5:]:
        p.alive = False
    s.pieces[4].cell, s.pieces[4].hp = 12, 1  # último rival, con 1 HP, junto a la bestia
    for seed in range(100):
        t = new_game(seed)
        t.pieces, t.turn = s.pieces, 0
        t, _ = tap(t, 24)
        t2, ev = tap(t, 12)
        if ev[0]["result"]["outcome"] == "hit":
            assert [e["kind"] for e in ev] == ["attack", "hit", "death", "win"]
            assert not t2.pieces[4].alive and t2.winner == 0 and t2.phase == "over"
            assert tap(t2, 24) == (t2, [])
            return
    raise AssertionError


def test_illegal_tap():
    s = new_game(0)
    s1, ev = tap(s, 5)
    assert ev == [] and s1 == s  # select: nada
    s2, _ = tap(s, 23)
    assert s2.phase == "target" and s2.selected == 0
    s3, ev = tap(s2, 7)
    assert ev == [] and s3.phase == "select" and s3.selected is None
    s4, _ = tap(s2, 24)
    assert s4.selected == 1  # otra propia: cambia la selección
    s5, _ = tap(s2, None)
    assert s5.selected is None


def test_json_roundtrip():
    s, _ = tap(new_game(3), 23)
    assert from_json(to_json(s)) == s


def random_game(seed):
    rng = random.Random(seed)
    s = new_game(seed)
    for _ in range(3000):
        if s.phase == "over":
            return s
        own = [p for p in s.pieces if p.alive and p.owner == s.turn]
        options = [(p, c) for p in own for c in legal_targets(s, p.id)["moves"] + legal_targets(s, p.id)["attacks"]]
        p, c = rng.choice(options)
        s, _ = tap(s, p.cell)
        s, _ = tap(s, c)
        cells = [p.cell for p in s.pieces if p.alive]
        assert len(cells) == len(set(cells))
        assert all(0 <= p.hp <= KINDS[p.kind]["hp"] for p in s.pieces)
    return s


def test_200_random_games():
    for seed in range(200):
        random_game(seed)
