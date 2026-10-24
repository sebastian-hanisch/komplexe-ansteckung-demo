"""Jede Zahl aus der README wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle mit je fünf Startgruppen (40 Läufe je Zelle), n = 250, c = 6, Startgruppe g = 5, wo nichts anderes steht.
„Voll“ heißt: mindestens 90 % der Betriebe haben übernommen. Alle Zufälle laufen über seedbare Generatoren und sind plattformstabil; Anteile sind Bruchteile von 40 bzw. 200 und
werden daher mit kleinem Band geprüft."""

from functools import lru_cache

import numpy as np
import pytest

import kpa_algorithm as A
import kpa_constants as C
import kpa_evaluation as ev
from kpa_scenario import make_instance

SW = C.SWEEP_SEEDS
TOL = 0.006
LABELS = [row[0] for row in C.TYPE_CASES]
RING, RING5, GRID, COMM, RANDOM, BA, POWER = LABELS


@lru_cache(maxsize=None)
def _types():
    return {r["label"]: r["cells"] for r in ev.type_rows(250, 6, 5, seeds=SW)}


@lru_cache(maxsize=None)
def _shortcuts():
    return ev.shortcut_rows(250, 6, 5, seeds=SW)


@lru_cache(maxsize=None)
def _watts():
    return ev.watts_rows(seeds=SW)


@lru_cache(maxsize=None)
def _communities(r):
    return ev.community_rows(240, 5, C.RULE_COUNT, r, 34, seeds=SW)


@lru_cache(maxsize=None)
def _bridge():
    return ev.bridge_rows(120, 12, 5, seeds=SW)


def _stat(sample_type, **rule):
    """Zelle `cell_stats` für einen Netztyp aus TYPE_CASES und eine Regel (n = 250, c = 6, g = 5)."""
    case = next(c for c in C.TYPE_CASES if c[0] == sample_type)
    sps = []
    for s in SW:
        adj = make_instance(case[1], 250, 6 if not (case[1] == C.T_GRID and rule.get("grid8")) else 8, s, beta=case[2], inside=case[3], layout=False).adj
        sps += [sp for _, sp in ev.run_batch(adj, 5, s, 5, **{k: v for k, v in rule.items() if k != "grid8"})]
    return ev.cell_stats(sps)


# --- E1: Netztypen und Schwellen -------------------------------------------------------------------------------------------------------------


def test_threshold_one_fills_every_network_and_the_rounds_follow_the_shape_of_the_net():
    cells = _types()
    assert all(cells[label][1]["full"] == 1.0 for label in LABELS) and [round(cells[label][1]["share"], 3) for label in LABELS] == [1.0, 1.0, 1.0, 1.0, 0.996, 1.0, 1.0]   # das Zufallsnetz hat Betriebe ohne Partner
    assert [cells[label][1]["rounds"] for label in LABELS] == [41.0, 8.0, 19.0, 5.0, 4.0, 3.0, 4.0]


def test_threshold_two_needs_triangles_in_the_median_but_not_every_run_fills():
    cells = _types()
    assert [round(cells[label][2]["full"], 3) for label in LABELS] == [1.0, 1.0, 1.0, 0.675, 0.15, 0.85, 0.3]
    assert [cells[label][2]["share"] for label in (RING, RING5, GRID)] == [1.0, 1.0, 1.0]
    assert cells[COMM][2]["share"] == pytest.approx(0.98, abs=TOL) and cells[BA][2]["share"] == 1.0 and cells[POWER][2]["share"] == pytest.approx(0.82, abs=TOL) and cells[RANDOM][2]["share"] == pytest.approx(0.02, abs=TOL)
    assert [cells[label][2]["rounds"] for label in (RING, RING5, GRID, COMM, BA, POWER)] == [61.0, 51.0, 30.5, 15.0, 6.0, 8.0]


def test_threshold_three_is_carried_by_the_regular_ring_only():
    cells = _types()
    assert [round(cells[label][3]["full"], 3) for label in LABELS] == [1.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0]
    assert cells[RING][3]["rounds"] == 122.0 and cells[RING5][3]["share"] == pytest.approx(0.08, abs=TOL) and cells[BA][3]["share"] == pytest.approx(0.02, abs=TOL)


