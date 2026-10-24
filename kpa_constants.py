"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Netztypen -----------------------------------------------------------------------------------------------------------------------------------
T_RING = "Ring (Watts–Strogatz)"
T_GRID = "Gitter"
T_COMMUNITIES = "Verbünde"
T_RANDOM = "Zufallsnetz"
T_BA = "Skalenfreies Netz (BA)"
T_POWER = "Potenzgesetz-Netz"
T_TWO_GROUPS = "Zwei Gruppen mit Brücke"
ALL_TYPES = (T_RING, T_GRID, T_COMMUNITIES, T_RANDOM, T_BA, T_POWER, T_TWO_GROUPS)
# Experiment 1: (Zeilenname, Netztyp, Umverdrahtung, Anteil innen); die Zwei-Gruppen-Netze haben ihr eigenes Experiment
TYPE_CASES = (("Ring, regelmäßig", T_RING, 0.0, 0.8), ("Ring mit 5 % Abkürzungen", T_RING, 0.05, 0.8), (T_GRID, T_GRID, 0.0, 0.8), ("Verbünde (80 % innen)", T_COMMUNITIES, 0.0, 0.8),
              (T_RANDOM, T_RANDOM, 0.0, 0.8), (T_BA, T_BA, 0.0, 0.8), (T_POWER, T_POWER, 0.0, 0.8))
BLOCKS = 6
BRIDGE_WIDE, BRIDGE_SPREAD = "breit (gemeinsame Enden)", "verteilt (verschiedene Enden)"
BRIDGE_MODES = (BRIDGE_WIDE, BRIDGE_SPREAD)

C_MEANING = {
    T_RING: "Nachbarn auf dem Ring (c gerade gerundet); die Umverdrahtung legt Kanten auf zufällige Ziele",
    T_GRID: "Nachbarschaft: unter 6 vier Nachbarn, 6 bis 7 mit einer Diagonale, ab 8 mit beiden Diagonalen",
    T_COMMUNITIES: "mittlerer Grad; der Anteil innen bestimmt, wie viele Kanten im eigenen Verbund bleiben (6 Verbünde)",
    T_RANDOM: "mittlerer Grad des Zufallsnetzes",
    T_BA: "zwei Kanten je neuem Knoten, also m = c / 2 gerundet",
    T_POWER: "mittlerer Grad (Gradfolge mit Potenzgesetz-Exponent 2,5, Konfigurationsmodell)",
    T_TWO_GROUPS: "mittlerer Grad innerhalb jeder der beiden Gruppen; dazu die Brücke",
}

N_MIN, N_MAX, DEFAULT_N = 60, 250, 150
C_MIN, C_MAX, DEFAULT_C = 3, 12, 6
SEED_MAX, DEFAULT_SEED = 999999, 35
BETA_MIN, BETA_MAX, DEFAULT_BETA = 0, 100, 0         # Umverdrahtung in Prozent (Ring)
INSIDE_MIN, INSIDE_MAX, DEFAULT_INSIDE = 20, 99, 80   # Anteil der Kanten innerhalb der Verbünde in Prozent
WIDTH_MIN, WIDTH_MAX, DEFAULT_WIDTH = 1, 5, 2         # Breite der Brücke (Zwei Gruppen)
R_MIN, R_MAX, DEFAULT_R = 1, 5, 2                     # Schwelle als Zahl der übernommenen Nachbarn
THETA_MIN, THETA_MAX, DEFAULT_THETA = 5, 60, 34       # Schwelle als Anteil der übernommenen Nachbarn in Prozent
G_MIN, G_MAX, DEFAULT_G = 1, 10, 5                    # Größe der Startgruppe (ein Betrieb und g - 1 Partner)
SWEEP_SEEDS = tuple(range(100000, 100008))             # feste Netze für alle Sweeps: nie ein einzelner Seed als Befund
LIVE_SEEDS = SWEEP_SEEDS[:4]
STARTS_PER_NET = 5                                    # Startgruppen je Netz in den Messreihen

RULE_COUNT, RULE_SHARE = "Zahl r der Nachbarn", "Anteil θ der Nachbarn"
RULES = (RULE_COUNT, RULE_SHARE)
DEFAULT_RULE = RULE_COUNT

# --- Experimente ----------------------------------------------------------------------------------------------------------------------------------
THRESHOLDS = (1, 2, 3)
SHORTCUT_BETAS = (0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
WATTS_THETA = 0.18
WATTS_ZS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0)
WATTS_N, WATTS_STARTS = 1000, 25                      # Netzgröße und Startknoten je Netz im Kaskadenfenster
COMMUNITY_INSIDES = (0.8, 0.9, 0.93, 0.95, 0.97, 0.99)
COMMUNITY_DEGREES = (8, 12)
BRIDGE_WIDTHS = (1, 2, 3, 4, 5)
FULL_SHARE = 0.9                                      # ein Lauf gilt als vollständig ab diesem Endanteil

