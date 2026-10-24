"""Komplexe Ansteckung: wann reicht ein Kontakt? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Sechstes Stück der Reihe „Netzwerkanalyse“: ein Betrieb übernimmt ein neues Verfahren, sobald genug seiner Partner es tun (Schwelle als Zahl r oder als Anteil θ).
Die Demo stellt die einfache Ansteckung (ein Partner genügt) der komplexen gegenüber und zeigt Kipppunkt bei Abkürzungen, Grenzen an Gemeinschaften, die Breite von Brücken und das Kaskadenfenster nach Watts.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import kpa_constants as C
from kpa_evaluation import (
    Settings,
    analyse,
    bridge_rows,
    community_rows,
    de,
    rule_kwargs,
    rule_text,
    shortcut_rows,
    type_rows,
    verdict_bridge,
    verdict_communities,
    verdict_main,
    verdict_shortcuts,
    verdict_types,
    verdict_watts,
    watts_rows,
)
from kpa_algorithm import adopted_by, one_short
from kpa_layout import dunkles_design, kopf_css
from kpa_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kpa_visualization import (
    build_bridge,
    build_communities,
    build_curves,
    build_network,
    build_shortcut_rounds,
    build_shortcuts,
    build_type_full,
    build_type_share,
    build_watts,
)

st.set_page_config(page_title="Komplexe Ansteckung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _types(n, c, g):
    return type_rows(n, c, g)


@st.cache_data(show_spinner=False)
def _shortcuts(n, c, g):
    return shortcut_rows(n, c, g)


@st.cache_data(show_spinner=False)
def _watts():
    return watts_rows()


@st.cache_data(show_spinner=False)
def _communities(n, g, rule, r, theta):
    return community_rows(n, g, rule, r, theta)


@st.cache_data(show_spinner=False)
def _bridge(n, c, g):
    return bridge_rows(n, c, g)


def experiment(name, label, key, compute, show, hint):
    """Teure Zusatzansicht erst auf Klick; das Ergebnis bleibt nur für genau diese Einstellungen stehen (Session State)."""
    state_key = f"exp_{name}"
    if st.button(label, key=f"run_{name}", help=hint):
        with st.spinner("Rechne …"):
            result = compute()
        st.session_state[state_key] = (key, result)
    state = st.session_state.get(state_key)
    if state is None:
        st.caption(f"Noch nicht gerechnet. {hint}")
        return
    if state[0] != key:
        st.info("Die Einstellungen haben sich seit der letzten Rechnung geändert. Bitte neu starten.")
        return
    show(state[1])


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kpa_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Komplexe Ansteckung: wann reicht ein Kontakt?")
st.markdown(
    """
**Sechstes Stück** der Reihe „Netzwerkanalyse“, im Ausbreitungs-Arm die Fortsetzung von Stück 5 (Einflussmaximierung): Eine Nachricht verbreitet sich schon, wenn ein Partner sie weitergibt. Ein **Verfahrenswechsel** („wir stellen erst um, wenn zwei Partner es tun“) braucht mehrere. In einem Netz von Subunternehmern und Lieferanten übernimmt ein Betrieb das neue Verfahren, sobald mindestens ***r*** seiner Partner es getan haben, oder ein Anteil **θ** seiner Partner. Eine **Startgruppe** (ein Betrieb und seine Partner) beginnt. Die Demo stellt die **einfache Ansteckung** (*r* = 1) der **komplexen** (*r* = 2, 3 oder Anteil θ) gegenüber.

Die Kernfrage: **Wann reicht ein Kontakt, wann braucht es mehrere, und woran hängt es?** Der Befund hängt an der **Breite** der Verbindungen (mehrere gemeinsame Partner), nicht an der bloßen Zahl der Kanten: eine einzige Brücke trägt die einfache, aber nicht die komplexe Ansteckung. Anders als die Fall-Demos zeigt diese Demo **ein** Modell an einem wachsenden Beispiel; die Ergebnisse sind **Modellbefunde**, keine Aussagen über die Wirklichkeit.

