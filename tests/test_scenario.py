"""Netze: gültige Netze, Determinismus (auch über Prozesse), Positionen, Brücken, Blockmodell, Watts–Strogatz."""

import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import kpa_constants as C
import kpa_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("typ", C.ALL_TYPES)
@pytest.mark.parametrize("n,c", [(C.N_MIN, C.C_MIN), (C.N_MIN, C.C_MAX), (C.DEFAULT_N, C.DEFAULT_C), (C.N_MAX, C.C_MAX)])
def test_every_corner_gives_a_valid_network(typ, n, c):
    inst = S.make_instance(typ, n, c, 35, beta=0.5, inside=0.99, width=C.WIDTH_MAX, mode=C.BRIDGE_SPREAD)
    assert inst.n >= 2 and len(inst.pos) == inst.n and inst.m >= 1
    for x, y in inst.pos:
        assert math.isfinite(x) and math.isfinite(y) and -1e-9 <= x <= 1 + 1e-9 and -1e-9 <= y <= 1 + 1e-9
    for a, nb in enumerate(inst.adj):
        assert list(nb) == sorted(set(nb)) and a not in nb
        for b in nb:
            assert a in inst.adj[b]


def test_instances_are_deterministic_per_seed_and_differ_between_seeds():
    a = S.make_instance(C.T_COMMUNITIES, 80, 6, 5)
    assert a.adj == S.make_instance(C.T_COMMUNITIES, 80, 6, 5).adj and a.pos == S.make_instance(C.T_COMMUNITIES, 80, 6, 5).pos
    assert S.make_instance(C.T_COMMUNITIES, 80, 6, 6, layout=False).adj != a.adj
    assert S.make_instance(C.T_TWO_GROUPS, 80, 6, 5, layout=False).adj != S.make_instance(C.T_TWO_GROUPS, 80, 6, 6, layout=False).adj


def test_network_is_independent_of_the_hash_seed_of_the_process():
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import hashlib, kpa_scenario as S, kpa_constants as C;"
            "h = hashlib.sha256();"
            "[h.update(repr(S.make_instance(t, 60, 5, 7, beta=0.3, inside=0.9, layout=False).adj).encode()) for t in C.ALL_TYPES];"
            "print(h.hexdigest())")
    outs = []
    for hashseed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        outs.append(subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(ROOT)], capture_output=True, text=True, env=env, check=True).stdout.strip())
    assert outs[0] == outs[1] and len(outs[0]) == 64


def test_layout_false_skips_the_force_layout_and_unknown_type_raises():
    inst = S.make_instance(C.T_RANDOM, 60, 4, 1, layout=False)
    assert set(inst.pos) == {(0.5, 0.5)}
    with pytest.raises(ValueError):
        S.make_instance("gibt es nicht", 60, 4, 1)


def test_ring_positions_are_on_a_circle_and_groups_exist_only_for_group_networks():
    ring = S.make_instance(C.T_RING, 40, 4, 1)
    assert all(abs(math.hypot(x - 0.5, y - 0.5) - 0.45) < 0.06 for x, y in ring.pos) and ring.groups is None
    assert S.make_instance(C.T_RANDOM, 40, 4, 1, layout=False).groups is None
    assert len(set(S.make_instance(C.T_COMMUNITIES, 60, 5, 1, layout=False).groups)) == C.BLOCKS
    assert set(S.make_instance(C.T_TWO_GROUPS, 60, 5, 1, layout=False).groups) == {0, 1}


# --- Ring ---------------------------------------------------------------------------------------------------------------------------------------


def test_ring_without_rewiring_has_exactly_c_neighbours_and_full_rewiring_changes_the_net():
    ring = S.gen_watts_strogatz(20, 4, 0.0, S._rng(1, 21))
    assert all(len(a) == 4 for a in ring) and ring[0] == (1, 2, 18, 19)
    mixed = S.gen_watts_strogatz(20, 4, 1.0, S._rng(1, 21))
    assert mixed != ring and sum(len(a) for a in mixed) == sum(len(a) for a in ring)


