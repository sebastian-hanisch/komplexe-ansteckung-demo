"""Netze: Generatoren (synthetisch, mit Seed; Zufallsnetz, Gitter, skalenfrei und Potenzgesetz als Kopie aus k-core-demo, Stück 1), Ring mit Umverdrahtung (Watts und Strogatz), Verbünde (Blockmodell) und zwei Gruppen mit einstellbarer Brücke; dazu die Anordnung für die Anzeige."""

import math
import random
from dataclasses import dataclass

import numpy as np

import kpa_constants as C


@dataclass(frozen=True)
class Instance:
    typ: str
    adj: tuple           # Nachbarlisten (sortierte Tupel), Knoten 0 bis n - 1
    pos: tuple           # (x, y) in [0, 1] für die Anzeige
    labels: object = None   # Namen je Knoten (Link-Netz) oder None
    groups: object = None   # Rolle je Knoten (Makler-Beispiel, Hubs, Link-Netz) oder None

    @property
    def n(self) -> int:
        return len(self.adj)

    @property
    def m(self) -> int:
        return sum(len(a) for a in self.adj) // 2


def _rng(seed, salt):
    return random.Random(int(seed) * 1_000_003 + salt)


def _from_edges(n, edges):
    sets = [set() for _ in range(n)]
    for a, b in edges:
        if a != b:
            sets[a].add(b)
            sets[b].add(a)
    return tuple(tuple(sorted(s)) for s in sets)


