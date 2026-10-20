"""Orakel-Test komplexe-ansteckung-demo: das Verfahren (Schwellen-Ausbreitung) gegen andere Rechenwege.

* Schwelle 1 ist Erreichbarkeit: networkx.node_connected_component liefert dieselbe Menge (200 Zufallsnetze).
* Der Fixpunkt ist die kleinste Menge, die die Startgruppe enthält und von außen nicht mehr überzeugt wird: `closure_bruteforce` zählt alle Teilmengen auf (Netze bis 11 Knoten, 200 Fälle, Zahl- und Anteilsregel).
* Die Reihenfolge der Übernahmen ist gleichgültig: eine asynchrone Fassung in zufälliger Knotenreihenfolge landet in derselben Menge wie die synchronen Runden.
* Die Runde, in der ein Knoten übernimmt, ist 1 + die Mindestzahl an Runden, die eine Kette von Auslösern braucht: Gegenprobe mit der naiven Runde-für-Runde-Schleife in reinem Python.
* Das Kaskadenfenster: scipy.stats.poisson und scipy.optimize.brentq liefern dieselben Grenzen wie Abtasten und Bisektion.
* Ring ohne Umverdrahtung stimmt mit networkx.watts_strogatz_graph(n, k, 0) überein; Umverdrahtung erhält die Kantenzahl."""

import numpy as np
import pytest

import kpa_algorithm as A
import kpa_constants as C
import kpa_scenario as S
from conftest import make_adj


def _random_net(rng, n_lo, n_hi, p_lo=0.05, p_hi=0.45):
    n = int(rng.integers(n_lo, n_hi))
    p = float(rng.uniform(p_lo, p_hi))
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p]
    return n, pairs, make_adj(n, pairs)


def test_threshold_one_is_reachability_like_networkx():
    nx = pytest.importorskip("networkx")
    for t in range(200):
        rng = np.random.default_rng(t)
        n, pairs, adj = _random_net(rng, 6, 30)
        seeds = rng.choice(n, int(rng.integers(1, 4)), replace=False).tolist()
        sp = A.threshold_spread(adj, seeds, r=1)
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(pairs)
        reach = set()
        for s in seeds:
            reach |= nx.node_connected_component(g, s)
        assert {v for v in range(n) if sp.round_of[v] >= 0} == reach, t
        for v in reach:                                                                                  # die Runde ist der Abstand zur Startgruppe
            assert sp.round_of[v] == min(nx.shortest_path_length(g, s, v) for s in seeds if nx.has_path(g, s, v)) or v in seeds


def test_fixed_point_equals_smallest_closed_superset_by_enumeration():
    for t in range(200):
        rng = np.random.default_rng(1000 + t)
        n, _, adj = _random_net(rng, 4, 12, 0.15, 0.6)
        seeds = rng.choice(n, int(rng.integers(1, min(4, n))), replace=False).tolist()
        if t % 2:
            kwargs = {"r": int(rng.integers(1, 4))}
        else:
            kwargs = {"theta": float(rng.choice([0.2, 0.34, 0.5, 0.75, 1.0]))}
        sp = A.threshold_spread(adj, seeds, **kwargs)
        assert frozenset(v for v in range(n) if sp.round_of[v] >= 0) == A.closure_bruteforce(adj, seeds, **kwargs), (t, kwargs)


def test_order_of_adoption_does_not_matter():
    for t in range(200):
        rng = np.random.default_rng(5000 + t)
        n, _, adj = _random_net(rng, 8, 40, 0.05, 0.3)
        seeds = rng.choice(n, int(rng.integers(1, 5)), replace=False).tolist()
        kwargs = {"r": int(rng.integers(2, 4))} if t % 2 else {"theta": float(rng.choice([0.25, 0.34, 0.5]))}
        need = A.need_vector(adj, **kwargs)
        cur = np.zeros(n, bool)
        cur[seeds] = True
        order = list(range(n))
        rng.shuffle(order)
        changed = True
        while changed:
            changed = False
            for v in order:
                if not cur[v] and sum(cur[w] for w in adj[v]) >= need[v]:
                    cur[v] = True
                    changed = True
        sp = A.threshold_spread(adj, seeds, **kwargs)
        assert [x >= 0 for x in sp.round_of] == cur.tolist(), (t, kwargs)


