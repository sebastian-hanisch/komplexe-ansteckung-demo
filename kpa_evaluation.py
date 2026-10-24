"""Kennzahlen, Messreihen und Verdikte der Demo „Komplexe Ansteckung“. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Protokoll: deterministische Schwelle (ein Knoten übernimmt, sobald r seiner Partner übernommen haben, oder ein Anteil θ seiner Partner); synchrone Runden bis zum Fixpunkt.
Gestartet wird mit einer Startgruppe (ein Knoten und bis zu g − 1 seiner Partner). Jede Messreihe nimmt gepoolt alle Läufe über feste Netze (`LIVE_SEEDS` in der App,
`SWEEP_SEEDS` für die README-Zahlen) und je Netz `STARTS_PER_NET` Startgruppen; ausgewiesen werden der Median des Endanteils, der Anteil der Läufe mit mindestens `FULL_SHARE`
(„vollständig“) und die Rundenzahl der vollständigen Läufe."""

import math
from dataclasses import dataclass
from statistics import median

import numpy as np

import kpa_algorithm as A
import kpa_constants as C
from kpa_scenario import Instance, make_instance

NAN = float("nan")


def de(x, digits=1) -> str:
    """Dezimalzahl mit Komma (deutsche Texte); eine nicht definierte Zahl erscheint als Gedankenstrich."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{digits}f}".replace(".", ",")


def runden(k) -> str:
    return "1 Runde" if k == 1 else f"{k} Runden"


def knapp(k) -> str:
    """Satz über die Betriebe, denen genau ein Partner zur Schwelle fehlt."""
    return "1 Knoten ist knapp davor (ihm fehlt genau ein Partner)." if k == 1 else f"{k} Knoten sind knapp davor (ihnen fehlt genau ein Partner)."


def _med(values) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return float(median(vals)) if vals else NAN


def rule_kwargs(rule, r, theta_pct) -> dict:
    """Parameter für den Kern: Zahlregel r oder Anteilsregel θ (Prozent in Anteil umgerechnet)."""
    return {"r": int(r)} if rule == C.RULE_COUNT else {"theta": theta_pct / 100.0}


def rule_text(rule, r, theta_pct) -> str:
    if rule == C.RULE_COUNT:
        return f"Schwelle r = {r}" + (" (ein übernommener Partner genügt)" if r == 1 else "")
    return f"Schwelle θ = {theta_pct} % der Partner"


# --- Hauptanalyse -----------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    netztyp: str = C.T_RING
    n: int = C.DEFAULT_N
    c: int = C.DEFAULT_C
    seed: int = C.DEFAULT_SEED
    beta: int = C.DEFAULT_BETA
    inside: int = C.DEFAULT_INSIDE
    width: int = C.DEFAULT_WIDTH
    mode: str = C.BRIDGE_WIDE
    rule: str = C.DEFAULT_RULE
    r: int = C.DEFAULT_R
    theta: int = C.DEFAULT_THETA
    g: int = C.DEFAULT_G


@dataclass(frozen=True, eq=False)
class Analysis:
    inst: Instance
    settings: Settings
    seeds: tuple
    spread: A.Spread
    reference: A.Spread          # dieselbe Startgruppe mit Schwelle r = 1 (einfache Ansteckung)
    need: np.ndarray             # nötige Zahl übernommener Partner je Knoten
    short: tuple                 # Knoten, denen am Ende genau ein Partner zur Schwelle fehlt
    start_share: float           # Endanteil in der Gruppe des Startknotens (nur bei Netzen mit Gruppen, sonst nan)
    other_share: float           # Endanteil außerhalb davon (nur bei Netzen mit Gruppen, sonst nan)
    compare: dict                # Beschriftung -> Spread derselben Startgruppe bei r = 1, 2, 3 und bei der gewählten Regel
    selected: str                # Beschriftung der gewählten Regel in `compare`

    @property
    def kwargs(self) -> dict:
        return rule_kwargs(self.settings.rule, self.settings.r, self.settings.theta)


def group_shares(inst: Instance, spread: A.Spread, start_node) -> tuple[float, float]:
    """Endanteil in der Gruppe des Startknotens und in allen anderen Gruppen; (nan, nan), wenn das Netz keine Gruppen hat."""
    if inst.groups is None:
        return NAN, NAN
    lab = np.array(inst.groups)
    ad = np.array([x >= 0 for x in spread.round_of])
    own = lab == lab[start_node]
    return (float(ad[own].mean()) if own.any() else NAN), (float(ad[~own].mean()) if (~own).any() else NAN)


def rule_label(rule, r, theta_pct) -> str:
    """Kurzbeschriftung der Regel für Diagramme: „r = 2“ oder „θ = 34 %“."""
    return f"r = {r}" if rule == C.RULE_COUNT else f"θ = {theta_pct} %"


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.netztyp, settings.n, settings.c, settings.seed, beta=settings.beta / 100.0, inside=settings.inside / 100.0,
                         width=settings.width, mode=settings.mode, layout=True)
    kw = rule_kwargs(settings.rule, settings.r, settings.theta)
    if inst.m == 0:
        empty = A.Spread((-1,) * inst.n, 0)
        return Analysis(inst, settings, (), empty, empty, A.need_vector(inst.adj, **kw), (), NAN, NAN, {}, rule_label(settings.rule, settings.r, settings.theta))
    seeds = A.group_seed(inst.adj, min(settings.g, inst.n), settings.seed)
    spread = A.threshold_spread(inst.adj, seeds, **kw)
    reference = A.threshold_spread(inst.adj, seeds, r=1)
    short = A.one_short(inst.adj, A.adopted_by(spread, spread.rounds), **kw)
    own, other = group_shares(inst, spread, seeds[0])
    label = rule_label(settings.rule, settings.r, settings.theta)
    compare = {f"r = {r}": A.threshold_spread(inst.adj, seeds, r=r) for r in sorted(set(C.THRESHOLDS) | ({settings.r} if settings.rule == C.RULE_COUNT else set()))}
    compare[label] = spread
    return Analysis(inst, settings, seeds, spread, reference, A.need_vector(inst.adj, **kw), short, own, other, compare, label)


def verdict_main(an: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage: füllt die Ausbreitung das Netz, und wenn nicht, woran hängt sie?"""
    st = an.settings
    if an.inst.m == 0:
        return "warning", "Das Netz hat keine Kanten: es gibt keine Partner, über die sich etwas ausbreiten könnte."
    n, sp = an.inst.n, an.spread
    when = f", nach {runden(sp.rounds)}" if sp.rounds > 0 else ", ohne dass in einer Runde jemand dazukam"
    head = f"Startgruppe aus {len(an.seeds)} Knoten, {rule_text(st.rule, st.r, st.theta)}: am Ende haben {sp.count} von {n} Knoten übernommen ({de(100 * sp.share, 0)} %){when}."
    simple = st.rule == C.RULE_COUNT and st.r == 1
    ref = "" if simple else (f" Zum Vergleich erreicht die einfache Ansteckung (r = 1) mit derselben Startgruppe {de(100 * an.reference.share, 0)} % nach {runden(an.reference.rounds)}.")
    groups = ""
    if not math.isnan(an.start_share):
        groups = f" Im Verbund des Startknotens haben {de(100 * an.start_share, 0)} % übernommen, in den übrigen {de(100 * an.other_share, 0)} %."
    if sp.share >= C.FULL_SHARE:
        return "success", head + " Die Ausbreitung füllt das Netz." + ref + groups
    if sp.count <= len(an.seeds):
        text = (head + " Sie kommt nicht aus der Startgruppe heraus: kein Knoten außerhalb hat genug übernommene Partner."
                + (f" {knapp(len(an.short))}" if an.short else " Auch knapp davor ist kein Knoten.") + ref + groups)
        return "info", text
    return "info", head + " Sie bleibt stehen, bevor das Netz voll ist." + (f" {knapp(len(an.short))}" if an.short else "") + ref + groups


