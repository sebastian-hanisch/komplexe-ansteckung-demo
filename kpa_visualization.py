"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kpa_algorithm as A
import kpa_constants as C
from kpa_evaluation import de

SYMBOLS = ("circle", "square", "diamond", "triangle-up", "triangle-down", "pentagon")
COLOR_GREY = "#b8b8b8"
COLOR_SHORT = "#e3b505"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340, bottom=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=bottom), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _pct_axis(fig, title):
    fig.update_yaxes(title_text=title, range=[0, 108], ticksuffix=" %")
    return fig


def build_network(inst, spread, t, seeds, short, height=460):
    """Netz mit festen Positionen im Zustand nach Runde t: grau = nicht übernommen, grün = früher übernommen, orange = in Runde t neu, rot umrandet = Startgruppe, gelb umrandet = knapp davor
    (es fehlt genau ein übernommener Partner). Netze mit Gruppen: je Gruppe eine Markierungsform."""
    n = inst.n
    size = 5 if n > 200 else 8
    u, v = A.edge_arrays(inst.adj)
    xs, ys = [], []
    for a, b in zip(u.tolist(), v.tolist()):
        if a < b:
            xs += [inst.pos[a][0], inst.pos[b][0], None]
            ys += [inst.pos[a][1], inst.pos[b][1], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_EDGE, width=0.7), hoverinfo="skip", showlegend=False))
    rnd = spread.round_of
    kinds = {"früher übernommen": [i for i in range(n) if 0 <= rnd[i] < t or (rnd[i] == 0 and t == 0)],
             f"in Runde {t} übernommen": [i for i in range(n) if rnd[i] == t and t > 0],
             "nicht übernommen": [i for i in range(n) if rnd[i] < 0 or rnd[i] > t]}
    colors = {"früher übernommen": C.COLOR_A, f"in Runde {t} übernommen": C.COLOR_B, "nicht übernommen": COLOR_GREY}
    for name, idx in kinds.items():
        if not idx:
            continue
        symbols = [SYMBOLS[inst.groups[i] % len(SYMBOLS)] for i in idx] if inst.groups is not None else "circle"
        fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in idx], y=[inst.pos[i][1] for i in idx], mode="markers", name=name,
                                 marker=dict(size=size, color=colors[name], symbol=symbols, line=dict(color="rgba(40,40,40,0.45)", width=0.4)),
                                 hovertext=[f"Knoten {i}: {len(inst.adj[i])} Partner" + (f", übernommen in Runde {rnd[i]}" if rnd[i] >= 0 else ", nicht übernommen") for i in idx], hoverinfo="text"))
    if short:
        fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in short], y=[inst.pos[i][1] for i in short], mode="markers", name="knapp davor",
                                 marker=dict(size=size + 6, color="rgba(0,0,0,0)", line=dict(color=COLOR_SHORT, width=2)),
                                 hovertext=[f"Knoten {i}: ein Partner fehlt" for i in short], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in seeds], y=[inst.pos[i][1] for i in seeds], mode="markers", name="Startgruppe",
                             marker=dict(size=size + 9, color="rgba(0,0,0,0)", line=dict(color=C.COLOR_SEED, width=2.5)),
                             hovertext=[f"Startgruppe: Knoten {i}" for i in seeds], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[-0.04, 1.04], y=[-0.04, 1.04], mode="markers", marker=dict(size=1, color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, autorange=True)
    fig.update_yaxes(visible=False, autorange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.02), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_curves(compare, selected):
    """Anteil der Übernehmer über die Runden für die Schwellen im Vergleich (dieselbe Startgruppe); die gewählte Regel dick."""
    fig = go.Figure()
    longest = max((sp.rounds for sp in compare.values()), default=0)
    for label, sp in compare.items():
        cur = A.curve(sp)
        ys = [100.0 * c / sp.n for c in cur] + [100.0 * cur[-1] / sp.n] * (longest - sp.rounds)
        color = C.R_COLORS.get(int(label.split("= ")[1]), C.COLOR_C) if label.startswith("r = ") else C.COLOR_C
        fig.add_trace(go.Scatter(x=list(range(longest + 1)), y=ys, mode="lines", name=label, line=dict(color=color, width=4 if label == selected else 1.8, shape="hv")))
    fig.update_xaxes(title_text="Runde")
    _pct_axis(fig, "Übernehmer")
    return _base(fig, height=300, bottom=40)


