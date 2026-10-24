"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jedes Preset zeigt, wofür es benannt ist."""

import kpa_algorithm as A
import kpa_constants as C
import kpa_evaluation as ev
import kpa_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, p in C.PRESETS.items():
        assert p["netztyp"] in C.ALL_TYPES and C.N_MIN <= p["n"] <= C.N_MAX and C.C_MIN <= p["c"] <= C.C_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert C.BETA_MIN <= p["beta"] <= C.BETA_MAX and C.INSIDE_MIN <= p["inside"] <= C.INSIDE_MAX and C.WIDTH_MIN <= p["width"] <= C.WIDTH_MAX, name
        assert p["mode"] in C.BRIDGE_MODES and p["rule"] in C.RULES and C.R_MIN <= p["r"] <= C.R_MAX and C.THETA_MIN <= p["theta"] <= C.THETA_MAX and C.G_MIN <= p["g"] <= C.G_MAX, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[C.DEFAULT_PRESET_NAME]) == ev.Settings()
    assert next(iter(C.PRESETS)) == C.DEFAULT_PRESET_NAME


def test_setting_specs_cover_every_preset_key_and_defaults_match():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key, state_key in P.PRESET_KEYS.items():
        assert P.SETTING_SPECS[state_key].default == C.PRESETS[C.DEFAULT_PRESET_NAME][key], key


def test_every_preset_differs_from_the_default_in_something_besides_the_network_type():
    default = C.PRESETS[C.DEFAULT_PRESET_NAME]
    for name, p in C.PRESETS.items():
        if name != C.DEFAULT_PRESET_NAME:
            assert any(p[k] != default[k] for k in p if k != "netztyp"), name


def test_presets_cover_the_teaching_cases():
    ps = C.PRESETS.values()
    assert {p["netztyp"] for p in ps} >= {C.T_RING, C.T_RANDOM, C.T_COMMUNITIES, C.T_TWO_GROUPS, C.T_BA}
    assert any(p["rule"] == C.RULE_SHARE for p in ps) and any(p["g"] == 1 for p in ps)


def test_each_preset_shows_what_its_name_says():
    full = {name: ev.analyse(_settings(name)) for name in C.PRESETS}
    assert full["Ring ohne Abkürzungen (Voreinstellung)"].spread.share == 1.0 and full["Ring ohne Abkürzungen (Voreinstellung)"].spread.rounds > full["Ring ohne Abkürzungen (Voreinstellung)"].reference.rounds
    tip = full["Abkürzungen: der Kipppunkt"]
    assert tip.spread.share < 0.2 and tip.reference.share == 1.0                                # r = 1 füllt, r = 2 steckt fest
    rnd = full["Zufallsnetz: kaum gemeinsame Partner"]
    assert rnd.spread.share < 0.2 and rnd.reference.share >= C.FULL_SHARE                              # einzelne Betriebe ohne Verbindung bleiben auch bei r = 1 draußen
    com = full["Gemeinschaften halten auf"]
    assert com.start_share == 1.0 and com.other_share == 0.0 and com.reference.share == 1.0     # der eigene Verbund ist voll, außerhalb nichts
    bridge = full["Brücke zu schmal"]
    assert bridge.start_share == 1.0 and bridge.other_share == 0.0 and bridge.reference.share == 1.0
    share = full["Anteilsregel: Hubs sind schwer zu überzeugen"]
    assert share.spread.share < 0.2 and share.reference.share >= C.FULL_SHARE
    cascade = full["Kaskadenfenster: ein Startbetrieb genügt"]
    assert len(cascade.seeds) == 1 and cascade.spread.share > 0.5


def test_every_preset_runs_and_the_verdict_is_a_known_kind():
    for name in C.PRESETS:
        an = ev.analyse(_settings(name))
        assert an.inst.n >= 2
        assert ev.verdict_main(an)[0] in ("success", "info", "warning"), name
        assert A.threshold_spread(an.inst.adj, an.seeds, **an.kwargs) == an.spread