# --- Messhilfen -------------------------------------------------------------------------------------------------------------------------------------


def run_batch(adj, g, net_seed, starts, within=None, **rule) -> list[tuple]:
    """Läufe von `starts` Startgruppen auf einem Netz: Liste von (Startgruppe, Spread). Netze ohne Kante liefern nichts."""
    out = []
    for i in range(starts):
        try:
            seeds = A.group_seed(adj, g, net_seed * 1000 + i, within)
        except ValueError:
            return out
        out.append((seeds, A.threshold_spread(adj, seeds, **rule)))
    return out


def cell_stats(spreads) -> dict:
    """Endanteil (Median), Anteil der vollständigen Läufe (mindestens FULL_SHARE) und Rundenzahl der vollständigen Läufe (Median) über eine Liste von Spreads."""
    if not spreads:
        return {"share": NAN, "full": NAN, "rounds": NAN, "runs": 0}
    shares = [s.share for s in spreads]
    full = [s for s in spreads if s.share >= C.FULL_SHARE]
    return {"share": float(median(shares)), "full": len(full) / len(spreads), "rounds": _med([float(s.rounds) for s in full]), "runs": len(spreads)}


# --- E1: Netztypen und Schwellen -------------------------------------------------------------------------------------------------------------------


def type_rows(n, c, g, seeds=C.LIVE_SEEDS, starts=C.STARTS_PER_NET, thresholds=C.THRESHOLDS, cases=C.TYPE_CASES) -> list[dict]:
    """Je Netztyp und Schwelle r: Endanteil, Anteil vollständiger Läufe und Rundenzahl (gepoolt über die festen Netze und Startgruppen)."""
    rows = []
    for label, typ, beta, inside in cases:
        per_r = {r: [] for r in thresholds}
        for seed in seeds:
            adj = make_instance(typ, n, c, seed, beta=beta, inside=inside, layout=False).adj
            for r in thresholds:
                per_r[r] += [sp for _, sp in run_batch(adj, g, seed, starts, r=r)]
        rows.append({"label": label, "typ": typ, "cells": {r: cell_stats(per_r[r]) for r in thresholds}})
    return rows


