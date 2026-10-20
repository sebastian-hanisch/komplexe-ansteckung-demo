"""Einheiten des Kerns an Mini-Instanzen mit von Hand gerechneten Werten (DEMO-PLAYBOOK §1b)."""

import math
import warnings

import numpy as np
import pytest

import kpa_algorithm as A
from conftest import bridged_cliques, make_adj


def test_edge_arrays_and_degrees(path5):
    src, dst = A.edge_arrays(path5)
    assert sorted(zip(src.tolist(), dst.tolist())) == [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3)]
    assert A.degrees(path5).tolist() == [1, 2, 2, 2, 1]
    s, d = A.edge_arrays(make_adj(3, []))
    assert len(s) == 0 and len(d) == 0


def test_need_vector_hand_values():
    adj = make_adj(6, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2)])         # Grade 4, 2, 2, 1, 1, 0
    assert A.need_vector(adj, r=2).tolist() == [2, 2, 2, 2, 2, 2]
    th = A.need_vector(adj, theta=0.5)                                  # ⌈0,5 · Grad⌉ = 2, 1, 1, 1 (mindestens 1), 1; Grad 0 nie
    assert th[:5].tolist() == [2, 1, 1, 1, 1] and math.isinf(th[5])
    assert A.need_vector(adj, theta=0.25)[0] == 1                       # 0,25 · 4 = 1 exakt: ⌈1⌉ = 1, kein Aufrunden durch Fließkommarauschen
    assert A.need_vector(adj, theta=0.34)[0] == 2                       # 0,34 · 4 = 1,36 → 2


def test_need_vector_rejects_bad_arguments(path5):
    for kwargs in ({}, {"r": 2, "theta": 0.3}, {"r": 0}, {"theta": 0.0}, {"theta": 1.5}):
        with pytest.raises(ValueError):
            A.need_vector(path5, **kwargs)


def test_path_with_threshold_one_reaches_everybody_in_distance_rounds(path5):
    sp = A.threshold_spread(path5, [0], r=1)
    assert sp.round_of == (0, 1, 2, 3, 4) and sp.rounds == 4 and sp.count == 5 and sp.share == 1.0


def test_path_with_threshold_two_is_stuck_at_the_start_group(path5):
    sp = A.threshold_spread(path5, [0, 1], r=2)
    assert sp.round_of == (0, 0, -1, -1, -1) and sp.rounds == 0 and sp.share == pytest.approx(0.4)


def test_triangle_strip_runs_along_the_strip(strip8):
    sp = A.threshold_spread(strip8, [0, 1], r=2)
    assert sp.round_of == (0, 0, 1, 2, 3, 4, 5, 6) and sp.rounds == 6
    assert A.curve(sp) == [2, 3, 4, 5, 6, 7, 8]


def test_star_center_adopts_but_leaves_stay_out(star5):
    sp = A.threshold_spread(star5, [1, 2], r=2)
    assert sp.round_of == (1, 0, 0, -1, -1)
    # Anteilsregel: Blätter (Grad 1) brauchen ⌈θ⌉ = 1 Nachbarn, die Mitte (Grad 4) bei θ = 0,5 zwei; mit dieser Regel füllt sich der Stern
    assert A.threshold_spread(star5, [1, 2], theta=0.5).round_of == (1, 0, 0, 2, 2)


def test_bridge_two_cliques_needs_width_two():
    # Startgruppe: drei Knoten der linken Clique, die den Tor-Knoten 0 sicher mitnehmen (Knoten 3 hat 3 Partner links)
    assert A.threshold_spread(bridged_cliques(1), [0, 1, 2], r=2).count == 4
    assert A.threshold_spread(bridged_cliques(1), [0, 1, 2], r=1).count == 8
    wide = A.threshold_spread(bridged_cliques(2), [0, 1, 2], r=2)
    assert wide.count == 8 and wide.round_of[4] == 1 and wide.round_of[5] == 1                           # Tor-Knoten 4 und 5 haben je zwei Nachbarn links (0 und 1)


def test_isolated_node_never_adopts():
    adj = make_adj(3, [(0, 1)])
    assert A.threshold_spread(adj, [0], theta=0.5).round_of == (0, 1, -1)
    assert A.threshold_spread(adj, [0], r=1).round_of == (0, 1, -1)


def test_seeds_are_validated(path5):
    with pytest.raises(ValueError):
        A.threshold_spread(path5, [7], r=1)
    with pytest.raises(ValueError):
        A.threshold_spread(path5, [-1], r=1)
    assert A.threshold_spread(path5, [], r=1).count == 0
    assert A.threshold_spread(path5, [2, 2, 2], r=9).round_of == (-1, -1, 0, -1, -1)                    # doppelte Starter zählen einmal