def _random_pairs(n, m, rng):
    """m verschiedene zufällige Knotenpaare (G(n, m))."""
    m = min(m, n * (n - 1) // 2)
    pairs = set()
    while len(pairs) < m:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            pairs.add((min(a, b), max(a, b)))
    return sorted(pairs)


# --- Generatoren ------------------------------------------------------------------------------------------------------------------------------------


def gen_random(n, c, rng):
    """Zufallsnetz G(n, m) mit m = round(c * n / 2) Kanten (mittlerer Grad c)."""
    return _from_edges(n, _random_pairs(n, round(c * n / 2), rng))


def gen_power(n, c, rng, gamma=2.5):
    """Konfigurationsmodell mit Gradfolge nach Potenzgesetz (Exponent gamma), auf mittleren Grad c skaliert; Schleifen und Doppelkanten fallen weg."""
    xs = [(1 - rng.random()) ** (-1 / (gamma - 1)) for _ in range(n)]
    mean = sum(xs) / n
    deg = [min(n - 1, max(1, round(x * c / mean))) for x in xs]
    if sum(deg) % 2:
        deg[0] += 1 if deg[0] < n - 1 else -1
    stubs = [v for v in range(n) for _ in range(deg[v])]
    rng.shuffle(stubs)
    return _from_edges(n, [(stubs[i], stubs[i + 1]) for i in range(0, len(stubs) - 1, 2)])


def gen_ba(n, c, rng):
    """Bevorzugte Anbindung (Barabási-Albert): Start mit vollständigem Graph auf m + 1 Knoten, jeder neue Knoten bringt m = round(c / 2) Kanten
    zu verschiedenen früheren Knoten, gewählt proportional zum Grad. Damit hat jeder Knoten mindestens m Nachbarn, und die Entfernung in
    umgekehrter Einfügereihenfolge zeigt Degeneracy m: alle Knoten haben die Kernzahl m."""
    m = max(1, round(c / 2))
    m = min(m, n - 1)
    edges = [(i, j) for i in range(m + 1) for j in range(i + 1, m + 1)]
    ends = [v for e in edges for v in e]
    for v in range(m + 1, n):
        targets = set()
        while len(targets) < m:
            targets.add(rng.choice(ends))
        for t in sorted(targets):
            edges.append((t, v))
            ends.extend((t, v))
    return _from_edges(n, edges)


def communities_of(n, blocks=6):
    base = max(1, n // blocks)
    return [min(v // base, blocks - 1) for v in range(n)]


def gen_communities(n, c, rng, blocks=6):
    """Sechs Verbünde: 80 % der Kanten innerhalb eines Verbunds, 20 % dazwischen; insgesamt round(c * n / 2) Kanten."""
    group = communities_of(n, blocks)
    members = [[v for v in range(n) if group[v] == g] for g in range(blocks)]
    m = min(round(c * n / 2), n * (n - 1) // 2)
    m_in = round(0.8 * m)
    capacity_in = sum(len(b) * (len(b) - 1) // 2 for b in members)
    m_in = min(m_in, capacity_in)
    weights = [len(b) * (len(b) - 1) // 2 for b in members]
    edges = set()
    while len(edges) < m_in:
        b = rng.choices(range(blocks), weights=weights)[0]
        if len(members[b]) < 2:
            continue
        x, y = rng.sample(members[b], 2)
        edges.add((min(x, y), max(x, y)))
    between_capacity = n * (n - 1) // 2 - capacity_in
    target = len(edges) + min(m - m_in, between_capacity)     # nie mehr Kanten verlangen, als zwischen den Verbünden möglich sind
    while len(edges) < target:
        x, y = rng.randrange(n), rng.randrange(n)
        if group[x] != group[y]:
            edges.add((min(x, y), max(x, y)))
    return _from_edges(n, sorted(edges))


def gen_ring(n, c, rng, shortcut=0.05):
    """Ring, jeder Knoten mit round(c / 2) Nachbarn auf jeder Seite, dazu je Ringkante mit Wahrscheinlichkeit 5 % eine zufällige Abkürzung."""
    half = max(1, min(round(c / 2), (n - 1) // 2))
    edges = set()
    for i in range(n):
        for d in range(1, half + 1):
            j = (i + d) % n
            edges.add((min(i, j), max(i, j)))
    lattice = sorted(edges)
    for a, b in lattice:
        if rng.random() < shortcut:
            x = rng.randrange(n)
            if x != a and (min(a, x), max(a, x)) not in edges:
                edges.add((min(a, x), max(a, x)))
    return _from_edges(n, sorted(edges))


def grid_side(n):
    return max(2, round(math.sqrt(n)))


def gen_grid(n, c):
    """Quadratisches Gitter mit side * side Knoten; c < 6: vier Nachbarn, 6 bis 7: dazu eine Diagonale, ab 8: beide Diagonalen."""
    s = grid_side(n)
    edges = []
    for r in range(s):
        for q in range(s):
            v = r * s + q
            if q + 1 < s:
                edges.append((v, v + 1))
            if r + 1 < s:
                edges.append((v, v + s))
                if c >= 6 and q + 1 < s:
                    edges.append((v, v + s + 1))
                if c >= 8 and q - 1 >= 0:
                    edges.append((v, v + s - 1))
    return _from_edges(s * s, edges)


def hubs_structure(n):
    """Aufteilung des Netzes „Hubs am Rand“: (Kerngröße, Zahl der Hubs, Zahl der Randknoten, Zahl der Blätter)."""
    core = max(8, n // 10)
    hubs = 5
    ring = n // 3
    leaves = n - core - hubs - ring
    return core, hubs, ring, leaves


def gen_hubs(n, c, rng):
    """Dichter Kern (Kantenwahrscheinlichkeit 0,5), 5 Hubs mit je einer Kante in den Kern und vielen Blättern, dazu Randknoten mit mehreren Kernkontakten.
    Hubs haben hohen Grad, aber Kernzahl 1."""
    core, hubs, ring, leaves = hubs_structure(n)
    edges = [(i, j) for i in range(core) for j in range(i + 1, core) if rng.random() < 0.5]
    hub_ids = list(range(core, core + hubs))
    ring_ids = list(range(core + hubs, core + hubs + ring))
    leaf_ids = list(range(core + hubs + ring, n))
    for h in hub_ids:
        edges.append((rng.randrange(core), h))
    for i, leaf in enumerate(leaf_ids):
        edges.append((hub_ids[i % hubs], leaf))
    contacts = min(core, max(2, round(c / 3)))
    for v in ring_ids:
        for t in sorted(rng.sample(range(core), contacts)):
            edges.append((t, v))
    return _from_edges(n, edges)


def hubs_roles(n):
    core, hubs, ring, leaves = hubs_structure(n)
    return tuple(["Kern"] * core + ["Hub"] * hubs + ["Rand"] * ring + ["Blatt"] * leaves)


# --- Anordnung für die Anzeige -----------------------------------------------------------------------------------------------------------------------


def _normalise(pos):
    lo = pos.min(axis=0)
    span = max(float((pos.max(axis=0) - lo).max()), 1e-9)
    out = (pos - lo) / span
    out = out + (1 - out.max(axis=0)) / 2     # die kürzere Achse mittig
    return out


def layout_force(adj, seed, iterations=80):
    """Fruchterman-Reingold, vektorisiert, mit schwacher Schwerkraft zur Mitte; deterministisch je Seed. Nur für die Anzeige."""
    n = len(adj)
    if n == 1:
        return ((0.5, 0.5),)
    rng = np.random.default_rng(int(seed))
    pos = rng.random((n, 2))
    edges = np.array([(i, j) for i in range(n) for j in adj[i] if i < j], dtype=int).reshape(-1, 2)
    k = math.sqrt(1.0 / n)
    t = 0.1
    for _ in range(iterations):
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.maximum(np.sqrt((delta ** 2).sum(-1)), 1e-6)
        disp = (delta / dist[..., None] * (k * k / dist)[..., None]).sum(axis=1)
        if len(edges):
            d = pos[edges[:, 0]] - pos[edges[:, 1]]
            length = np.maximum(np.sqrt((d ** 2).sum(1)), 1e-6)
            f = (d / length[:, None]) * (length * length / k)[:, None]
            np.add.at(disp, edges[:, 0], -f)
            np.add.at(disp, edges[:, 1], f)
        disp -= 0.6 * (pos - pos.mean(axis=0))
        length = np.maximum(np.sqrt((disp ** 2).sum(1)), 1e-9)
        pos = pos + disp / length[:, None] * np.minimum(length, t)[:, None]
        t = max(0.005, t * 0.96)
    center = np.median(pos, axis=0)
    d = pos - center
    r = np.sqrt((d ** 2).sum(1))
    cap = max(1.6 * float(np.percentile(r, 90)), 1e-9)      # Ausreißer auf einen Kreis zurückholen, damit der dichte Teil lesbar bleibt
    pos = center + d * np.minimum(1.0, cap / np.maximum(r, 1e-12))[:, None]
    out = _normalise(pos)
    return tuple((float(x), float(y)) for x, y in out)


def layout_grid(n_side):
    return tuple(((q + 0.5) / n_side, 1 - (r + 0.5) / n_side) for r in range(n_side) for q in range(n_side))


def layout_ring(n):
    return tuple((0.5 + 0.45 * math.cos(2 * math.pi * i / n), 0.5 + 0.45 * math.sin(2 * math.pi * i / n)) for i in range(n))


# --- Ring mit Umverdrahtung, Blockmodell, zwei Gruppen -----------------------------------------------------------------------------------------------------


def gen_watts_strogatz(n, k, beta, rng):
    """Watts-Strogatz: Ring mit k / 2 Nachbarn auf jeder Seite; jede Gitterkante wird mit Wahrscheinlichkeit beta an ihrem zweiten Ende auf einen zufälligen Knoten umgelegt
    (keine Schleife, keine Doppelkante). beta = 0 ist der regelmäßige Ring, beta = 1 ein Zufallsnetz mit derselben Kantenzahl."""
    half = max(1, min(k // 2, (n - 1) // 2))
    lattice = []
    for i in range(n):
        for d in range(1, half + 1):
            lattice.append((i, (i + d) % n))
    edges = {(min(a, b), max(a, b)) for a, b in lattice}
    for a, b in lattice:
        if rng.random() < beta:
            key = (min(a, b), max(a, b))
            for _ in range(20):                     # ein freies Ziel suchen; sonst bleibt die Kante
                x = rng.randrange(n)
                new = (min(a, x), max(a, x))
                if x != a and new not in edges:
                    edges.discard(key)
                    edges.add(new)
                    break
    return _from_edges(n, sorted(edges))


def sbm_probabilities(n, q, c, inside):
    """Kantenwahrscheinlichkeit innerhalb (p_in) und zwischen (p_out) den Gruppen für mittleren Grad c und den Anteil `inside` der Kanten innerhalb; auf höchstens 1 begrenzt.
    Gruppen gleich groß (Knoten i gehört zu Gruppe i * q // n); gibt es keine Paare innerhalb oder zwischen den Gruppen, ist die jeweilige Wahrscheinlichkeit 0."""
    lab = np.arange(n) * q // n
    same = lab[:, None] == lab[None, :]
    n_in = (same.sum() - n) / 2.0
    n_out = n * (n - 1) / 2.0 - n_in
    m = c * n / 2.0
    p_in = min(1.0, inside * m / n_in) if n_in > 0 else 0.0
    p_out = min(1.0, (1.0 - inside) * m / n_out) if n_out > 0 else 0.0
    return p_in, p_out


def gen_communities_sbm(n, c, inside, seed, blocks=C.BLOCKS):
    """Blockmodell mit `blocks` gleich großen Verbünden, mittlerem Grad c und dem Anteil `inside` der Kanten innerhalb der Verbünde. Rückgabe (Nachbarlisten, Gruppe je Knoten)."""
    lab = np.arange(n) * blocks // n
    p_in, p_out = sbm_probabilities(n, blocks, c, inside)
    prob = np.where(lab[:, None] == lab[None, :], p_in, p_out)
    u = np.random.default_rng(int(seed)).random((n, n))
    upper = np.triu(u < prob, 1)
    pairs = np.argwhere(upper)
    return _from_edges(n, [(int(a), int(b)) for a, b in pairs]), tuple(int(x) for x in lab)


def gen_two_groups(n, c, w, mode, seed):
    """Zwei gleich große Gruppen (n // 2 Knoten, inneres Mittel c), verbunden durch eine Brücke der Breite w: `breit` verbindet w Tor-Knoten der einen Gruppe vollständig mit w Tor-Knoten der anderen
    (w · w Kanten, jeder Tor-Knoten hat w Nachbarn auf der anderen Seite); `verteilt` setzt dieselben w · w Kanten mit paarweise verschiedenen Enden. Rückgabe (Nachbarlisten, Gruppe je Knoten)."""
    rng = np.random.default_rng(int(seed))
    nb = n // 2
    p_in = min(1.0, c / max(1, nb - 1))
    edges = set()
    for block in (0, 1):
        for i in range(nb):
            for j in range(i + 1, nb):
                if rng.random() < p_in:
                    edges.add((block * nb + i, block * nb + j))
    w = max(1, min(int(w), int(math.isqrt(nb))))
    if mode == C.BRIDGE_WIDE:
        ga = rng.choice(nb, size=w, replace=False).tolist()
        gb = (nb + rng.choice(nb, size=w, replace=False)).tolist()
        edges |= {(x, y) for x in ga for y in gb}
    else:
        ea = rng.choice(nb, size=w * w, replace=False).tolist()
        eb = (nb + rng.choice(nb, size=w * w, replace=False)).tolist()
        edges |= set(zip(ea, eb))
    return _from_edges(2 * nb, sorted(edges)), tuple([0] * nb + [1] * nb)


# --- Zusammenbau --------------------------------------------------------------------------------------------------------------------------------------


def make_instance(typ, n, c, seed, beta=0.0, inside=0.8, width=2, mode=C.BRIDGE_WIDE, layout=True) -> Instance:
    """Netz zu Typ, Größe n, Parameter c und Seed. `beta` (Umverdrahtungsanteil) wirkt beim Ring, `inside` (Anteil der Kanten innerhalb der Verbünde) bei den Verbünden, `width` und `mode` bei den zwei Gruppen.
    `layout=False` lässt die teure Kräfte-Anordnung weg (alle Knoten auf (0,5; 0,5)); die Mess-Experimente brauchen nur das Netz."""
    if typ == C.T_RING:
        adj = gen_watts_strogatz(n, c, beta, _rng(seed, 21))
        return Instance(typ, adj, layout_ring(n))
    if typ == C.T_GRID:
        adj = gen_grid(n, c)
        return Instance(typ, adj, layout_grid(grid_side(n)))
    groups = None
    if typ == C.T_COMMUNITIES:
        adj, lab = gen_communities_sbm(n, c, inside, seed)
        groups, salt = lab, 14
    elif typ == C.T_TWO_GROUPS:
        adj, lab = gen_two_groups(n, c, width, mode, seed)
        groups, salt = lab, 18
    else:
        salt = {C.T_RANDOM: 11, C.T_POWER: 12, C.T_BA: 13}.get(typ)
        if salt is None:
            raise ValueError(f"unbekannter Netztyp: {typ}")
        rng = _rng(seed, salt)
        adj = gen_random(n, c, rng) if typ == C.T_RANDOM else gen_power(n, c, rng) if typ == C.T_POWER else gen_ba(n, c, rng)
    pos = layout_force(adj, int(seed) % 1_000_003 + salt) if layout else ((0.5, 0.5),) * len(adj)
    return Instance(typ, adj, pos, groups=groups)