def verdict_types(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E1: in wie vielen Netztypen füllt die Ausbreitung das Netz, je Schwelle?"""
    valid = [r for r in rows if r["cells"] and not all(math.isnan(c["share"]) for c in r["cells"].values())]
    if not valid:
        return "warning", "Keine Läufe möglich."
    thresholds = sorted(valid[0]["cells"])
    parts = []
    for r in thresholds:
        fills = [row["label"] for row in valid if row["cells"][r]["share"] >= C.FULL_SHARE]
        parts.append(f"bei r = {r} in {len(fills)} von {len(valid)} Netztypen" + (f" ({', '.join(fills)})" if 0 < len(fills) < len(valid) else ""))
    return "info", f"Im Median füllt die Ausbreitung (mindestens {de(100 * C.FULL_SHARE, 0)} % der Knoten) das Netz " + "; ".join(parts) + ". Eine höhere Schwelle trägt in keinem Netz weiter als eine niedrigere."


# --- E2: Abkürzungen im Ring ------------------------------------------------------------------------------------------------------------------------


def shortcut_rows(n, c, g, betas=C.SHORTCUT_BETAS, seeds=C.LIVE_SEEDS, starts=C.STARTS_PER_NET, thresholds=C.THRESHOLDS) -> list[dict]:
    """Ring mit Umverdrahtungsanteil β: Endanteil, Anteil vollständiger Läufe und Rundenzahl je Schwelle."""
    rows = []
    for beta in betas:
        per_r = {r: [] for r in thresholds}
        for seed in seeds:
            adj = make_instance(C.T_RING, n, c, seed, beta=beta, layout=False).adj
            for r in thresholds:
                per_r[r] += [sp for _, sp in run_batch(adj, g, seed, starts, r=r)]
        rows.append({"beta": beta, "cells": {r: cell_stats(per_r[r]) for r in thresholds}})
    return rows


def tipping_beta(rows: list[dict], r, level=0.5):
    """Kleinstes β, ab dem höchstens der Anteil `level` der Läufe vollständig ist (der Kipppunkt der Schwelle r); None, wenn es keinen gibt."""
    for row in rows:
        if row["cells"][r]["full"] <= level:
            return row["beta"]
    return None


def verdict_shortcuts(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E2: Abkürzungen beschleunigen die einfache Ansteckung; die Schwelle 2 braucht gemeinsame Partner und kippt."""
    if len(rows) < 2:
        return "warning", "Zu wenige Messpunkte."
    first, last = rows[0], rows[-1]
    r1_first, r1_last = first["cells"][1]["rounds"], last["cells"][1]["rounds"]
    r2 = [(row["beta"], row["cells"][2]["rounds"]) for row in rows if row["cells"][2]["full"] > 0.5]
    tip = tipping_beta(rows, 2)
    text = f"Bei r = 1 sinkt die Rundenzahl von {de(r1_first, 0)} (ohne Abkürzungen) auf {de(r1_last, 0)} (β = {de(100 * last['beta'], 0)} %). "
    if r2:
        best = min(r2, key=lambda x: x[1])
        text += f"Bei r = 2 sinkt sie zunächst von {de(r2[0][1], 0)} auf {de(best[1], 0)} (β = {de(100 * best[0], 0)} %). "
    if tip is not None:
        text += (f"Ab β = {de(100 * tip, 0)} % füllt die Ausbreitung mit r = 2 das Netz in höchstens der Hälfte der Läufe (Endanteil dort {de(100 * next(r['cells'][2]['share'] for r in rows if r['beta'] == tip), 0)} %): "
                 "die Abkürzungen nehmen die gemeinsamen Partner, auf die sie angewiesen ist.")
    else:
        text += "Im untersuchten Bereich bleibt r = 2 vollständig."
    return "info", text


# --- E3: Watts-Kaskaden -----------------------------------------------------------------------------------------------------------------------------


def watts_rows(theta=C.WATTS_THETA, n=C.WATTS_N, zs=C.WATTS_ZS, seeds=C.LIVE_SEEDS, starts=C.WATTS_STARTS, big=0.05) -> list[dict]:
    """Ein einzelner Startknoten im Zufallsnetz G(n, m) mit mittlerem Grad z und der Anteilsregel θ: Anteil der Läufe mit einer Kaskade über `big` der Knoten, mittlere Größe der großen Kaskaden
    und der Vorhersagewert der Formel (positiv = Fenster)."""
    rows = []
    for z in zs:
        cascades, sizes = [], []
        for seed in seeds:
            adj = make_instance(C.T_RANDOM, n, z, seed, layout=False).adj
            for _, sp in run_batch(adj, 1, seed, starts, theta=theta):
                cascades.append(sp.share > big)
                if sp.share > big:
                    sizes.append(sp.share)
        rows.append({"z": z, "frac": float(np.mean(cascades)) if cascades else NAN, "size": _med(sizes), "margin": A.cascade_margin(z, theta), "runs": len(cascades)})
    return rows


def verdict_watts(rows: list[dict], theta=C.WATTS_THETA) -> tuple[str, str]:
    """Verdikt zu E3: tritt die Kaskade dort auf, wo die Formel das Fenster vorhersagt?"""
    window = A.vulnerable_window(theta)
    if window is None:
        return "warning", f"Für θ = {de(100 * theta, 0)} % sagt die Formel kein Kaskadenfenster voraus."
    inside = [r["frac"] for r in rows if window[0] < r["z"] < window[1] and not math.isnan(r["frac"])]
    outside = [r["frac"] for r in rows if not (window[0] < r["z"] < window[1]) and not math.isnan(r["frac"])]
    if not inside or not outside:
        return "warning", "Die Messpunkte liegen nicht beiderseits des Fensters."
    return "info", (f"Die Formel (K* = {A.vulnerable_max_degree(theta)}) sagt Kaskaden für {de(window[0], 2)} < z < {de(window[1], 2)} voraus. Gemessen lösen innerhalb dieses Fensters im Mittel "
                    f"{de(100 * float(np.mean(inside)), 0)} % der Einzelstarter eine Kaskade über 5 % der Knoten aus, außerhalb {de(100 * float(np.mean(outside)), 0)} % (Mittel über die gewählten Messpunkte; am Rand verschwimmt das Fenster). "
                    "Zu wenige Partner: der Start steckt in einem Stück fest. Zu viele: jeder Partner hat so viele Partner, dass ein einzelner nicht mehr überzeugt.")


# --- E4: Gemeinschaften -----------------------------------------------------------------------------------------------------------------------------


def community_rows(n, g, rule, r, theta_pct, insides=C.COMMUNITY_INSIDES, degrees=C.COMMUNITY_DEGREES, seeds=C.LIVE_SEEDS, starts=C.STARTS_PER_NET) -> list[dict]:
    """Verbünde (Blockmodell, 6 gleich große Gruppen) mit Anteil `inside` der Kanten innen: Endanteil gesamt, im Verbund des Startknotens und außerhalb (Median gepoolt über die festen Netze und Startgruppen)."""
    rule_kw = rule_kwargs(rule, r, theta_pct)
    rows = []
    for c in degrees:
        for inside in insides:
            tot, own, oth = [], [], []
            for seed in seeds:
                inst = make_instance(C.T_COMMUNITIES, n, c, seed, inside=inside, layout=False)
                for seeds_, sp in run_batch(inst.adj, g, seed, starts, **rule_kw):
                    o, x = group_shares(inst, sp, seeds_[0])
                    tot.append(sp.share)
                    own.append(o)
                    oth.append(x)
            rows.append({"c": c, "inside": inside, "total": _med(tot), "own": _med(own), "other": _med(oth)})
    return rows


def verdict_communities(rows: list[dict], rule, r, theta_pct) -> tuple[str, str]:
    """Verdikt zu E4: ab welchem Anteil innen hält ein Verbund die Ausbreitung auf?"""
    if not rows:
        return "warning", "Keine Läufe."
    parts = []
    for c in sorted({row["c"] for row in rows}):
        mine = [row for row in rows if row["c"] == c]
        stopped = [row for row in mine if row["other"] < 0.1]
        if stopped:
            first = min(stopped, key=lambda row: row["inside"])
            parts.append(f"bei mittlerem Grad {c} ab {de(100 * first['inside'], 0)} % der Kanten innen (dort {de(100 * first['own'], 0)} % im eigenen Verbund, {de(100 * first['other'], 0)} % außerhalb)")
        else:
            best = max(mine, key=lambda row: row["inside"])
            parts.append(f"bei mittlerem Grad {c} auch bei {de(100 * best['inside'], 0)} % innen nicht (außerhalb {de(100 * best['other'], 0)} %)")
    return "info", f"Mit {rule_text(rule, r, theta_pct)} hält ein Verbund die Ausbreitung auf: " + "; ".join(parts) + ". Für die einfache Ansteckung (r = 1) gibt es keine solche Grenze."


# --- E5: Brückenbreite ------------------------------------------------------------------------------------------------------------------------------


def bridge_rows(n, c, g, widths=C.BRIDGE_WIDTHS, modes=C.BRIDGE_MODES, thresholds=C.THRESHOLDS, seeds=C.LIVE_SEEDS, starts=C.STARTS_PER_NET) -> list[dict]:
    """Zwei Gruppen mit Brücke der Breite w: Anteil der anderen Gruppe, der erreicht wird (Median), und Anteil der Läufe, in denen mindestens die Hälfte der anderen Gruppe erreicht wird.
    Gestartet wird in der ersten Gruppe (Startknoten und Partner dort)."""
    rows = []
    for mode in modes:
        for w in widths:
            per_r = {r: [] for r in thresholds}
            for seed in seeds:
                inst = make_instance(C.T_TWO_GROUPS, n, c, seed, width=w, mode=mode, layout=False)
                first = [i for i, lab in enumerate(inst.groups) if lab == 0]
                for r in thresholds:
                    for _, sp in run_batch(inst.adj, g, seed, starts, within=first, r=r):
                        per_r[r].append(float(np.mean([sp.round_of[i] >= 0 for i, lab in enumerate(inst.groups) if lab == 1])))
            rows.append({"mode": mode, "w": w, "cells": {r: {"other": _med(per_r[r]), "cross": float(np.mean(np.array(per_r[r]) >= 0.5)) if per_r[r] else NAN} for r in thresholds}})
    return rows


def first_crossing(rows: list[dict], mode, r):
    """Kleinste Brückenbreite, bei der die Schwelle r in mindestens der Hälfte der Läufe die andere Gruppe zur Hälfte erreicht; None, wenn keine."""
    for row in sorted((x for x in rows if x["mode"] == mode), key=lambda x: x["w"]):
        if row["cells"][r]["cross"] >= 0.5:
            return row["w"]
    return None


def verdict_bridge(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E5: eine breite Brücke führt die Schwelle r ab einer Breite in die andere Gruppe (gemessen); dieselbe Kantenzahl mit verschiedenen Enden trägt sie nicht."""
    if not rows:
        return "warning", "Keine Läufe."
    modes = [m for m in C.BRIDGE_MODES if any(x["mode"] == m for x in rows)]
    rs = sorted(rows[0]["cells"])
    parts = []
    for r in rs:
        text = []
        for m in modes:
            f = first_crossing(rows, m, r)
            label = "breit" if m == C.BRIDGE_WIDE else "verteilt"
            text.append(f"{label} ab Breite {f}" if f is not None else f"{label} nie (bis Breite {max(x['w'] for x in rows)})")
        parts.append(f"r = {r}: " + ", ".join(text))
    spread_never = all(first_crossing(rows, C.BRIDGE_SPREAD, r) is None for r in rs if r >= 2) if C.BRIDGE_SPREAD in modes else False
    tail = (" Gleich viele Kanten mit verschiedenen Enden tragen eine Schwelle ab 2 gar nicht: auf der anderen Seite hätte jeder Tor-Knoten nur einen übernommenen Partner." if spread_never else "")
    return "info", "Die andere Gruppe wird in mindestens der Hälfte der Läufe zur Hälfte erreicht: " + "; ".join(parts) + "." + tail