def test_ring_with_few_nodes_and_odd_neighbour_count_is_rounded_down():
    tri = S.gen_watts_strogatz(3, 6, 0.0, S._rng(1, 21))
    assert tri == ((1, 2), (0, 2), (0, 1))                                                  # höchstens (n - 1) // 2 Nachbarn je Seite
    odd = S.gen_watts_strogatz(20, 5, 0.0, S._rng(1, 21))
    assert all(len(a) == 4 for a in odd)                                                    # c = 5 wird zu zwei Nachbarn je Seite


# --- Blockmodell ---------------------------------------------------------------------------------------------------------------------------------


def test_sbm_probabilities_by_hand():
    # n = 4, 2 Gruppen {0,1} und {2,3}: 2 Paare innen, 4 Paare außen; c = 1 heißt m = 2 Kanten
    assert S.sbm_probabilities(4, 2, 1, 0.5) == pytest.approx((0.5, 0.25))
    assert S.sbm_probabilities(4, 2, 1, 1.0) == pytest.approx((1.0, 0.0))
    assert S.sbm_probabilities(4, 2, 1, 0.0) == pytest.approx((0.0, 0.5))
    assert S.sbm_probabilities(4, 2, 99, 0.5) == (1.0, 1.0)                                  # auf höchstens 1 begrenzt
    assert S.sbm_probabilities(4, 4, 1, 0.5) == pytest.approx((0.0, 2 * 0.5 / 6))            # Gruppen der Größe 1: keine Paare innen
    assert S.sbm_probabilities(4, 1, 1, 0.5) == pytest.approx((0.5 * 2 / 6, 0.0))            # eine Gruppe: keine Paare außen


def test_communities_have_the_requested_share_of_inside_edges_and_equal_blocks():
    n, c = 240, 8
    for inside in (0.5, 0.9):
        fractions = []
        for seed in range(100000, 100008):
            adj, lab = S.gen_communities_sbm(n, c, inside, seed)
            inner = sum(1 for a in range(n) for b in adj[a] if a < b and lab[a] == lab[b])
            total = sum(len(x) for x in adj) // 2
            fractions.append(inner / total)
            assert abs(total - c * n / 2) < 0.15 * c * n / 2
        assert float(np.mean(fractions)) == pytest.approx(inside, abs=0.03)
    assert np.bincount(lab).tolist() == [n // C.BLOCKS] * C.BLOCKS


# --- Zwei Gruppen -------------------------------------------------------------------------------------------------------------------------------


def test_two_groups_inner_degree_and_bridge_endpoints():
    adj, lab = S.gen_two_groups(200, 8, 3, C.BRIDGE_WIDE, 1)
    cross = [(a, b) for a in range(200) for b in adj[a] if a < b and lab[a] != lab[b]]
    assert len(cross) == 9
    inner = [sum(1 for b in adj[a] if lab[b] == lab[a]) for a in range(200)]
    assert float(np.mean(inner)) == pytest.approx(8, abs=1.0)
    gates_a = {a for a, _ in cross}
    gates_b = {b for _, b in cross}
    assert len(gates_a) == 3 and len(gates_b) == 3
    for b in gates_b:                                                                       # jeder Tor-Knoten hat genau w Nachbarn auf der anderen Seite
        assert sum(1 for a in adj[b] if lab[a] == 0) == 3


def test_two_groups_width_is_clamped_to_the_group_size_root_and_odd_n_loses_a_node():
    adj, lab = S.gen_two_groups(20, 4, 5, C.BRIDGE_SPREAD, 1)                                # n // 2 = 10, isqrt(10) = 3: 3 · 3 Kanten
    assert sum(1 for a in range(20) for b in adj[a] if a < b and lab[a] != lab[b]) == 9
    adj, lab = S.gen_two_groups(21, 4, 1, C.BRIDGE_WIDE, 1)
    assert len(adj) == 20 and lab.count(0) == 10 and lab.count(1) == 10
