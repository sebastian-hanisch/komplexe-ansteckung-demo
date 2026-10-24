"""Verdikte und Messhilfen an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses
import math

import pytest

import kpa_algorithm as A
import kpa_constants as C
import kpa_evaluation as ev
from conftest import make_adj

NAN = float("nan")


def _an(spread_rounds, seeds, count, ref_rounds=4, ref_count=None, short=(), start=NAN, other=NAN, rule=C.RULE_COUNT, r=2, theta=34, edges=True):
    """Analyse mit handgesetzten Ergebnissen auf einem echten kleinen Netz (n = 60)."""
    base = ev.analyse(ev.Settings(C.T_RANDOM, C.N_MIN, 4, 3))
    inst = base.inst if edges else dataclasses.replace(base.inst, adj=tuple(() for _ in base.inst.adj))
    n = inst.n

    def spread(k, rounds):
        return A.Spread(tuple([0] * min(seeds, k) + [1] * max(0, k - seeds) + [-1] * (n - k)), rounds)

    st = dataclasses.replace(base.settings, rule=rule, r=r, theta=theta)
    return dataclasses.replace(base, inst=inst, settings=st, seeds=tuple(range(seeds)), spread=spread(count, spread_rounds), reference=spread(n if ref_count is None else ref_count, ref_rounds),
                               short=tuple(short), start_share=start, other_share=other)


def test_de_uses_a_decimal_comma_and_a_dash_for_undefined_numbers():
    assert ev.de(1.26, 1) == "1,3" and ev.de(0.9487, 3) == "0,949" and ev.de(3, 0) == "3" and ev.de(NAN, 2) == "–" and ev.de(None) == "–"


def test_runden_and_rule_texts():
    assert ev.runden(1) == "1 Runde" and ev.runden(0) == "0 Runden" and ev.runden(36) == "36 Runden"
    assert ev.rule_text(C.RULE_COUNT, 1, 34) == "Schwelle r = 1 (ein übernommener Partner genügt)"
    assert ev.rule_text(C.RULE_COUNT, 3, 34) == "Schwelle r = 3" and ev.rule_text(C.RULE_SHARE, 3, 34) == "Schwelle θ = 34 % der Partner"
    assert ev.rule_kwargs(C.RULE_COUNT, 3, 34) == {"r": 3} and ev.rule_kwargs(C.RULE_SHARE, 3, 34) == {"theta": 0.34}
    assert ev.rule_label(C.RULE_COUNT, 3, 34) == "r = 3" and ev.rule_label(C.RULE_SHARE, 3, 34) == "θ = 34 %"


def test_main_verdict_success_when_the_net_is_filled():
    n = 60
    kind, text = ev.verdict_main(_an(7, 5, n))
    assert kind == "success" and f"Startgruppe aus 5 Knoten, Schwelle r = 2: am Ende haben {n} von {n} Knoten übernommen (100 %), nach 7 Runden." in text
    assert "Die Ausbreitung füllt das Netz." in text and "Zum Vergleich erreicht die einfache Ansteckung (r = 1) mit derselben Startgruppe 100 % nach 4 Runden." in text


def test_main_verdict_threshold_for_filled_is_ninety_percent():
    assert ev.analyse(ev.Settings(C.T_RANDOM, C.N_MIN, 4, 3)).inst.n == 60
    assert ev.verdict_main(_an(3, 5, 54))[0] == "success"                                            # 54 / 60 = 90 %
    assert ev.verdict_main(_an(3, 5, 53))[0] == "info"


def test_main_verdict_stuck_in_the_start_group_names_the_nodes_one_short():
    kind, text = ev.verdict_main(_an(0, 5, 5, short=(7, 9)))
    assert kind == "info" and "ohne dass in einer Runde jemand dazukam" in text and "kein Knoten außerhalb hat genug übernommene Partner" in text
    assert "2 Knoten sind knapp davor (ihnen fehlt genau ein Partner)." in text and "(8 %)" in text
    kind, text = ev.verdict_main(_an(0, 5, 5))
    assert "Auch knapp davor ist kein Knoten." in text


def test_main_verdict_partial_spread_and_group_shares():
    kind, text = ev.verdict_main(_an(3, 5, 30, short=(1,), start=1.0, other=0.25))
    assert kind == "info" and "(50 %), nach 3 Runden" in text and "Sie bleibt stehen, bevor das Netz voll ist." in text
    assert "1 Knoten ist knapp davor (ihm fehlt genau ein Partner)." in text and "Im Verbund des Startknotens haben 100 % übernommen, in den übrigen 25 %." in text


def test_main_verdict_for_threshold_one_and_share_rule_and_without_edges():
    kind, text = ev.verdict_main(_an(4, 5, 60, r=1))
    assert "Schwelle r = 1 (ein übernommener Partner genügt)" in text and "Zum Vergleich" not in text
    kind, text = ev.verdict_main(_an(4, 5, 30, rule=C.RULE_SHARE, theta=34))
    assert "Schwelle θ = 34 % der Partner" in text and "Zum Vergleich" in text
    kind, text = ev.verdict_main(_an(0, 0, 0, edges=False))
    assert kind == "warning" and "keine Kanten" in text


# --- Messhilfen ---------------------------------------------------------------------------------------------------------------------------------


def test_cell_stats_by_hand():
    def sp(k, rounds, n=10):
        return A.Spread(tuple([0] * k + [-1] * (n - k)), rounds)

    stats = ev.cell_stats([sp(10, 4), sp(9, 8), sp(2, 1), sp(1, 0)])                                # Anteile 1; 0,9; 0,2; 0,1
    assert stats == {"share": 0.55, "full": 0.5, "rounds": 6.0, "runs": 4}                          # Median (0,2 + 0,9) / 2; zwei vollständige Läufe mit Runden 4 und 8
    empty = ev.cell_stats([])
    assert empty["runs"] == 0 and math.isnan(empty["share"]) and math.isnan(empty["full"])
    none_full = ev.cell_stats([sp(1, 0)])
    assert none_full["full"] == 0.0 and math.isnan(none_full["rounds"])


def test_group_shares_by_hand():
    from kpa_scenario import Instance

    inst = Instance("x", make_adj(4, [(0, 1), (2, 3)]), ((0, 0),) * 4, groups=(0, 0, 1, 1))
    sp = A.Spread((0, 1, -1, -1), 1)
    assert ev.group_shares(inst, sp, 0) == (1.0, 0.0) and ev.group_shares(inst, sp, 2) == (0.0, 1.0)
    assert all(math.isnan(x) for x in ev.group_shares(dataclasses.replace(inst, groups=None), sp, 0))
    one = dataclasses.replace(inst, groups=(0, 0, 0, 0))
    own, other = ev.group_shares(one, sp, 0)
    assert own == 0.5 and math.isnan(other)


def test_run_batch_returns_starts_runs_and_nothing_for_a_net_without_edges():
    adj = make_adj(6, [(0, 1), (1, 2), (2, 0), (3, 4)])
    runs = ev.run_batch(adj, 2, 7, 4, r=1)
    assert len(runs) == 4 and all(len(sd) == 2 for sd, _ in runs)
    assert ev.run_batch(make_adj(3, []), 2, 7, 4, r=1) == []
    within = ev.run_batch(adj, 2, 7, 4, within={3, 4}, r=1)
    assert all(set(sd) == {3, 4} for sd, _ in within)


# --- Verdikte der Experimente -----------------------------------------------------------------------------------------------------------------------


def _cell(share, full=None, rounds=NAN):
    return {"share": share, "full": share if full is None else full, "rounds": rounds, "runs": 20}


def test_verdict_types_counts_networks_per_threshold():
    rows = [{"label": "A", "typ": "A", "cells": {1: _cell(1.0), 2: _cell(1.0), 3: _cell(1.0)}},
            {"label": "B", "typ": "B", "cells": {1: _cell(1.0), 2: _cell(0.9), 3: _cell(0.02)}},
            {"label": "C", "typ": "C", "cells": {1: _cell(1.0), 2: _cell(0.89), 3: _cell(0.02)}}]
    kind, text = ev.verdict_types(rows)
    assert kind == "info" and "bei r = 1 in 3 von 3 Netztypen; bei r = 2 in 2 von 3 Netztypen (A, B); bei r = 3 in 1 von 3 Netztypen (A)." in text
    assert ev.verdict_types([])[0] == "warning"
    assert ev.verdict_types([{"label": "A", "typ": "A", "cells": {1: _cell(NAN)}}])[0] == "warning"


def _srow(beta, f1, f2, f3, r1=10.0, r2=20.0, s2=1.0):
    return {"beta": beta, "cells": {1: {"share": 1.0, "full": f1, "rounds": r1, "runs": 20}, 2: {"share": s2, "full": f2, "rounds": r2, "runs": 20}, 3: {"share": 0.0, "full": f3, "rounds": NAN, "runs": 20}}}


def test_tipping_beta_and_verdict_shortcuts_by_hand():
    rows = [_srow(0.0, 1, 1, 1, r1=49, r2=74), _srow(0.1, 1, 0.93, 0, r1=6, r2=38), _srow(0.2, 1, 0.68, 0, r1=5, r2=25), _srow(0.3, 1, 0.38, 0, r1=5, r2=20, s2=0.07), _srow(1.0, 1, 0, 0, r1=4, r2=NAN, s2=0.02)]
    assert ev.tipping_beta(rows, 2) == 0.3 and ev.tipping_beta(rows, 2, level=0.0) == 1.0 and ev.tipping_beta(rows, 1) is None
    kind, text = ev.verdict_shortcuts(rows)
    assert kind == "info"
    assert "Bei r = 1 sinkt die Rundenzahl von 49 (ohne Abkürzungen) auf 4 (β = 100 %)." in text
    assert "Bei r = 2 sinkt sie zunächst von 74 auf 25 (β = 20 %)." in text
    assert "Ab β = 30 % füllt die Ausbreitung mit r = 2 das Netz in höchstens der Hälfte der Läufe (Endanteil dort 7 %)" in text
    assert ev.verdict_shortcuts(rows[:1])[0] == "warning"
    no_tip = ev.verdict_shortcuts([_srow(0.0, 1, 1, 1), _srow(0.1, 1, 1, 1)])[1]
    assert "Im untersuchten Bereich bleibt r = 2 vollständig." in no_tip


def test_verdict_watts_compares_inside_and_outside_of_the_window():
    lo, hi = A.vulnerable_window(C.WATTS_THETA)
    rows = [{"z": 0.5, "frac": 0.0, "size": NAN, "margin": -0.25, "runs": 100}, {"z": 3.0, "frac": 0.9, "size": 0.9, "margin": 2.8, "runs": 100},
            {"z": 4.0, "frac": 0.7, "size": 0.9, "margin": 2.9, "runs": 100}, {"z": 8.0, "frac": 0.2, "size": NAN, "margin": -5.0, "runs": 100}]
    kind, text = ev.verdict_watts(rows)
    assert kind == "info" and f"für {ev.de(lo, 2)} < z < {ev.de(hi, 2)} voraus" in text and "(K* = 5)" in text
    assert "innerhalb dieses Fensters im Mittel 80 % der Einzelstarter" in text and "außerhalb 10 % (Mittel über die gewählten Messpunkte" in text
    assert ev.verdict_watts(rows[1:3])[0] == "warning" and ev.verdict_watts(rows, theta=0.5)[0] == "warning"
    assert ev.verdict_watts([r for r in rows if r["z"] < 3])[0] == "warning"


def _crow(c, inside, own, other):
    return {"c": c, "inside": inside, "total": (own + other) / 2, "own": own, "other": other}


def test_verdict_communities_names_the_first_inside_share_that_holds_the_spread():
    rows = [_crow(8, 0.9, 1.0, 0.995), _crow(8, 0.93, 1.0, 0.4), _crow(8, 0.95, 1.0, 0.0), _crow(8, 0.97, 1.0, 0.0),
            _crow(12, 0.95, 1.0, 1.0), _crow(12, 0.99, 1.0, 0.5)]
    kind, text = ev.verdict_communities(rows, C.RULE_COUNT, 2, 34)
    assert kind == "info" and text.startswith("Mit Schwelle r = 2 hält ein Verbund die Ausbreitung auf: ")
    assert "bei mittlerem Grad 8 ab 95 % der Kanten innen (dort 100 % im eigenen Verbund, 0 % außerhalb)" in text
    assert "bei mittlerem Grad 12 auch bei 99 % innen nicht (außerhalb 50 %)" in text and "Für die einfache Ansteckung (r = 1) gibt es keine solche Grenze." in text
    assert ev.verdict_communities([], C.RULE_COUNT, 2, 34)[0] == "warning"


def _brow(mode, w, c1, c2, c3):
    return {"mode": mode, "w": w, "cells": {1: {"other": 1.0, "cross": c1}, 2: {"other": 0.0, "cross": c2}, 3: {"other": 0.0, "cross": c3}}}


def test_first_crossing_and_verdict_bridge_by_hand():
    rows = [_brow(C.BRIDGE_WIDE, 1, 1, 0, 0), _brow(C.BRIDGE_WIDE, 2, 1, 0.88, 0), _brow(C.BRIDGE_WIDE, 3, 1, 1, 0.12), _brow(C.BRIDGE_WIDE, 4, 1, 1, 0.7),
            _brow(C.BRIDGE_SPREAD, 1, 1, 0, 0), _brow(C.BRIDGE_SPREAD, 2, 1, 0, 0), _brow(C.BRIDGE_SPREAD, 3, 1, 0, 0), _brow(C.BRIDGE_SPREAD, 4, 1, 0, 0)]
    assert ev.first_crossing(rows, C.BRIDGE_WIDE, 1) == 1 and ev.first_crossing(rows, C.BRIDGE_WIDE, 2) == 2 and ev.first_crossing(rows, C.BRIDGE_WIDE, 3) == 4
    assert ev.first_crossing(rows, C.BRIDGE_SPREAD, 2) is None and ev.first_crossing(rows, C.BRIDGE_WIDE, 3) == 4
    exactly_half = [_brow(C.BRIDGE_WIDE, 1, 0.5, 0.49, 0)]
    assert ev.first_crossing(exactly_half, C.BRIDGE_WIDE, 1) == 1 and ev.first_crossing(exactly_half, C.BRIDGE_WIDE, 2) is None
    kind, text = ev.verdict_bridge(rows)
    assert kind == "info" and "r = 1: breit ab Breite 1, verteilt ab Breite 1" in text and "r = 2: breit ab Breite 2, verteilt nie (bis Breite 4)" in text
    assert "r = 3: breit ab Breite 4, verteilt nie (bis Breite 4)" in text and "tragen eine Schwelle ab 2 gar nicht" in text
    leaky = rows[:4] + [_brow(C.BRIDGE_SPREAD, 4, 1, 0.6, 0)]
    assert "tragen eine Schwelle ab 2 gar nicht" not in ev.verdict_bridge(leaky)[1]
    assert "tragen eine Schwelle ab 2 gar nicht" not in ev.verdict_bridge(rows[:4])[1]
    assert ev.verdict_bridge([])[0] == "warning"