def test_verdict_of_experiment_one_counts_7_5_1_networks_and_every_threshold_differs():
    text = ev.verdict_types([{"label": k, "typ": k, "cells": v} for k, v in _types().items()])[1]
    assert "bei r = 1 in 7 von 7 Netztypen; bei r = 2 in 5 von 7 Netztypen (" in text and "bei r = 3 in 1 von 7 Netztypen (Ring, regelmäßig)" in text
    cells = _types()
    fills = {r: {label for label in LABELS if cells[label][r]["share"] >= C.FULL_SHARE} for r in C.THRESHOLDS}
    assert fills[3] < fills[2] < fills[1]                                                         # jede Schwelle trägt weniger als die vorige (echte Teilmengen: keine Nullspalte)


def test_edges_with_a_common_partner_by_networkx():
    nx = pytest.importorskip("networkx")
    shares = {}
    for label, typ, beta, inside in C.TYPE_CASES:
        vals = []
        for s in SW:
            adj = make_instance(typ, 250, 6, s, beta=beta, inside=inside, layout=False).adj
            g = nx.Graph()
            g.add_edges_from((a, b) for a in range(len(adj)) for b in adj[a] if a < b)
            vals.append(np.mean([any(True for _ in nx.common_neighbors(g, a, b)) for a, b in g.edges()]))
        shares[label] = float(np.median(vals))
    assert [round(shares[label], 2) for label in LABELS] == [1.0, 0.95, 1.0, 0.36, 0.12, 0.35, 0.54]
    # gemeinsame Partner erleichtern die Schwelle 2, aber ihr Anteil allein sagt den Befund nicht voraus: das Potenzgesetz-Netz hat mehr als Verbünde und skalenfreies Netz und füllt seltener
    assert shares[POWER] > shares[COMM] and _types()[POWER][2]["full"] < _types()[COMM][2]["full"]


# --- Startgruppe ----------------------------------------------------------------------------------------------------------------------------------


def test_a_single_starter_never_spreads_with_threshold_two_and_two_starters_suffice_on_the_ring():
    for label, typ, beta, inside in C.TYPE_CASES:
        sps = []
        for s in SW:
            adj = make_instance(typ, 250, 6, s, beta=beta, inside=inside, layout=False).adj
            sps += [sp for _, sp in ev.run_batch(adj, 1, s, 5, r=2)]
        assert all(sp.count == 1 and sp.rounds == 0 for sp in sps), label
    ring5 = {}
    for g in (2, 3, 5, 10):
        sps = []
        for s in SW:
            adj = make_instance(C.T_RING, 250, 6, s, beta=0.05, layout=False).adj
            sps += [sp for _, sp in ev.run_batch(adj, g, s, 5, r=2)]
        ring5[g] = ev.cell_stats(sps)["full"]
    assert ring5 == {2: 0.975, 3: 0.975, 5: 1.0, 10: 1.0}


# --- E2: Abkürzungen ---------------------------------------------------------------------------------------------------------------------------


def test_shortcuts_speed_up_threshold_one_and_two_until_the_tipping_point():
    rows = {row["beta"]: row["cells"] for row in _shortcuts()}
    assert [rows[b][1]["rounds"] for b in (0.0, 0.01, 0.05, 0.1, 1.0)] == [41.0, 19.0, 8.0, 6.0, 4.0] and all(rows[b][1]["full"] == 1.0 for b in rows)
    assert [rows[b][2]["rounds"] for b in (0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5)] == [61.0, 61.0, 51.0, 35.0, 22.0, 18.0, 18.5]
    assert [rows[b][2]["full"] for b in C.SHORTCUT_BETAS] == [1.0, 1.0, 1.0, 1.0, 0.775, 0.425, 0.25, 0.0]


