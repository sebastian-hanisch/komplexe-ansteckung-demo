"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button, fährt jeden Slider an seine Grenzen,
prüft Permalink, Netztypen, Regeln und alle fünf Experimente; es darf kein Python-Fehler auftreten."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import kpa_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
EXPERIMENTS = ("types", "shortcuts", "watts", "communities", "bridge")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert _metric(at, "Betriebe / Partnerschaften") == "150 / 450" and _metric(at, "Startgruppe") == "5 Betriebe"
    assert _metric(at, "Übernommen am Ende") == "150 von 150" and _metric(at, "Runden") == "36"
    assert any("Die Ausbreitung füllt das Netz" in s.value for s in at.success) and not at.error and not at.warning


def test_every_preset_click_does_not_raise():
    for name in C.PRESETS:
        at = _fresh_app()
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_all_sliders_at_their_minimum_and_all_at_their_maximum_do_not_raise():
    for edge in ("min", "max"):
        at = _fresh_app()
        for index in range(len(at.slider)):
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("typ", C.ALL_TYPES)
def test_every_network_type_renders_with_both_rules(typ):
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(typ).run(timeout=TIMEOUT)
    assert not at.exception
    for rule in C.RULES:
        at.selectbox(key="rule_select").set_value(rule).run(timeout=TIMEOUT)
        assert not at.exception, (typ, rule, [str(e) for e in at.exception])


def test_the_round_slider_walks_through_the_spread():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_RANDOM).run(timeout=TIMEOUT)
    round_slider = next(s for s in at.slider if s.label == "Runde")
    for t in range(int(round_slider.min), int(round_slider.max) + 1):
        round_slider.set_value(t).run(timeout=TIMEOUT)
        assert not at.exception, t
        round_slider = next(s for s in at.slider if s.label == "Runde")
    assert any("knapp davor" in c.value for c in at.caption)


def test_a_stuck_spread_is_reported_as_info_with_the_one_short_nodes():
    at = _fresh_app()
    at.sidebar.button(key="preset_Gemeinschaften halten auf").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Im Verbund des Startknotens haben 100 % übernommen, in den übrigen 0 %." in i.value for i in at.info)
    assert _metric(at, "Übernommen am Ende").startswith("25 von 150")


def test_permalink_values_are_clamped_and_unknown_choices_ignored():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "5"
    at.query_params["c"] = "99"
    at.query_params["beta"] = "-4"
    at.query_params["innen"] = "500"
    at.query_params["g"] = "0"
    at.query_params["typ"] = "gibt es nicht"
    at.query_params["regel"] = "Unsinn"
    at.query_params["bruecke"] = "Unsinn"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.slider(key="n_slider").value == C.N_MIN and at.slider(key="c_slider").value == C.C_MAX and at.slider(key="beta_slider").value == C.BETA_MIN
    assert at.slider(key="inside_slider").value == C.INSIDE_MAX and at.slider(key="g_slider").value == C.G_MIN
    assert at.selectbox(key="netztyp_select").value == C.T_RING and at.selectbox(key="rule_select").value == C.DEFAULT_RULE and at.selectbox(key="mode_select").value == C.BRIDGE_WIDE


def test_permalink_selects_a_network_type_a_rule_and_a_bridge():
    at = AppTest.from_file(APP_PATH)
    at.query_params["typ"] = C.T_TWO_GROUPS
    at.query_params["regel"] = C.RULE_SHARE
    at.query_params["bruecke"] = C.BRIDGE_SPREAD
    at.query_params["theta"] = "20"
    at.run(timeout=TIMEOUT)
    assert not at.exception and at.selectbox(key="netztyp_select").value == C.T_TWO_GROUPS and at.selectbox(key="rule_select").value == C.RULE_SHARE
    assert at.selectbox(key="mode_select").value == C.BRIDGE_SPREAD and at.slider(key="theta_slider").value == 20


def test_every_experiment_runs_and_is_invalidated_by_a_setting_change():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.slider(key="n_slider").set_value(C.N_MIN).run(timeout=TIMEOUT)         # kleines Netz: schnell
    for name in EXPERIMENTS:
        at.button(key=f"run_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
    texts = " ".join(x.value for x in list(at.info) + list(at.warning) + list(at.success))
    for fragment in ("füllt die Ausbreitung (mindestens 90 %", "Bei r = 1 sinkt die Rundenzahl", "sagt Kaskaden für", "hält ein Verbund die Ausbreitung auf", "Die andere Gruppe wird in mindestens der Hälfte"):
        assert fragment in texts, fragment
    at.slider(key="n_slider").set_value(C.N_MIN + 10).run(timeout=TIMEOUT)
    assert not at.exception
    assert sum("neu starten" in i.value for i in at.info) >= len(EXPERIMENTS) - 1       # alle von n abhängigen Ergebnisse sind ungültig (das Kaskadenfenster hängt von keiner Einstellung ab)