def test_round_numbers_against_naive_loop():
    for t in range(100):
        rng = np.random.default_rng(9000 + t)
        n, _, adj = _random_net(rng, 8, 35, 0.08, 0.35)
        seeds = rng.choice(n, 2, replace=False).tolist()
        r = int(rng.integers(1, 4))
        expect = [-1] * n
        for s in seeds:
            expect[s] = 0
        rnd = 0
        while True:
            now = [v for v in range(n) if expect[v] < 0 and sum(1 for w in adj[v] if 0 <= expect[w] <= rnd) >= r]
            if not now:
                break
            rnd += 1
            for v in now:
                expect[v] = rnd
        assert A.threshold_spread(adj, seeds, r=r).round_of == tuple(expect), t


def test_cascade_window_against_scipy():
    stats = pytest.importorskip("scipy.stats")
    optimize = pytest.importorskip("scipy.optimize")
    for theta in (0.1, 0.18, 0.25, 0.3):
        big_k = int(np.floor(1.0 / theta + 1e-9))

        def margin(z):
            return sum(k * (k - 1) * stats.poisson.pmf(k, z) for k in range(2, big_k + 1)) - z

        zs = np.linspace(0.05, 30.0, 6000)
        sign = np.array([margin(z) > 0 for z in zs])
        if not sign.any():
            assert A.vulnerable_window(theta) is None, theta
            continue
        i0, i1 = int(np.flatnonzero(sign)[0]), int(np.flatnonzero(sign)[-1])
        lo = optimize.brentq(margin, zs[i0 - 1], zs[i0])
        hi = optimize.brentq(margin, zs[i1], zs[i1 + 1])
        w = A.vulnerable_window(theta)
        assert w[0] == pytest.approx(lo, abs=1e-6) and w[1] == pytest.approx(hi, abs=1e-6), theta


def test_ring_without_rewiring_is_the_networkx_lattice_and_rewiring_keeps_edge_count():
    nx = pytest.importorskip("networkx")
    for n, k in ((20, 4), (30, 6), (60, 6), (25, 2)):
        ours = S.gen_watts_strogatz(n, k, 0.0, S._rng(1, 21))
        theirs = nx.watts_strogatz_graph(n, k, 0.0, seed=1)
        assert {(a, b) for a in range(n) for b in ours[a] if a < b} == {tuple(sorted(e)) for e in theirs.edges()}
        for beta in (0.1, 0.5, 1.0):
            adj = S.gen_watts_strogatz(n, k, beta, S._rng(3, 21))
            assert sum(len(a) for a in adj) // 2 == n * (k // 2)
            assert all(v not in adj[v] for v in range(n))


def test_two_groups_bridge_structure_by_independent_count():
    for w in (1, 2, 3, 4, 5):
        for mode, distinct in ((C.BRIDGE_WIDE, False), (C.BRIDGE_SPREAD, True)):
            adj, lab = S.gen_two_groups(100, 6, w, mode, 11)
            cross = [(a, b) for a in range(100) for b in adj[a] if a < b and lab[a] != lab[b]]
            assert len(cross) == w * w
            left, right = {a for a, _ in cross}, {b for _, b in cross}
            assert (len(left) == w * w and len(right) == w * w) if distinct else (len(left) == w and len(right) == w)


def test_cascade_margin_equals_z_squared_times_the_regularized_incomplete_gamma():
    """Σ_{k=2..K} k (k − 1) p_k = z² · P(Poisson(z) ≤ K − 2) = z² · Q(K − 1, z): die Bedingung lässt sich als z · Q(K* − 1, z) > 1 schreiben."""
    special = pytest.importorskip("scipy.special")
    for theta in (0.1, 0.18, 0.25):
        big_k = A.vulnerable_max_degree(theta)
        for z in (0.5, 1.0, 2.5, 4.0, 5.76, 9.0):
            assert A.cascade_margin(z, theta) + z == pytest.approx(z * z * special.gammaincc(big_k - 1, z), rel=1e-9), (theta, z)