def test_threshold_two_tips_at_thirty_percent_and_threshold_three_already_at_one_percent():
    rows = _shortcuts()
    assert ev.tipping_beta(rows, 2) == 0.3 and ev.tipping_beta(rows, 3) == 0.01 and ev.tipping_beta(rows, 1) is None
    r3 = {row["beta"]: row["cells"][3] for row in rows}
    assert r3[0.0]["full"] == 1.0 and r3[0.01]["full"] == 0.25 and r3[0.01]["share"] == pytest.approx(0.28, abs=TOL) and r3[0.05]["full"] == 0.0
    r2 = {row["beta"]: row["cells"][2] for row in rows}
    assert r2[0.3]["share"] == pytest.approx(0.11, abs=TOL) and r2[1.0]["share"] == pytest.approx(0.02, abs=TOL)
    text = ev.verdict_shortcuts(rows)[1]
    assert "von 41 (ohne Abkürzungen) auf 4 (β = 100 %)" in text and "zunächst von 61 auf 22 (β = 20 %)" in text and "Ab β = 30 %" in text and "Endanteil dort 11 %" in text


# --- E3: Kaskadenfenster -------------------------------------------------------------------------------------------------------------------------


def test_cascade_window_from_the_formula_and_in_the_simulation():
    lo, hi = A.vulnerable_window(C.WATTS_THETA)
    assert lo == pytest.approx(1.0207, abs=1e-3) and hi == pytest.approx(5.7647, abs=1e-3) and A.vulnerable_max_degree(C.WATTS_THETA) == 5
    frac = {r["z"]: r["frac"] for r in _watts()}
    assert [frac[z] for z in C.WATTS_ZS] == [0.0, 0.035, 0.755, 0.85, 0.94, 0.91, 0.745, 0.58, 0.265, 0.055, 0.005, 0.0]
    size = {r["z"]: r["size"] for r in _watts()}
    assert size[4.0] == pytest.approx(0.98, abs=TOL) and size[1.5] == pytest.approx(0.58, abs=TOL) and size[6.5] == pytest.approx(0.998, abs=TOL)


def test_verdict_of_experiment_three_names_the_averages_inside_and_outside():
    text = ev.verdict_watts(_watts())[1]
    assert "1,02 < z < 5,76" in text and "innerhalb dieses Fensters im Mittel 80 % der Einzelstarter" in text and "außerhalb 6 %" in text


def test_window_exists_only_for_small_thresholds():
    assert A.vulnerable_window(0.25) is not None and A.vulnerable_window(0.26) is None and A.vulnerable_window(0.5) is None
    small, large = A.vulnerable_window(0.18), A.vulnerable_window(0.1)
    assert large[1] - large[0] > small[1] - small[0]                                              # je kleiner die Schwelle, desto breiter das Fenster


# --- E4: Gemeinschaften ----------------------------------------------------------------------------------------------------------------------