def test_empty_net_has_no_nodes_and_share_zero():
    sp = A.threshold_spread((), [], r=1)
    assert sp.n == 0 and sp.share == 0.0 and sp.rounds == 0


def test_adopted_by_and_curve(strip8):
    sp = A.threshold_spread(strip8, [0, 1], r=2)
    assert A.adopted_by(sp, 0) == (True, True, False, False, False, False, False, False)
    assert A.adopted_by(sp, 2) == (True, True, True, True, False, False, False, False)
    assert A.adopted_by(sp, 99) == (True,) * 8
    assert A.curve(A.threshold_spread(strip8, [0, 1], r=3)) == [2]                                      # nichts kommt dazu: nur Runde 0


def test_group_seed_hand_properties(strip8):
    g = A.group_seed(strip8, 3, 7)
    assert len(g) == 3 and list(g) == sorted(g) and len(set(g)) == 3
    assert any(all(w in strip8[v] for w in g if w != v) for v in g)                                      # der Startknoten ist mit beiden anderen Mitgliedern verbunden
    assert A.group_seed(strip8, 3, 7) == g                                                               # gleicher Seed, gleiche Gruppe
    assert len(A.group_seed(strip8, 1, 7)) == 1
    assert len(A.group_seed(make_adj(4, [(0, 1)]), 5, 3)) == 2                                           # weniger Partner als g − 1: kleinere Gruppe


def test_group_seed_rejects_empty_net_and_zero_size(path5):
    with pytest.raises(ValueError):
        A.group_seed(make_adj(3, []), 2, 1)
    with pytest.raises(ValueError):
        A.group_seed(path5, 0, 1)


def test_one_short_nodes(strip8):
    sp = A.threshold_spread(strip8, [0, 1], r=3)
    # Schwelle 3, Gruppe {0, 1}: Knoten 2 hat zwei übernommene Nachbarn (0, 1) → fehlt einer; Knoten 3 hat nur 1 → fehlen zwei
    assert A.one_short(strip8, A.adopted_by(sp, 0), r=3) == (2,)
    assert A.count_adopted_neighbours(strip8, A.adopted_by(sp, 0)).tolist() == [1, 1, 2, 1, 0, 0, 0, 0]
    # Anteil θ = 0,5: Knoten 2 (Grad 4, braucht 2) hat zwei Übernehmer und gehört nicht mehr dazu; Knoten 3 (Grad 4, braucht 2) hat einen (Knoten 1)
    assert A.one_short(strip8, A.adopted_by(sp, 0), theta=0.5) == (3,)
    adj = make_adj(3, [(0, 1)])                                                                          # Knoten 2 ohne Partner
    assert A.one_short(adj, (True, False, False), r=2) == (1,)                                           # Knoten 1: ein Übernehmer, braucht 2; Knoten 2: null Übernehmer, fehlen zwei
    assert A.one_short(adj, (True, False, False), theta=0.5) == ()                                       # Knoten 1 braucht nur 1 und übernimmt gleich; Grad 0 fehlt nie nur einer


# --- Fixpunkt: monoton, reihenfolgeunabhängig -------------------------------------------------------------------------------------------------------


def test_closure_bruteforce_hand_values(path5, star5):
    assert A.closure_bruteforce(path5, [0], r=1) == frozenset(range(5))
    assert A.closure_bruteforce(path5, [0, 1], r=2) == frozenset({0, 1})
    assert A.closure_bruteforce(star5, [1, 2], r=2) == frozenset({0, 1, 2})
    with pytest.raises(ValueError):
        A.closure_bruteforce(make_adj(17, []), [0], r=1)


def test_spread_is_monotone_in_threshold_and_seeds(strip8):
    sizes = [A.threshold_spread(strip8, [0, 1], r=r).count for r in (1, 2, 3, 4)]
    assert sizes == sorted(sizes, reverse=True) and sizes[0] == 8 and sizes[-1] == 2
    assert A.threshold_spread(strip8, [0, 1, 2], r=2).count >= A.threshold_spread(strip8, [0, 1], r=2).count


# --- Kaskadenfenster -------------------------------------------------------------------------------------------------------------------------------------


def test_vulnerable_max_degree_hand_values():
    assert A.vulnerable_max_degree(0.18) == 5 and A.vulnerable_max_degree(0.2) == 5 and A.vulnerable_max_degree(0.34) == 2
    assert A.vulnerable_max_degree(0.5) == 2 and A.vulnerable_max_degree(0.51) == 1 and A.vulnerable_max_degree(1.0) == 1
    for bad in (0.0, -0.1, 1.2):
        with pytest.raises(ValueError):
            A.vulnerable_max_degree(bad)