Weiter unten: fünf Experimente (**🔬**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Schwellenregel", expanded=True):
    st.markdown(
        """
1. **Übernahme:** ein Betrieb übernimmt, sobald mindestens *r* seiner Partner übernommen haben (Regel „Zahl“), oder mindestens der Anteil θ seiner Partner, mindestens aber einer (Regel „Anteil“). Ein Betrieb ohne Partner übernimmt nie.
2. **Startgruppe:** ein zufälliger Betrieb und bis zu *g* − 1 seiner Partner haben von Anfang an übernommen (Runde 0). Ein einzelner Starter reicht für *r* ≥ 2 nicht: niemand hätte zwei übernommene Partner.
3. **Runden:** in jeder Runde prüfen alle Betriebe gleichzeitig, ob sie jetzt genug übernommene Partner haben. Wer übernommen hat, bleibt dabei (es gibt keinen Rückschritt).
4. **Fixpunkt:** die Ausbreitung endet, wenn in einer Runde niemand dazukommt. Weil nie jemand aussteigt, ist das Ergebnis **unabhängig von der Reihenfolge**: es ist die kleinste Menge, die die Startgruppe enthält und von außen nicht mehr überzeugt wird.
5. **Der Regler „Runde“** blättert durch die Ausbreitung: grün früher, orange in dieser Runde übernommen, gelb umrandet sind Betriebe, denen genau **ein** übernommener Partner fehlt.
        """
    )
    st.markdown(
        """
| Begriff | Bedeutung hier |
|---|---|
| **Einfache Ansteckung** | Schwelle *r* = 1: ein übernommener Partner genügt. Das ist reine Erreichbarkeit im Netz. |
| **Komplexe Ansteckung** | Schwelle *r* ≥ 2 oder ein Anteil θ der Partner: mehrere Quellen sind nötig. |
| **Dreiecke** | Zwei Partner eines Betriebs, die auch miteinander Partner sind. Gemeinsame Partner erleichtern die Schwelle 2; Dreiecke sind dafür nicht notwendig. |
| **Kipppunkt** | Der Anteil Abkürzungen im Ring, ab dem die Schwelle 2 das Netz in höchstens der Hälfte der Läufe füllt (Experiment 2). |
| **Brückenbreite** | Zahl der Partner, über die ein Betrieb auf der anderen Seite einer Brücke erreicht wird (Experiment 5). |
| **Kaskadenfenster** | Bereich des mittleren Grads, in dem ein einzelner Startknoten bei Anteilsregel eine große Kaskade auslösen kann (Experiment 3, nach Watts). |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Netz zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    typ = st.selectbox("Netztyp", C.ALL_TYPES, key="netztyp_select", help="Welches Netz erzeugt wird. Das Zwei-Gruppen-Netz hat eine einstellbare Brücke.")
    n = st.slider("Betriebe n", *bounds("n_slider"), key="n_slider", help="Zahl der Knoten (beim Gitter auf ein Quadrat gerundet, bei zwei Gruppen auf eine gerade Zahl).")
    c = st.slider("Partner je Betrieb c", *bounds("c_slider"), key="c_slider", help="Was c bedeutet, hängt vom Netztyp ab (siehe darunter).")
    st.caption(C.C_MEANING[typ])
    beta = st.slider("Abkürzungen β (%)", *bounds("beta_slider"), key="beta_slider", help="Nur beim Ring: Anteil der Gitterkanten, die auf ein zufälliges Ziel umgelegt werden.")
    inside = st.slider("Anteil der Kanten innen (%)", *bounds("inside_slider"), key="inside_slider", help="Nur bei Verbünden: Anteil der Kanten innerhalb der sechs Verbünde.")
    width = st.slider("Brückenbreite w", *bounds("width_slider"), key="width_slider", help="Nur bei zwei Gruppen: Zahl der Tor-Knoten je Seite; die Brücke hat w · w Kanten.")
    mode = st.selectbox("Brückenart", C.BRIDGE_MODES, key="mode_select", help="Nur bei zwei Gruppen: „breit“ verbindet w Tor-Knoten vollständig mit w Tor-Knoten, „verteilt“ setzt gleich viele Kanten mit verschiedenen Enden.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt das Netz und die Startgruppe.")
    st.button("🎲 Neu würfeln", width="stretch", on_click=randomize_seed)
    st.markdown("**Schwelle und Start**")
    rule = st.selectbox("Schwellenregel", C.RULES, key="rule_select", help="Zahl r: so viele Partner müssen übernommen haben. Anteil θ: dieser Anteil der Partner (mindestens einer).")
    r = st.slider("Zahl r der Partner", *bounds("r_slider"), key="r_slider", help="Wirkt bei der Regel „Zahl“. r = 1 ist die einfache Ansteckung.")
    theta = st.slider("Anteil θ der Partner (%)", *bounds("theta_slider"), key="theta_slider", help="Wirkt bei der Regel „Anteil“. Ein Betrieb mit d Partnern braucht aufgerundet θ · d, mindestens einen.")
    g = st.slider("Startgruppe g", *bounds("g_slider"), key="g_slider", help="Ein Betrieb und bis zu g − 1 seiner Partner übernehmen in Runde 0.")

sync_query_params({"netztyp_select": typ, "n_slider": int(n), "c_slider": int(c), "seed_input": int(seed), "beta_slider": int(beta), "inside_slider": int(inside), "width_slider": int(width),
                   "mode_select": mode, "rule_select": rule, "r_slider": int(r), "theta_slider": int(theta), "g_slider": int(g)})

settings = Settings(typ, int(n), int(c), int(seed), int(beta), int(inside), int(width), mode, rule, int(r), int(theta), int(g))
with st.spinner("Rechne die Ausbreitung …"):
    an = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die Ausbreitung Runde für Runde")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Betriebe / Partnerschaften", f"{an.inst.n} / {an.inst.m}")
m2.metric("Startgruppe", f"{len(an.seeds)} Betriebe")
m3.metric("Übernommen am Ende", f"{an.spread.count} von {an.inst.n}", delta=f"{de(100 * an.spread.share, 0)} %", delta_color="off")
m4.metric("Runden", f"{an.spread.rounds}", delta=f"einfache Ansteckung: {an.reference.rounds}", delta_color="off")
if an.inst.m > 0:
    t = st.slider("Runde", 0, max(an.spread.rounds, 1), an.spread.rounds, help="Zustand nach dieser Runde; 0 ist die Startgruppe.")
    t = min(t, an.spread.rounds)
    state = adopted_by(an.spread, t)
    short = one_short(an.inst.adj, state, **rule_kwargs(rule, int(r), int(theta)))
    st.plotly_chart(build_network(an.inst, an.spread, t, an.seeds, short), width="stretch", key="net_chart")
    st.caption(f"Nach Runde {t} haben {sum(state)} von {an.inst.n} Betrieben übernommen; {len(short)} sind knapp davor (gelb umrandet). "
               + ("Verbünde bzw. Gruppen haben je eine Markierungsform. " if an.inst.groups is not None else "")
               + "Rot umrandet: die Startgruppe.")
    st.markdown("**Anteil der Übernehmer über die Runden** (dieselbe Startgruppe, Schwellen im Vergleich; die gewählte Regel dick)")
    st.plotly_chart(build_curves(an.compare, an.selected), width="stretch", key="curve_chart")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wann reicht ein Kontakt, wann braucht es mehrere?")
kind, text = verdict_main(an)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

n_exp, c_exp, g_exp = settings.n, settings.c, settings.g
runs_per_cell = len(C.LIVE_SEEDS) * C.STARTS_PER_NET
st.subheader("🔬 Experiment 1: Welche Netze tragen welche Schwelle?")
st.caption(f"Je Netztyp und Schwelle *r* = 1, 2, 3: {runs_per_cell} Läufe ({len(C.LIVE_SEEDS)} feste Netze mit je {C.STARTS_PER_NET} Startgruppen), n = {n_exp}, c = {c_exp}, Startgruppe g = {g_exp}. "
           f"Ein Lauf füllt das Netz ab {de(100 * C.FULL_SHARE, 0)} % übernommener Betriebe.")


def show_types(rows):
    st.markdown("**Endanteil (Median)**")
    st.plotly_chart(build_type_share(rows), width="stretch", key="type_share_chart")
    st.markdown("**Anteil der Läufe, die das Netz füllen**")
    st.plotly_chart(build_type_full(rows), width="stretch", key="type_full_chart")
    kind_, text_ = verdict_types(rows)
    getattr(st, kind_)(text_)


experiment("types", "Netztypen vergleichen", (n_exp, c_exp, g_exp), lambda: _types(n_exp, c_exp, g_exp), show_types, "Rechnet sieben Netze mit je vier Zufallsnetzen und drei Schwellen, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 2: Wie viele Abkürzungen verträgt die Schwelle 2?")
st.caption(f"Ring mit c = {c_exp} Nachbarn und Anteil β umverdrahteter Kanten ({', '.join(de(100 * b, 0) for b in C.SHORTCUT_BETAS)} %), n = {n_exp}, Startgruppe g = {g_exp}; {runs_per_cell} Läufe je Punkt.")


def show_shortcuts(rows):
    st.markdown("**Anteil der Läufe, die das Netz füllen**")
    st.plotly_chart(build_shortcuts(rows), width="stretch", key="shortcut_chart")
    st.markdown("**Runden der vollständigen Läufe** (logarithmische Achse; fehlende Punkte: kein Lauf füllt das Netz)")
    st.plotly_chart(build_shortcut_rounds(rows), width="stretch", key="shortcut_rounds_chart")
    kind_, text_ = verdict_shortcuts(rows)
    getattr(st, kind_)(text_)


experiment("shortcuts", "Abkürzungen messen", (n_exp, c_exp, g_exp), lambda: _shortcuts(n_exp, c_exp, g_exp), show_shortcuts, "Rechnet acht Werte für β mit je vier Netzen und drei Schwellen, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 3: Das Kaskadenfenster")
st.caption(f"Zufallsnetz mit n = {C.WATTS_N} Betrieben, Anteilsregel θ = {de(100 * C.WATTS_THETA, 0)} %, **ein einzelner** Startbetrieb; mittlerer Grad z von {de(C.WATTS_ZS[0], 1)} bis {de(C.WATTS_ZS[-1], 1)}; "
           f"{len(C.LIVE_SEEDS) * C.WATTS_STARTS} Läufe je Punkt. Hinterlegt: das Fenster der Formel (Betriebe mit höchstens ⌊1/θ⌋ Partnern bilden eine zusammenhängende Gruppe).")


def show_watts(rows):
    st.plotly_chart(build_watts(rows), width="stretch", key="watts_chart")
    kind_, text_ = verdict_watts(rows)
    getattr(st, kind_)(text_)


experiment("watts", "Fenster messen", "fest", _watts, show_watts, "Rechnet zwölf Werte von z mit je vier Netzen aus 1 000 Betrieben, einige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 4: Halten Gemeinschaften die Schwelle auf?")
st.caption(f"Sechs gleich große Verbünde, n = {n_exp}, Startgruppe g = {g_exp}, {rule_text(rule, int(r), int(theta))} aus der Seitenleiste; "
           f"Anteil der Kanten innen {', '.join(de(100 * x, 0) for x in C.COMMUNITY_INSIDES)} %, mittlerer Grad {' und '.join(str(x) for x in C.COMMUNITY_DEGREES)}; {runs_per_cell} Läufe je Punkt.")


def show_communities(rows):
    st.plotly_chart(build_communities(rows), width="stretch", key="community_chart")
    kind_, text_ = verdict_communities(rows, rule, int(r), int(theta))
    getattr(st, kind_)(text_)


experiment("communities", "Gemeinschaften messen", (n_exp, g_exp, rule, int(r), int(theta)), lambda: _communities(n_exp, g_exp, rule, int(r), int(theta)), show_communities,
           "Rechnet zwölf Netzkonfigurationen mit je vier Netzen, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 5: Breite der Brücke")
st.caption(f"Zwei Gruppen mit n = {n_exp - n_exp % 2} Betrieben, c = {c_exp} Partnern innerhalb jeder Gruppe, Start in der ersten Gruppe (g = {g_exp}); Brücke der Breite *w* = {C.BRIDGE_WIDTHS[0]} bis {C.BRIDGE_WIDTHS[-1]}, "
           "„breit“: *w* Tor-Knoten je Seite vollständig verbunden, „verteilt“: dieselben *w* · *w* Kanten mit verschiedenen Enden. Gezählt: Läufe, in denen mindestens die Hälfte der anderen Gruppe übernimmt.")


def show_bridge(rows):
    st.plotly_chart(build_bridge(rows), width="stretch", key="bridge_chart")
    kind_, text_ = verdict_bridge(rows)
    getattr(st, kind_)(text_)


experiment("bridge", "Brücken messen", (n_exp, c_exp, g_exp), lambda: _bridge(n_exp, c_exp, g_exp), show_bridge, "Rechnet zehn Brückenvarianten mit je vier Netzen und drei Schwellen, wenige Sekunden.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Deterministische Schwellen** | Die Dynamik hat keinen Zufall: ein Betrieb mit genug übernommenen Partnern übernimmt sicher, sonst nie. Zufall steckt nur im Netz und in der Startgruppe. Mit einer Übernahmewahrscheinlichkeit je Kontakt (wie in Experimenten mit Menschen) verschwimmt der Kipppunkt. | – |
| **Gleiche Schwelle für alle** | Alle Betriebe haben dieselbe Schwelle *r* bzw. θ. In der Wirklichkeit streuen Schwellen, und die Verteilung der Schwellen entscheidet über den Verlauf (Granovetter 1978); bei Watts (2002) sind es Anteile mit Heterogenität. | – |
| **Startgruppe statt Einzelstarter** | Mit einem einzelnen Starter passiert bei *r* ≥ 2 nichts, weil niemand zwei übernommene Partner hat. Der Befund hängt an der Größe und am Zusammenhalt der Startgruppe (Regler *g*). | – |
| **Kein Rückschritt** | Wer übernommen hat, bleibt dabei. Aussteigen, Vergessen und Rückfälle fehlen. | Stück 10 (Voter-Modell) |
| **Statisches Netz** | Die Partnerschaften ändern sich während der Ausbreitung nicht. | Stück 13 (zeitliche Netze) |
| **Keine Gegenmaßnahme** | Niemand bremst die Ausbreitung gezielt, etwa durch Impfen oder Sperren von Knoten. | Stück 7 (Eindämmung) |
| **Modellbefund** | Die Demo zeigt Verhalten im Modell, nicht die Wirkung in der Wirklichkeit; die Lücke zwischen Modellen und empirischen Tests ist groß (Flache u. a. 2017). | – |
| **Synthetische Netze, Ränder, Größe** | Die Zahlen gelten für diese Netztypen bei n bis 250 und für Mediane über feste Netze. Das Gitter hat Randknoten mit weniger Partnern; das Zwei-Gruppen-Netz ist ein Handbeispiel, kein Messwert eines echten Netzes. | – |
| **Kaskadenfenster: eigene Rechnung** | Die Bedingung Σ k(k − 1) pₖ > z über die Knoten mit höchstens ⌊1/θ⌋ Partnern ist die hier hergeleitete Form für ein Poisson-Netz. Ob sie die Zahlen der Originalarbeit von Watts (2002) trifft, ist nicht geprüft. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Übernahmeregel.** $A_t$ sei die Menge der Betriebe, die bis Runde $t$ übernommen haben, $A_0$ die Startgruppe, $N(v)$ die Partner von $v$ und $d_v = |N(v)|$. Ein Betrieb $v \notin A_t$ übernimmt in Runde $t+1$, wenn

$$|N(v) \cap A_t| \ge s_v$$

gilt. Die nötige Zahl $s_v$ ist bei der Regel „Zahl“ gleich $r$, bei der Regel „Anteil“

$$s_v = \max\bigl(1, \lceil \theta\, d_v \rceil\bigr)$$

(für $d_v = 0$ nie). Mit $r = 1$ ist das die Erreichbarkeit von $A_0$.

**Monotonie und Fixpunkt.** Aus $A_t \subseteq A_{t+1}$ folgt, dass die Folge nach höchstens $n$ Runden stehen bleibt. Der Endzustand $A_\infty$ ist die kleinste Menge $S \supseteq A_0$ mit $|N(v) \cap S| < s_v$ für alle $v \notin S$, hängt also nicht von der Reihenfolge ab. Er wächst mit $A_0$ und fällt mit $r$ bzw. $\theta$.

**Verwundbare Betriebe.** Ein Betrieb mit $d$ Partnern lässt sich durch einen einzigen übernommenen Partner überzeugen, wenn $\lceil \theta d \rceil = 1$ ist, also für

$$d \le K^* = \lfloor 1/\theta \rfloor$$

**Kaskadenfenster.** Im Poisson-Netz mit mittlerem Grad $z$ (Gradverteilung $p_k = e^{-z} z^k / k!$) bilden die verwundbaren Betriebe eine zusammenhängende Gruppe, wenn im Mittel mehr als ein verwundbarer Partner nachfolgt:

$$\sum_{k=2}^{K^*} k\,(k-1)\,p_k > z$$

Das ist die Bedingung für eine unendliche Gruppe in einem Zufallsnetz mit gegebener Gradfolge (Molloy–Reed), angewandt auf den Teil der Betriebe mit Grad höchstens $K^*$. Sie liefert für $\theta = 0{,}18$ ein Fenster $z_\mathrm{unten} < z < z_\mathrm{oben}$ (Experiment 3).

**Literatur.**
- Centola, D., Macy, M. (2007): *Complex Contagions and the Weakness of Long Ties.* American Journal of Sociology 113(3), 702–734.
- Watts, D. J. (2002): *A simple model of global cascades on random networks.* PNAS 99(9), 5766–5771.
- Granovetter, M. (1978): *Threshold Models of Collective Behavior.* American Journal of Sociology 83(6), 1420–1443.
- Flache, A. u. a. (2017): *Models of Social Influence: Towards the Next Frontiers.* JASSS 20(4), 2.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
