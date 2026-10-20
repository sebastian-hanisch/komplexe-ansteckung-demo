"""Kern der Demo (nur numpy/Standardbibliothek): Ausbreitung mit Schwelle (deterministisch), Startgruppe, Zustand nach Runde t und das Kaskadenfenster nach Watts.

Regel: ein Knoten übernimmt, sobald mindestens `need` seiner Nachbarn übernommen haben; `need` ist für alle Knoten r (Zahl) oder je Knoten max(1, ⌈θ · Grad⌉) (Anteil; Grad 0 nie).
Synchrone Runden bis zum Fixpunkt. Die Regel ist monoton (ein Übernehmer verlässt nie wieder), der Fixpunkt ist daher unabhängig von der Reihenfolge der Knoten:
er ist die kleinste Knotenmenge, die die Startgruppe enthält und von außen nicht mehr überzeugt wird (`closure_bruteforce` rechnet genau das nach).
Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b)."""

import itertools
import math
from dataclasses import dataclass

import numpy as np

EPS = 1e-9


@dataclass(frozen=True)
class Spread:
    round_of: tuple     # Runde der Übernahme je Knoten: 0 = Startgruppe, -1 = nie
    rounds: int         # Zahl der Runden, in denen jemand neu übernommen hat

    @property
    def n(self) -> int:
        return len(self.round_of)

    @property
    def count(self) -> int:
        return sum(1 for t in self.round_of if t >= 0)

    @property
    def share(self) -> float:
        return self.count / self.n if self.n else 0.0


def edge_arrays(adj):
    """Gerichtete Kantenlisten (Quelle, Ziel), jede Kante in beiden Richtungen."""
    pairs = [(a, b) for a in range(len(adj)) for b in adj[a]]
    if not pairs:
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    src, dst = zip(*pairs)
    return np.array(src, dtype=int), np.array(dst, dtype=int)


def degrees(adj):
    return np.array([len(a) for a in adj], dtype=int)


def need_vector(adj, r=None, theta=None):
    """Nötige Zahl übernommener Nachbarn je Knoten. Genau einer der Parameter ist gesetzt: r (Zahl, für alle gleich) oder theta (Anteil des Grads, mindestens 1; Grad 0: nie, unendlich)."""
    if (r is None) == (theta is None):
        raise ValueError("genau einer von r und theta muss gesetzt sein")
    n = len(adj)
    if r is not None:
        if r < 1:
            raise ValueError("r muss mindestens 1 sein")
        return np.full(n, float(r))
    if not 0 < theta <= 1:
        raise ValueError("theta muss in (0, 1] liegen")
    deg = degrees(adj)
    return np.where(deg > 0, np.maximum(1.0, np.ceil(theta * deg - EPS)), np.inf)


def threshold_spread(adj, seeds, r=None, theta=None) -> Spread:
    """Synchrone Runden: in jeder Runde übernehmen alle, die jetzt genug übernommene Nachbarn haben. Bis niemand mehr dazukommt."""
    n = len(adj)
    seeds = sorted(set(int(s) for s in seeds))
    if any(not 0 <= s < n for s in seeds):
        raise ValueError("Startknoten außerhalb des Netzes")
    need = need_vector(adj, r, theta)
    src, dst = edge_arrays(adj)
    round_of = np.full(n, -1, dtype=int)
    round_of[seeds] = 0
    rounds = 0
    while True:
        adopted = round_of >= 0
        cnt = np.bincount(dst, weights=adopted[src].astype(float), minlength=n)
        new = (cnt >= need) & ~adopted
        if not new.any():
            break
        rounds += 1
        round_of[new] = rounds
    return Spread(tuple(int(t) for t in round_of), rounds)


def adopted_by(spread: Spread, t: int) -> tuple:
    """Wahrheitswert je Knoten: bis einschließlich Runde t übernommen."""
    return tuple(0 <= x <= t for x in spread.round_of)


def curve(spread: Spread):
    """Zahl der Übernehmer nach Runde 0, 1, …, rounds."""
    return [sum(1 for x in spread.round_of if 0 <= x <= t) for t in range(spread.rounds + 1)]


def closure_bruteforce(adj, seeds, r=None, theta=None) -> frozenset:
    """Unabhängiges Orakel für kleine Netze (n ≤ 16): die kleinste Menge S mit Startgruppe ⊆ S, von der kein Außenstehender überzeugt wird (weniger als `need` Nachbarn in S).
    Der Durchschnitt aller solchen Mengen ist wieder eine solche Menge, also ist das Ergebnis genau der Fixpunkt der Regel. Rechnet nur mit Mengen, ohne Runden."""
    n = len(adj)
    if n > 16:
        raise ValueError("closure_bruteforce ist nur für n ≤ 16 gedacht")
    need = need_vector(adj, r, theta)
    seeds = frozenset(int(s) for s in seeds)
    best = frozenset(range(n))
    others = [v for v in range(n) if v not in seeds]
    for size in range(len(others) + 1):
        for extra in itertools.combinations(others, size):
            s = seeds | frozenset(extra)
            if len(s) >= len(best):
                continue
            if all(sum(1 for w in adj[v] if w in s) < need[v] for v in range(n) if v not in s):
                best = s
    return best


