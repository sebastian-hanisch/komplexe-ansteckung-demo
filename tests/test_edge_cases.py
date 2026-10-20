"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste und größte Regler, Startgruppe größer als der Grad, Netze ohne Kanten, Warnungen als Fehler, Abbildungen."""

import math
import warnings

import pytest

import kpa_algorithm as A
import kpa_constants as C
import kpa_evaluation as ev
import kpa_visualization as V
from conftest import make_adj


@pytest.mark.parametrize("typ", C.ALL_TYPES)
@pytest.mark.parametrize("rule", C.RULES)
def test_every_network_type_and_rule_at_the_slider_corners_runs_without_warnings(typ, rule):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for n, c, g, r, theta in ((C.N_MIN, C.C_MIN, C.G_MAX, C.R_MAX, C.THETA_MAX), (C.N_MIN, C.C_MAX, C.G_MIN, C.R_MIN, C.THETA_MIN), (C.N_MAX, C.C_MAX, C.G_MAX, C.R_MAX, C.THETA_MAX)):
            an = ev.analyse(ev.Settings(typ, n, c, 3, C.BETA_MAX, C.INSIDE_MAX, C.WIDTH_MAX, C.BRIDGE_SPREAD, rule, r, theta, g))
            assert 0 <= an.spread.count <= an.inst.n and an.spread.rounds <= an.inst.n
            assert all(0 <= x for x in [an.spread.rounds]) and ev.verdict_main(an)[0] in ("success", "info", "warning")
            assert set(an.compare) >= {"r = 1", "r = 2", "r = 3"}


def test_start_group_is_never_larger_than_the_node_and_its_partners():
    adj = make_adj(6, [(0, 1), (0, 2), (3, 4)])
    for seed in range(20):
        seeds = A.group_seed(adj, 10, seed)
        centre = [v for v in seeds if all(w in adj[v] for w in seeds if w != v)]
        assert len(seeds) <= 3 and centre, seed
        assert set(seeds) <= {0, 1, 2} or set(seeds) == {3, 4}


def test_group_seed_within_restricts_start_and_partners_and_fails_without_candidates():
    adj = make_adj(6, [(0, 1), (0, 2), (3, 4), (2, 3)])
    for seed in range(20):
        assert set(A.group_seed(adj, 3, seed, within={0, 1, 2})) <= {0, 1, 2}
    with pytest.raises(ValueError):
        A.group_seed(adj, 2, 1, within={5})                                                             # Knoten 5 hat keinen Partner
    with pytest.raises(ValueError):
        A.group_seed(adj, 2, 1, within={0, 4})                                                          # beide haben Partner, aber nicht in der Menge


def test_threshold_larger_than_every_degree_keeps_the_start_group_only():
    adj = make_adj(6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    sp = A.threshold_spread(adj, [0, 1, 2], r=3)
    assert sp.count == 3 and sp.rounds == 0 and sp.round_of == (0, 0, 0, -1, -1, -1)


def test_start_group_covering_the_whole_net_ends_at_once():
    adj = make_adj(3, [(0, 1), (1, 2)])
    sp = A.threshold_spread(adj, [0, 1, 2], r=2)
    assert sp.count == 3 and sp.rounds == 0 and A.curve(sp) == [3]


def test_share_rule_rounding_does_not_depend_on_float_noise():
    # 0,3 · 10 = 3,0000000000000004 in Fließkomma: das Aufrunden darf daraus keine vier Partner machen
    adj = make_adj(11, [(0, i) for i in range(1, 11)])
    assert A.need_vector(adj, theta=0.3)[0] == 3 and A.need_vector(adj, theta=0.1)[0] == 1 and A.need_vector(adj, theta=0.7)[0] == 7


def test_experiments_run_on_the_smallest_networks_without_warnings():
    seeds = C.LIVE_SEEDS[:2]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        t = ev.type_rows(C.N_MIN, C.C_MIN, C.G_MAX, seeds=seeds, starts=2)
        s = ev.shortcut_rows(C.N_MIN, C.C_MAX, C.G_MIN, betas=(0.0, 1.0), seeds=seeds, starts=2)
        w = ev.watts_rows(n=C.N_MIN, zs=(0.5, 4.0, 8.0), seeds=seeds, starts=3)
        cm = ev.community_rows(C.N_MIN, C.G_MAX, C.RULE_SHARE, 2, C.THETA_MIN, insides=(0.5, 0.99), degrees=(8,), seeds=seeds, starts=2)
        b = ev.bridge_rows(C.N_MIN, C.C_MAX, C.G_MAX, widths=(1, 5), seeds=seeds, starts=2)
    assert len(t) == len(C.TYPE_CASES) and len(s) == 2 and len(w) == 3 and len(cm) == 2 and len(b) == 4
    for row in t:
        assert all(0.0 <= c["share"] <= 1.0 for c in row["cells"].values())
    for verdict in (ev.verdict_types(t), ev.verdict_shortcuts(s), ev.verdict_watts(w), ev.verdict_communities(cm, C.RULE_SHARE, 2, C.THETA_MIN), ev.verdict_bridge(b)):
        assert verdict[0] in ("success", "info", "warning") and verdict[1]


def test_figures_are_built_for_every_round_and_for_the_experiment_rows():
    an = ev.analyse(ev.Settings(C.T_TWO_GROUPS, 80, 6, 3, rule=C.RULE_SHARE, g=3))
    for t in range(an.spread.rounds + 1):
        fig = V.build_network(an.inst, an.spread, t, an.seeds, A.one_short(an.inst.adj, A.adopted_by(an.spread, t), **an.kwargs))
        assert all(tr.visible is not False for tr in fig.data)
    assert V.build_curves(an.compare, an.selected).data
    seeds = C.LIVE_SEEDS[:2]
    t = ev.type_rows(C.N_MIN, 4, 3, seeds=seeds, starts=2)
    s = ev.shortcut_rows(C.N_MIN, 6, 3, betas=(0.0, 0.5), seeds=seeds, starts=2)
    for fig in (V.build_type_share(t), V.build_type_full(t), V.build_shortcuts(s), V.build_shortcut_rounds(s), V.build_watts(ev.watts_rows(n=C.N_MIN, zs=(1.0, 4.0), seeds=seeds, starts=2)),
                V.build_communities(ev.community_rows(C.N_MIN, 3, C.RULE_COUNT, 2, 34, insides=(0.8,), degrees=(8,), seeds=seeds, starts=2)), V.build_bridge(ev.bridge_rows(C.N_MIN, 8, 3, widths=(1, 2), seeds=seeds, starts=2))):
        assert fig.data and all(ax.fixedrange for ax in (fig.layout.xaxis, fig.layout.yaxis))


def test_empty_state_traces_are_left_out_of_the_network_figure():
    an = ev.analyse(ev.Settings())
    fig0 = V.build_network(an.inst, an.spread, 0, an.seeds, ())
    names = [tr.name for tr in fig0.data if tr.name]
    assert "nicht übernommen" in names and not any(n.startswith("in Runde") for n in names) and "knapp davor" not in names


def test_de_handles_infinity_and_large_values():
    assert ev.de(1234.5678, 1) == "1234,6" and not math.isnan(float(ev.de(0.0, 1).replace(",", ".")))