# --- Darstellung ---------------------------------------------------------------------------------------------------------------------------------
COLOR_EDGE = "rgba(120,120,120,0.30)"
COLOR_SEED = "#d62728"
COLOR_A = "#2F6B65"
COLOR_B = "#c4623b"
COLOR_C = "#6b5b95"
R_COLORS = {1: "#2F6B65", 2: "#c4623b", 3: "#6b5b95", 4: "#9d755d", 5: "#4c78a8"}

PRESETS = {
    "Ring ohne Abkürzungen (Voreinstellung)": {"netztyp": T_RING, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": DEFAULT_INSIDE, "width": DEFAULT_WIDTH,
                                               "mode": BRIDGE_WIDE, "rule": RULE_COUNT, "r": DEFAULT_R, "theta": DEFAULT_THETA, "g": DEFAULT_G},
    "Abkürzungen: der Kipppunkt": {"netztyp": T_RING, "n": 250, "c": DEFAULT_C, "seed": 37, "beta": 50, "inside": DEFAULT_INSIDE, "width": DEFAULT_WIDTH,
                                   "mode": BRIDGE_WIDE, "rule": RULE_COUNT, "r": DEFAULT_R, "theta": DEFAULT_THETA, "g": DEFAULT_G},
    "Zufallsnetz: kaum gemeinsame Partner": {"netztyp": T_RANDOM, "n": DEFAULT_N, "c": 4, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": DEFAULT_INSIDE, "width": DEFAULT_WIDTH,
                                               "mode": BRIDGE_WIDE, "rule": RULE_COUNT, "r": DEFAULT_R, "theta": DEFAULT_THETA, "g": DEFAULT_G},
    "Gemeinschaften halten auf": {"netztyp": T_COMMUNITIES, "n": DEFAULT_N, "c": 8, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": 97, "width": DEFAULT_WIDTH,
                                  "mode": BRIDGE_WIDE, "rule": RULE_COUNT, "r": DEFAULT_R, "theta": DEFAULT_THETA, "g": DEFAULT_G},
    "Brücke zu schmal": {"netztyp": T_TWO_GROUPS, "n": 120, "c": 12, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": DEFAULT_INSIDE, "width": 1,
                         "mode": BRIDGE_WIDE, "rule": RULE_COUNT, "r": DEFAULT_R, "theta": DEFAULT_THETA, "g": DEFAULT_G},
    "Anteilsregel: Hubs sind schwer zu überzeugen": {"netztyp": T_BA, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": DEFAULT_INSIDE, "width": DEFAULT_WIDTH,
                                                     "mode": BRIDGE_WIDE, "rule": RULE_SHARE, "r": DEFAULT_R, "theta": 34, "g": DEFAULT_G},
    "Kaskadenfenster: ein Startbetrieb genügt": {"netztyp": T_RANDOM, "n": DEFAULT_N, "c": 4, "seed": DEFAULT_SEED, "beta": DEFAULT_BETA, "inside": DEFAULT_INSIDE, "width": DEFAULT_WIDTH,
                                                 "mode": BRIDGE_WIDE, "rule": RULE_SHARE, "r": DEFAULT_R, "theta": 18, "g": 1},
}
PRESET_HELP = {
    "Ring ohne Abkürzungen (Voreinstellung)": "Regelmäßiger Ring mit sechs Nachbarn, Schwelle 2: die Ansteckung wandert Runde für Runde um den Ring.",
    "Abkürzungen: der Kipppunkt": "Ring mit 50 % Abkürzungen: die einfache Ansteckung wäre in wenigen Runden fertig, die Schwelle 2 bleibt in den meisten Läufen stecken (dieser Zufalls-Seed zeigt so einen Lauf; ein anderer kann das Netz füllen).",
    "Zufallsnetz: kaum gemeinsame Partner": "Zufallsnetz mit vier Partnern je Betrieb: zwei Partner eines Betriebs haben fast nie einen gemeinsamen Partner, die Schwelle 2 stockt sofort.",
    "Gemeinschaften halten auf": "Sechs Verbünde mit 97 % der Kanten innen: die Schwelle 2 füllt den eigenen Verbund und kommt nicht über die Grenze.",
    "Brücke zu schmal": "Zwei dichte Gruppen, verbunden durch eine einzige Kante: eine einfache Ansteckung geht hinüber, die Schwelle 2 nicht.",
    "Anteilsregel: Hubs sind schwer zu überzeugen": "Ein Anteil von 34 % der Partner: Knoten mit vielen Partnern brauchen viele Übernehmer, die Ausbreitung bleibt in der Startgruppe.",
    "Kaskadenfenster: ein Startbetrieb genügt": "Zufallsnetz mit vier Partnern, Anteil 18 %, ein einziger Startbetrieb: Betrieben mit höchstens fünf Partnern genügt ein übernommener Partner, daraus wird eine Kaskade (Experiment 3 zeigt das Fenster).",
}
DEFAULT_PRESET_NAME = "Ring ohne Abkürzungen (Voreinstellung)"