def group_seed(adj, g, seed, within=None) -> tuple:
    """Startgruppe: ein Knoten mit mindestens einem Partner und bis zu g − 1 seiner Partner, aus dem Zufalls-Seed. Bei g = 1 nur der Knoten.
    `within` (Knotenmenge) beschränkt Startknoten und Partner darauf (etwa auf eine der zwei Gruppen); ohne Kandidaten gibt es einen Fehler."""
    if g < 1:
        raise ValueError("die Startgruppe braucht mindestens einen Knoten")
    allowed = None if within is None else set(int(x) for x in within)
    cand = [i for i, a in enumerate(adj) if (allowed is None or i in allowed) and any(allowed is None or w in allowed for w in a)]
    if not cand:
        raise ValueError("das Netz hat keine Kante" if allowed is None else "kein Knoten der Gruppe hat einen Partner in der Gruppe")
    rng = np.random.default_rng(int(seed))
    s = int(rng.choice(cand))
    nb = [w for w in adj[s] if allowed is None or w in allowed]
    rng.shuffle(nb)
    return tuple(sorted([s] + [int(x) for x in nb[: g - 1]]))


def count_adopted_neighbours(adj, adopted):
    """Je Knoten die Zahl seiner übernommenen Nachbarn."""
    ad = np.array(adopted, dtype=bool)
    src, dst = edge_arrays(adj)
    return np.bincount(dst, weights=ad[src].astype(float), minlength=len(adj)).astype(int)


def one_short(adj, adopted, r=None, theta=None) -> tuple:
    """Knoten, die nicht übernommen haben, schon mindestens einen übernommenen Nachbarn haben und denen genau einer zur Schwelle fehlt ("kurz davor"; Grad 0 ausgenommen)."""
    need = need_vector(adj, r, theta)
    cnt = count_adopted_neighbours(adj, adopted)
    ad = np.array(adopted, dtype=bool)
    return tuple(int(v) for v in range(len(adj)) if not ad[v] and np.isfinite(need[v]) and cnt[v] >= 1 and cnt[v] == need[v] - 1)


# --- Kaskadenfenster nach Watts (eigene Herleitung, siehe README) --------------------------------------------------------------------------------------


def vulnerable_max_degree(theta) -> int:
    """Größter Grad K*, bei dem ein einziger übernommener Nachbar reicht: ⌈θ · K⌉ = 1, also K* = ⌊1 / θ⌋."""
    if not 0 < theta <= 1:
        raise ValueError("theta muss in (0, 1] liegen")
    return int(math.floor(1.0 / theta + EPS))


def poisson_pmf(k, z):
    return math.exp(-z) * z**k / math.factorial(k) if z > 0 else (1.0 if k == 0 else 0.0)


def cascade_margin(z, theta) -> float:
    """Σ_{k=2..K*} k (k − 1) p_k − z für ein Poisson-Netz mit mittlerem Grad z: positiv heißt, dass sich die verwundbaren Knoten (Grad ≤ K*) im Mittel weiter anstecken (Verzweigungszahl über 1)."""
    big_k = vulnerable_max_degree(theta)
    return sum(k * (k - 1) * poisson_pmf(k, z) for k in range(2, big_k + 1)) - z


def vulnerable_window(theta, z_max=40.0, step=0.01):
    """Bereich (z_unten, z_oben) des mittleren Grads, in dem cascade_margin positiv ist, per Abtasten und Bisektion; None, wenn es keinen gibt (z. B. θ > 1/2)."""
    zs = np.arange(step, z_max, step)
    vals = np.array([cascade_margin(float(z), theta) for z in zs])
    pos = np.flatnonzero(vals > 0)
    if pos.size == 0:
        return None

    def bisect(a, b):
        fa = cascade_margin(a, theta) > 0
        for _ in range(60):
            mid = 0.5 * (a + b)
            if (cascade_margin(mid, theta) > 0) == fa:
                a = mid
            else:
                b = mid
        return 0.5 * (a + b)

    i0, i1 = int(pos[0]), int(pos[-1])
    lo = bisect(float(zs[i0 - 1]) if i0 > 0 else step / 10, float(zs[i0]))
    hi = bisect(float(zs[i1]), float(zs[i1 + 1]) if i1 + 1 < len(zs) else z_max)
    return (lo, hi)