def _bars(rows, key, title, fmt, rng=None):
    fig = go.Figure()
    thresholds = sorted(rows[0]["cells"]) if rows else []
    for r in thresholds:
        ys = [100.0 * row["cells"][r][key] for row in rows]
        fig.add_trace(go.Bar(x=[row["label"] for row in rows], y=ys, name=f"r = {r}", marker_color=C.R_COLORS.get(r, C.COLOR_C), text=[de(y, 0) for y in ys], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=title, range=[0, 118], ticksuffix=" %")
    fig.update_xaxes(tickangle=-25)
    return _base(fig, height=380, bottom=110)


def build_type_share(rows):
    """Endanteil (Median) je Netztyp und Schwelle."""
    return _bars(rows, "share", "Endanteil (Median)", de)


def build_type_full(rows):
    """Anteil der Läufe, die das Netz füllen (mindestens 90 %), je Netztyp und Schwelle."""
    return _bars(rows, "full", "Läufe, die das Netz füllen", de)


def build_shortcuts(rows):
    """Rundenzahl der vollständigen Läufe über den Anteil Abkürzungen (links) und Anteil der vollständigen Läufe (rechts), je Schwelle."""
    xs = [f"{de(100 * row['beta'], 0)} %" for row in rows]
    fig = go.Figure()
    for r in sorted(rows[0]["cells"]):
        fig.add_trace(go.Scatter(x=xs, y=[100.0 * row["cells"][r]["full"] for row in rows], mode="lines+markers", name=f"r = {r}", line=dict(color=C.R_COLORS.get(r, C.COLOR_C), width=3)))
    fig.update_xaxes(title_text="Anteil Abkürzungen β")
    return _pct_axis(_base(fig, height=320, bottom=40), "Läufe, die das Netz füllen")


def build_shortcut_rounds(rows):
    """Rundenzahl der vollständigen Läufe über β, je Schwelle (Lücken, wo kein Lauf das Netz füllt)."""
    xs = [f"{de(100 * row['beta'], 0)} %" for row in rows]
    fig = go.Figure()
    for r in sorted(rows[0]["cells"]):
        fig.add_trace(go.Scatter(x=xs, y=[row["cells"][r]["rounds"] for row in rows], mode="lines+markers", name=f"r = {r}", line=dict(color=C.R_COLORS.get(r, C.COLOR_C), width=3), connectgaps=False))
    fig.update_xaxes(title_text="Anteil Abkürzungen β")
    fig.update_yaxes(title_text="Runden bis zum Ende", type="log", tickvals=[2, 5, 10, 20, 50, 100, 200], ticktext=["2", "5", "10", "20", "50", "100", "200"])
    return _base(fig, height=320, bottom=40)


def build_watts(rows, theta=C.WATTS_THETA):
    """Anteil der Einzelstarter mit Kaskade über dem mittleren Grad z; das Fenster der Formel ist hinterlegt."""
    fig = go.Figure()
    window = A.vulnerable_window(theta)
    if window is not None:
        fig.add_vrect(x0=window[0], x1=window[1], fillcolor="rgba(47,107,101,0.15)", line_width=0, annotation_text="Fenster der Formel", annotation_position="top left")
    fig.add_trace(go.Scatter(x=[r["z"] for r in rows], y=[100.0 * r["frac"] for r in rows], mode="lines+markers", name="gemessen", line=dict(color=C.COLOR_B, width=3),
                             hovertemplate="z = %{x}: %{y:.0f} %<extra></extra>"))
    fig.update_xaxes(title_text="mittlerer Grad z")
    return _pct_axis(_base(fig, height=320, bottom=40), "Starter mit Kaskade über 5 %")


def build_communities(rows):
    """Endanteil im Verbund des Startknotens (gestrichelt) und außerhalb (durchgezogen) über den Anteil der Kanten innen, je mittlerem Grad."""
    fig = go.Figure()
    for i, c in enumerate(sorted({row["c"] for row in rows})):
        mine = [row for row in rows if row["c"] == c]
        color = (C.COLOR_A, C.COLOR_B, C.COLOR_C)[i % 3]
        xs = [100.0 * row["inside"] for row in mine]
        fig.add_trace(go.Scatter(x=xs, y=[100.0 * row["other"] for row in mine], mode="lines+markers", name=f"außerhalb, Grad {c}", line=dict(color=color, width=3)))
        fig.add_trace(go.Scatter(x=xs, y=[100.0 * row["own"] for row in mine], mode="lines", name=f"eigener Verbund, Grad {c}", line=dict(color=color, width=1.5, dash="dash")))
    fig.update_xaxes(title_text="Anteil der Kanten innerhalb der Verbünde (%)")
    return _pct_axis(_base(fig, height=340, bottom=50), "Endanteil")


def build_bridge(rows):
    """Anteil der Läufe, in denen mindestens die Hälfte der anderen Gruppe erreicht wird, je Brückenbreite und Schwelle, für beide Brückenarten."""
    xs = [f"{'breit' if row['mode'] == C.BRIDGE_WIDE else 'verteilt'}, Breite {row['w']}" for row in rows]
    fig = go.Figure()
    for r in sorted(rows[0]["cells"]):
        ys = [100.0 * row["cells"][r]["cross"] for row in rows]
        fig.add_trace(go.Bar(x=xs, y=ys, name=f"r = {r}", marker_color=C.R_COLORS.get(r, C.COLOR_C), text=[de(y, 0) for y in ys], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Läufe, die hinüberkommen", range=[0, 118], ticksuffix=" %")
    fig.update_xaxes(tickangle=-35)
    return _base(fig, height=400, bottom=120)