def test_cascade_margin_hand_value_for_k_star_two():
    # K* = 2: nur k = 2 zählt, 2 · 1 · p_2 = 2 · e^{-z} z² / 2 = z² e^{-z}; Spanne = z² e^{-z} − z
    for z in (0.5, 1.0, 2.0):
        assert A.cascade_margin(z, 0.5) == pytest.approx(z * z * math.exp(-z) - z)
    assert A.cascade_margin(1.0, 0.5) == pytest.approx(math.exp(-1) - 1.0)


def test_window_for_theta_half_is_empty_and_for_small_theta_exists():
    assert A.vulnerable_window(0.5) is None                                                              # z e^{-z} < 1 immer
    assert A.vulnerable_window(0.6) is None
    assert A.vulnerable_window(0.3) is None and A.vulnerable_window(0.26) is None and A.vulnerable_window(0.25) is not None          # K* = 3: z (1 + z) e^{-z} < 1 für alle z; K* = 4 reicht
    lo, hi = A.vulnerable_window(0.18)
    assert 1.0 < lo < 1.1 and 5.7 < hi < 5.8                                                             # Vormessung: 1,03 < z < 5,76
    assert A.cascade_margin(lo, 0.18) == pytest.approx(0.0, abs=1e-9) and A.cascade_margin(hi, 0.18) == pytest.approx(0.0, abs=1e-9)
    mid = 0.5 * (lo + hi)
    assert A.cascade_margin(mid, 0.18) > 0 and A.cascade_margin(lo - 0.1, 0.18) < 0 and A.cascade_margin(hi + 0.1, 0.18) < 0


def test_window_is_one_connected_interval():
    for theta in (0.1, 0.18, 0.25):
        w = A.vulnerable_window(theta)
        assert w is not None
        zs = np.arange(0.05, 40.0, 0.05)
        pos = [float(z) for z in zs if A.cascade_margin(float(z), theta) > 0]
        assert min(pos) >= w[0] - 0.05 and max(pos) <= w[1] + 0.05
        assert all(A.cascade_margin(z, theta) > 0 for z in pos[:: max(1, len(pos) // 20)])


def test_window_widens_when_threshold_gets_smaller():
    w1, w2 = A.vulnerable_window(0.25), A.vulnerable_window(0.1)
    assert w2[1] - w2[0] > w1[1] - w1[0]


def test_no_warnings_in_the_core(strip8):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        A.threshold_spread(strip8, [0, 1], theta=0.4)
        A.threshold_spread(make_adj(3, []), [0], theta=0.4)
        A.vulnerable_window(0.18)


# --- Lücken aus der Mutationsprüfung ---------------------------------------------------------------------------------------------------------


def test_closure_bruteforce_accepts_sixteen_nodes_and_rejects_seventeen():
    adj16 = make_adj(16, [(i, i + 1) for i in range(15)])
    assert A.closure_bruteforce(adj16, range(14), r=1) == frozenset(range(16))                          # zwei Außenstehende: 4 Teilmengen, schnell
    with pytest.raises(ValueError):
        A.closure_bruteforce(make_adj(17, [(i, i + 1) for i in range(16)]), range(15), r=1)


def test_one_short_includes_the_last_node():
    adj = make_adj(3, [(0, 1), (1, 2)])
    assert A.one_short(adj, (True, True, False), r=2) == (2,)                                           # Knoten 2: ein übernommener Partner, nötig 2


def test_poisson_pmf_hand_values():
    assert A.poisson_pmf(0, 0.0) == 1.0 and A.poisson_pmf(3, 0.0) == 0.0 and A.poisson_pmf(1, 0.0) == 0.0
    assert A.poisson_pmf(0, 1.0) == pytest.approx(math.exp(-1)) and A.poisson_pmf(2, 1.5) == pytest.approx(math.exp(-1.5) * 1.5**2 / 2)
    assert sum(A.poisson_pmf(k, 3.0) for k in range(60)) == pytest.approx(1.0)


def test_seed_equal_to_n_is_out_of_range(path5):
    with pytest.raises(ValueError):
        A.threshold_spread(path5, [5], r=1)
    assert A.threshold_spread(path5, [4], r=1).count == 5


def test_window_with_a_coarse_grid_still_finds_both_edges():
    exact = A.vulnerable_window(0.18)
    coarse_start = A.vulnerable_window(0.18, step=2.0)                                                  # das Fenster beginnt schon am ersten Gitterpunkt
    assert coarse_start[0] == pytest.approx(exact[0], abs=1e-6) and coarse_start[1] == pytest.approx(exact[1], abs=1e-6)
    coarse_end = A.vulnerable_window(0.18, z_max=5.9, step=0.5)                                         # das Fenster reicht bis zum letzten Gitterpunkt
    assert coarse_end[0] == pytest.approx(exact[0], abs=1e-6) and coarse_end[1] == pytest.approx(exact[1], abs=1e-6)
