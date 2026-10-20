"""Gemeinsame Fixtures und Hilfen (DEMO-PLAYBOOK §1b): Mini-Instanzen, an denen jede Einheit von Hand geprüft wird."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_adj(n, pairs):
    """Nachbarlisten (Tupel von sortierten Tupeln) aus einer Kantenliste."""
    sets = [set() for _ in range(n)]
    for a, b in pairs:
        if a != b:
            sets[a].add(b)
            sets[b].add(a)
    return tuple(tuple(sorted(s)) for s in sets)


@pytest.fixture
def path5():
    """Pfad 0 - 1 - 2 - 3 - 4. Mit Schwelle 1 erreicht der Start bei 0 alle (Runde i für Knoten i); mit Schwelle 2 und Startgruppe {0, 1} bleibt es dort stehen (Knoten 2 hat nur einen Nachbarn in der Gruppe)."""
    return make_adj(5, [(0, 1), (1, 2), (2, 3), (3, 4)])


@pytest.fixture
def strip8():
    """Dreiecksstreifen: Knoten i ist mit i + 1 und i + 2 verbunden (n = 8). Startgruppe {0, 1}, Schwelle 2: Knoten i übernimmt in Runde i − 1 (Knoten 2 hat die Nachbarn 0 und 1, Knoten 3 die Nachbarn 1 und 2, …)."""
    return make_adj(8, [(i, j) for i in range(8) for j in (i + 1, i + 2) if j < 8])


@pytest.fixture
def star5():
    """Stern: Mitte 0, Blätter 1 bis 4. Schwelle 2 mit Startgruppe {1, 2}: die Mitte hat zwei übernommene Nachbarn und übernimmt in Runde 1; die Blätter 3 und 4 haben nur einen Nachbarn (die Mitte) und bleiben draußen."""
    return make_adj(5, [(0, 1), (0, 2), (0, 3), (0, 4)])


def bridged_cliques(w):
    """Zwei 4er-Cliquen {0..3} und {4..7}, verbunden durch K_{w,w} zwischen den ersten w Knoten jeder Clique (w ≤ 4)."""
    pairs = [(i, j) for base in (0, 4) for i in range(base, base + 4) for j in range(i + 1, base + 4)]
    pairs += [(a, 4 + b) for a in range(w) for b in range(w)]
    return make_adj(8, pairs)