def test_communities_hold_threshold_two_back_only_with_very_few_cross_edges():
    rows = {(r["c"], r["inside"]): r for r in _communities(2)}
    assert [round(rows[(8, i)]["other"], 3) for i in C.COMMUNITY_INSIDES] == [1.0, 0.995, 0.405, 0.0, 0.0, 0.0]
    assert [round(rows[(12, i)]["other"], 3) for i in C.COMMUNITY_INSIDES] == [1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
    assert rows[(8, 0.95)]["own"] == 1.0 and rows[(8, 0.95)]["total"] == pytest.approx(1 / 6, abs=TOL) and rows[(12, 0.97)]["total"] == pytest.approx(1 / 6, abs=TOL)
    text = ev.verdict_communities(_communities(2), C.RULE_COUNT, 2, 34)[1]
    assert "bei mittlerem Grad 8 ab 95 %" in text and "bei mittlerem Grad 12 ab 97 %" in text


def test_simple_contagion_knows_no_community_border():
    assert all(r["other"] == 1.0 and r["total"] == 1.0 for r in _communities(1))


# --- E5: Brücken ------------------------------------------------------------------------------------------------------------------------------


def test_bridge_width_decides_and_spread_out_edges_never_carry_threshold_two():
    rows = {(r["mode"], r["w"]): r["cells"] for r in _bridge()}
    wide = [[rows[(C.BRIDGE_WIDE, w)][r]["cross"] for w in C.BRIDGE_WIDTHS] for r in C.THRESHOLDS]
    assert wide[0] == [1.0] * 5 and wide[1] == [0.0, 0.875, 1.0, 1.0, 1.0] and wide[2] == [0.0, 0.0, 0.125, 0.7, 0.95]
    assert all(rows[(C.BRIDGE_SPREAD, w)][r]["cross"] == 0.0 for w in C.BRIDGE_WIDTHS for r in (2, 3)) and all(rows[(C.BRIDGE_SPREAD, w)][1]["cross"] == 1.0 for w in C.BRIDGE_WIDTHS)
    assert rows[(C.BRIDGE_WIDE, 3)][3]["other"] == pytest.approx(0.05, abs=TOL)                    # nur die drei Tor-Knoten (3 von 60) übernehmen
    assert [ev.first_crossing(_bridge(), C.BRIDGE_WIDE, r) for r in C.THRESHOLDS] == [1, 2, 4] and [ev.first_crossing(_bridge(), C.BRIDGE_SPREAD, r) for r in C.THRESHOLDS] == [1, None, None]


# --- Anteilsregel -----------------------------------------------------------------------------------------------------------------------------


def test_share_rule_at_thirty_four_percent_fills_only_nets_with_equal_degrees():
    st = {label: _stat(label, theta=0.34) for label in LABELS}
    assert [round(st[label]["full"], 3) for label in LABELS] == [1.0, 0.05, 0.0, 0.0, 0.0, 0.0, 0.1]
    assert st[RING]["rounds"] == 122.0 and st[COMM]["share"] == pytest.approx(0.02, abs=TOL) and st[RING5]["share"] == pytest.approx(0.19, abs=TOL)
    grid8 = _stat(GRID, theta=0.34, grid8=True)
    assert grid8["full"] == 1.0 and grid8["rounds"] == 29.5
    assert _stat(GRID, theta=0.5, grid8=True)["full"] == 0.0


def test_share_rule_at_twenty_percent_fills_every_network_type():
    st = {label: _stat(label, theta=0.2) for label in LABELS}
    assert [round(st[label]["full"], 2) for label in LABELS] == [1.0, 1.0, 1.0, 1.0, 1.0, 0.97, 0.82]
    assert [st[label]["rounds"] for label in LABELS] == [61.0, 39.0, 24.0, 9.0, 8.0, 6.0, 6.0]


# --- Standardnetz und Presets ---------------------------------------------------------------------------------------------------------------


def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_default_network_and_presets():
    d = _preset("Ring ohne Abkürzungen (Voreinstellung)")
    assert (d.inst.n, d.inst.m, len(d.seeds), d.spread.count, d.spread.rounds, d.reference.rounds) == (150, 450, 5, 150, 36, 24) and d.compare["r = 3"].rounds == 72
    k = _preset("Abkürzungen: der Kipppunkt")
    assert (k.inst.n, k.inst.m, k.spread.count, k.spread.rounds, len(k.short), k.reference.count, k.reference.rounds) == (250, 750, 9, 2, 26, 250, 4)
    z = _preset("Zufallsnetz: kaum gemeinsame Partner")
    assert (z.inst.m, z.spread.count, z.spread.rounds, len(z.short), z.reference.count, z.reference.rounds) == (300, 7, 1, 25, 147, 5)
    g = _preset("Gemeinschaften halten auf")
    assert (g.inst.m, g.spread.count, g.spread.rounds, len(g.short), g.reference.count, g.start_share, g.other_share) == (626, 25, 3, 5, 150, 1.0, 0.0)
    b = _preset("Brücke zu schmal")
    assert (b.inst.n, b.inst.m, b.spread.count, b.spread.rounds, len(b.short), b.reference.count, b.reference.rounds) == (120, 718, 60, 3, 1, 120, 6)
    h = _preset("Anteilsregel: Hubs sind schwer zu überzeugen")
    assert (h.inst.m, h.spread.count, h.spread.rounds, len(h.short), h.reference.rounds, h.compare["r = 2"].count) == (444, 6, 1, 15, 3, 150)
    w = _preset("Kaskadenfenster: ein Startbetrieb genügt")
    assert (w.inst.m, len(w.seeds), w.spread.count, w.spread.rounds, w.reference.count) == (300, 1, 147, 7, 147)


def test_cascade_preset_stops_with_more_partners():
    s = C.PRESETS["Kaskadenfenster: ein Startbetrieb genügt"]
    assert ev.analyse(ev.Settings(**{**s, "c": 8})).spread.count == 2 and ev.analyse(ev.Settings(**{**s, "c": 3})).spread.count == 146
