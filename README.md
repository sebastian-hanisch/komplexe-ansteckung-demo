# Komplexe Ansteckung: wann reicht ein Kontakt? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-komplexe-ansteckung-demo.streamlit.app/)** -->

Sechstes Stück der **Netzwerkanalyse-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, im Ausbreitungs-Arm die Fortsetzung der Einflussmaximierung (Stück 5, die einfache Ansteckung mit einer Wahrscheinlichkeit je Kontakt); Zusammenfluss mit Stück 3 (Breite statt Länge der Brücken) und Stück 2 (Gemeinschaften bremsen oder tragen). Die [Demo zu Kaskaden](https://sebastianhanisch-kaskaden-demo.streamlit.app/) rechnet SIR und lastbasierte Kaskaden, aber keine Schwellenregel über die Zahl oder den Anteil der Partner.

Ein Betrieb in einem Netz von Subunternehmern und Lieferanten übernimmt ein neues Verfahren, sobald mindestens ***r*** seiner Partner es getan haben, oder ein Anteil **θ** seiner Partner. Eine **Startgruppe** (ein Betrieb und bis zu *g* − 1 seiner Partner) beginnt; in Runden prüfen alle Betriebe gleichzeitig, bis niemand mehr dazukommt (deterministische Schwelle, das **Bootstrap-Perkolationsmodell** der Physik). Die Demo stellt die **einfache Ansteckung** (*r* = 1) der **komplexen** (*r* = 2, 3 oder Anteil θ) gegenüber.

## Kernfrage

**Wann reicht ein Kontakt, wann braucht es mehrere, und woran hängt der Unterschied?** Der Gesamtplan vermutete „Abkürzungen helfen bei *r* = 1 und schaden bei *r* ≥ 2“ und „Gemeinschaften tragen komplexe, bremsen einfache Ausbreitung“. Beide Vermutungen sind in dieser Form **nicht** eingetreten (siehe Hypothesen); an ihre Stelle tritt der Befund, der in der Demo steht: es gibt einen **Kipppunkt**, und es zählt die **Breite** der Verbindungen, nicht ihre Länge oder Kantenzahl.

## Befunde und Korrekturen gegenüber dem Plan

- **Abkürzungen im Ring: ein Kipppunkt, kein einfaches „schaden“.** Bei *r* = 2 beschleunigen Abkürzungen zunächst (61 Runden ohne, 22 bei 20 % Abkürzungen); ab 30 % füllt die Ausbreitung das Netz nur noch in 42,5 % der Läufe, bei 100 % nie. Bei *r* = 3 genügt schon 1 % Abkürzungen (nur noch 25 % der Läufe füllen), ab 5 % keiner mehr.
- **Gemeinschaften halten die komplexe, nicht die einfache Ansteckung auf** (umgekehrt zur Plan-Vermutung): die einfache kennt keine Grenze (außerhalb des Startverbunds 100 % auch bei 99 % Kanten innen); die komplexe (*r* = 2) bleibt ab 95 % Kanten innen (mittlerer Grad 8) bzw. 97 % (Grad 12) im eigenen Verbund.
- **Die Breite entscheidet:** eine Brücke aus *w* Tor-Knoten, die vollständig mit *w* Tor-Knoten der anderen Seite verbunden sind, trägt die Schwelle *r* ab *w* = *r*; dieselben *w* · *w* Kanten mit paarweise verschiedenen Enden tragen *r* ≥ 2 nie. Für *r* = 3 füllt sich die Gruppe hinter der Brücke erst ab *w* = 4, bei *w* = 3 übernehmen nur die drei Tor-Knoten.
- **Dreiecke sind nötig, ihr Anteil allein sagt den Befund nicht voraus:** das Potenzgesetz-Netz hat mehr Kanten mit gemeinsamem Partner (54 %) als Verbünde (36 %) und skalenfreies Netz (35 %) und füllt bei *r* = 2 seltener.
- **Ein einzelner Starter genügt für *r* ≥ 2 nie** (jeder Lauf bleibt bei einem Betrieb); schon zwei Betriebe reichen im Ring mit 5 % Abkürzungen in 97,5 % der Läufe.
- **Anteilsregel θ = 34 %: Hubs sind schwer zu überzeugen.** Nur der regelmäßige Ring (6 Partner, nötig 3) und das Gitter mit 8 Partnern füllen; in Netzen mit stark schwankendem Grad (Zufallsnetz, skalenfrei, Verbünde) bleibt sie bei den Startenden stehen.
- **Kaskadenfenster nach Watts:** die eigene Rechnung sagt für θ = 18 % ein Fenster 1,02 < *z* < 5,76 voraus; gemessen lösen im Fenster im Mittel 80 % der Einzelstarter eine Kaskade aus, außerhalb 6 %.

## Modell

Deterministische Schwellen: ein Betrieb *v* mit *d*<sub>*v*</sub> Partnern übernimmt in Runde *t* + 1, wenn mindestens *s*<sub>*v*</sub> Partner bis Runde *t* übernommen haben; *s*<sub>*v*</sub> = *r* (Regel „Zahl“) oder max(1, ⌈θ · *d*<sub>*v*</sub>⌉) (Regel „Anteil“, Grad 0 nie). Die Regel ist monoton (wer übernommen hat, bleibt), der Endzustand ist die kleinste Menge, die die Startgruppe enthält und von außen nicht mehr überzeugt wird, und hängt nicht von der Reihenfolge ab. Mit *r* = 1 ist es Erreichbarkeit. Zufall steckt nur in Netz und Startgruppe (Zufalls-Seed). Der 📐-Expander der App enthält die Formeln einschließlich der Bedingung für das Kaskadenfenster.

## Methodik

| Baustein | Inhalt |
|---|---|
| **Netze** | Zufallsnetz, Gitter, skalenfrei (BA), Potenzgesetz-Netz (Generatoren aus `k-core-demo`, Stück 1, als Kopie); Ring mit Umverdrahtung β (Watts–Strogatz), Verbünde (Blockmodell, 6 gleich große Gruppen, Anteil innen einstellbar), zwei Gruppen mit Brücke der Breite *w* (breit oder verteilt) |
| **Regel** | Zahl *r* (1 bis 5) oder Anteil θ (5 bis 60 %); Startgruppe *g* = 1 bis 10 |
| **Experiment 1** | Endanteil, Anteil der Läufe mit mindestens 90 % und Runden je Netztyp und *r* = 1, 2, 3 (40 Läufe je Zelle: acht Netze mit je fünf Startgruppen) |
| **Experiment 2** | Ring mit β von 0 bis 100 %: Läufe, die das Netz füllen, und Runden je *r* |
| **Experiment 3** | Kaskadenfenster: Zufallsnetz mit 1 000 Betrieben, θ = 18 %, ein einzelner Startbetrieb, mittlerer Grad *z* von 0,5 bis 8; gegen die Formel Σ *k*(*k* − 1) *p*<sub>*k*</sub> > *z* |
| **Experiment 4** | Verbünde: Endanteil im Startverbund und außerhalb über den Anteil der Kanten innen, mittlerer Grad 8 und 12 |
| **Experiment 5** | Zwei Gruppen: breite gegen verteilte Brücke über die Breite *w* = 1 bis 5 |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle mit je fünf Startgruppen (40 Läufe), *n* = 250, *c* = 6, Startgruppe *g* = 5, wo nichts anderes steht. „Füllt“ heißt: mindestens 90 % der Betriebe haben übernommen.

| Frage | Befund |
|---|---|
| **Stimmen die Bausteine?** | *r* = 1 stimmt mit den Zusammenhangskomponenten und Abständen aus `networkx` überein (200 Zufallsnetze); der Endzustand ist die kleinste von außen nicht mehr überzeugte Obermenge der Startgruppe (Aufzählung aller Teilmengen, 200 Netze mit bis zu 11 Knoten, Zahl- und Anteilsregel); eine asynchrone Fassung in zufälliger Reihenfolge landet in derselben Menge (200 Netze); die Runde jeder Übernahme stimmt mit einer naiven Schleife überein (100 Netze); das Kaskadenfenster stimmt mit `scipy` (Poisson, Bisektion) und mit *z* · *Q*(*K*\* − 1, *z*) über die regularisierte unvollständige Gammafunktion überein; der Ring ohne Umverdrahtung ist der `networkx`-Ring (`tests/test_oracle_komplexe_ansteckung.py`) |
| **Welche Netze tragen welche Schwelle?** (*c* = 6, *g* = 5; Anteil füllender Läufe) | **r = 1: alle sieben Netze 100 %** (Runden: Ring 41, Ring mit 5 % Abkürzungen 8, Gitter 19, Verbünde 5, Zufallsnetz 4, skalenfrei 3, Potenzgesetz 4). **r = 2:** Ring, Ring mit 5 %, Gitter **100 %**, skalenfrei 85 %, Verbünde (80 % innen) 67,5 %, Potenzgesetz 30 %, **Zufallsnetz 15 %** (Endanteil im Median 2 %). **r = 3:** nur der regelmäßige Ring 100 % (122 Runden), skalenfrei 10 %, alle anderen 0 % |
| **Wie viele Kanten haben einen gemeinsamen Partner?** | Ring 100 %, Ring mit 5 % 95 %, Gitter 100 %, Potenzgesetz 54 %, Verbünde 36 %, skalenfrei 35 %, Zufallsnetz **12 %** (Median über die acht Netze) |
| **Wie viele Abkürzungen verträgt die Schwelle 2?** (Ring, *c* = 6, β = 0 / 1 / 5 / 10 / 20 / 30 / 50 / 100 %) | Läufe, die füllen: *r* = 2: 100 / 100 / 100 / 100 / **77,5** / **42,5** / **25** / **0 %**. Runden der füllenden Läufe, *r* = 1: 41 / 19 / 8 / 6 / 5 / 5 / 4 / 4; *r* = 2: 61 / 61 / 51 / 35 / **22** / 18 / 18,5 / –. *r* = 3: 100 % bei β = 0, **25 %** bei 1 %, 0 % ab 5 % |
| **Gibt es ein Kaskadenfenster?** (θ = 18 %, *n* = 1 000, ein Startbetrieb; Anteil Läufe mit Kaskade über 5 %) | Formel: **1,02 < *z* < 5,76** (*K*\* = 5). Gemessen bei *z* = 0,5 / 1 / 1,5 / 2 / 3 / 4 / 5 / 5,5 / 6 / 6,5 / 7 / 8: 0 / 3,5 / **75,5** / 85 / **94** / 91 / 74,5 / 58 / 26,5 / 5,5 / 0,5 / 0 %. Größe der großen Kaskaden im Median 98 % bei *z* = 4. Fenster nur für θ ≤ 25 % (θ = 26 % und größer: keines) |
| **Halten Gemeinschaften die Schwelle 2 auf?** (6 Verbünde, *n* = 240, *g* = 5; Anteil außerhalb des Startverbunds, bei 80 / 90 / 93 / 95 / 97 / 99 % Kanten innen) | Grad 8: 100 / 99,5 / **40,5** / **0** / 0 / 0 %. Grad 12: 100 / 100 / 100 / **100** / **0** / 0 %. Im Startverbund 100 %, insgesamt 1/6. **Schwelle 1: überall 100 %**, auch bei 99 % innen |
| **Wie breit muss die Brücke sein?** (zwei Gruppen, *n* = 120, *c* = 12; Läufe, in denen mindestens die Hälfte der anderen Gruppe übernimmt, *w* = 1 bis 5) | **breit:** *r* = 1: 100 % bei jedem *w*; *r* = 2: 0 / 87,5 / 100 / 100 / 100 %; *r* = 3: 0 / 0 / **12,5** / 70 / 95 %. **verteilt (dieselben *w* · *w* Kanten):** *r* = 1: 100 %, *r* = 2 und 3: **0 %** bei jedem *w*. Bei *w* = 3, *r* = 3 übernehmen im Median 5 % der anderen Gruppe (die drei Tor-Knoten von 60) |
| **Anteilsregel** (*n* = 250, *c* = 6, Anteil füllender Läufe: regelmäßiger Ring / Ring mit 5 % / Gitter / Verbünde / Zufall / skalenfrei / Potenzgesetz) | **θ = 34 %:** 100 / 5 / 0 / 0 / 0 / 0 / 10 %; das Gitter mit 8 Partnern füllt zu 100 % (29,5 Runden), bei θ = 50 % nicht mehr. **θ = 20 %:** 100 / 100 / 100 / 100 / 100 / 97 / 82 % |
| **Startgruppe** | *g* = 1, *r* = 2: in allen 280 Läufen (sieben Netztypen) bleibt es bei einem Betrieb. Ring mit 5 % Abkürzungen, *r* = 2: Läufe, die füllen, bei *g* = 2 / 3 / 5 / 10: 97,5 / 97,5 / 100 / 100 % |
| **Standardnetz** (Ring, *n* = 150, *c* = 6, Seed 35, *g* = 5, *r* = 2) | 450 Kanten; alle 150 Betriebe übernehmen nach **36** Runden; *r* = 1 braucht 24, *r* = 3 braucht 72 |
| **Preset Abkürzungen: der Kipppunkt** (Ring, *n* = 250, β = 50 %, Seed 37) | 750 Kanten; die Schwelle 2 bleibt bei 9 von 250 Betrieben stehen (2 Runden), 26 Betriebe sind knapp davor; *r* = 1 füllt das Netz nach 4 Runden |
| **Preset Zufallsnetz** (*n* = 150, *c* = 4) | 300 Kanten; *r* = 2: 7 Betriebe nach 1 Runde, 25 knapp davor; *r* = 1: 147 Betriebe nach 5 Runden (die übrigen 3 hängen nicht mit der Startgruppe zusammen) |
| **Preset Gemeinschaften halten auf** (*n* = 150, *c* = 8, 97 % innen) | 626 Kanten; *r* = 2: 25 von 150 (ein Verbund), nach 3 Runden, 5 knapp davor, außerhalb 0 %; *r* = 1: alle 150 nach 6 Runden |
| **Preset Brücke zu schmal** (zwei Gruppen, *n* = 120, *c* = 12, *w* = 1) | 718 Kanten; *r* = 2: genau die erste Gruppe (60 von 120) nach 3 Runden, 1 Betrieb knapp davor; *r* = 1: alle 120 nach 6 Runden |
| **Preset Anteilsregel** (skalenfrei, *n* = 150, *c* = 6, θ = 34 %) | 444 Kanten; θ = 34 %: 6 von 150 nach 1 Runde, 15 knapp davor; *r* = 2 füllt dasselbe Netz zu 150 von 150, *r* = 1 nach 3 Runden |
| **Preset Kaskadenfenster** (Zufallsnetz, *n* = 150, *c* = 4, θ = 18 %, *g* = 1) | 147 von 150 nach 7 Runden aus einem einzigen Startbetrieb; mit *c* = 8 bleibt es bei 2 Betrieben, mit *c* = 3 sind es 146 |

### Hypothesen des Einzelplans

| | Hypothese | Ergebnis |
|---|---|---|
| H1 | *r* = 1 ist Erreichbarkeit, der Endzustand hängt nicht von der Reihenfolge ab | ✅ Orakel: 200 Netze gegen `networkx`, 200 Netze asynchron gegen synchron, 0 Abweichungen |
| H2 | Komplexe Ansteckung braucht überlappende Nachbarschaften (Dreiecke) | ⚠ teilweise: Zufallsnetz (12 % der Kanten mit gemeinsamem Partner) füllt bei *r* = 2 nur 15 %; Ring und Gitter (100 %) 100 %; aber das Potenzgesetz-Netz (54 %) füllt seltener (30 %) als skalenfrei (35 %, 85 %) |
| H3 | Abkürzungen schaden bei *r* ≥ 2 | ⚠ nur teilweise: bei *r* = 2 beschleunigen sie bis 20 %, kippen ab 30 % (42,5 % füllen), 100 % nie; bei *r* = 3 kippt es schon bei 1 % (25 %); bei *r* = 1 verkürzen sie die Zeit (41 → 4 Runden) |
| H4 | Die Brückenbreite entscheidet | ✅ breite Brücke ab *w* = *r* (*r* = 2: ab 2); verteilte Kanten tragen *r* ≥ 2 nie; ⚠ bei *r* = 3 füllt sich die Gruppe dahinter erst ab *w* = 4 (12,5 % bei *w* = 3) |
| H5 | Kaskaden gibt es nur in einem Fenster des mittleren Grades (Watts) | ✅ Formel 1,02 bis 5,76; gemessen 75,5 % bei 1,5 bis 58 % bei 5,5, aber 0 % bei 0,5 und 8; am Rand verschwimmt es (3,5 % bei 1, 26,5 % bei 6) |
| H6 | Gemeinschaften tragen die komplexe, bremsen die einfache Ansteckung | ⚠ **umgekehrt:** die einfache kennt keine Grenze (100 % überall), die komplexe (*r* = 2) hält ab 95 % (Grad 8) bzw. 97 % (Grad 12) Kanten innen an der Grenze an |
| H7 | Anteilsregel: Hubs sind schwerer zu überzeugen als Randknoten | ✅ θ = 34 % füllt nur Netze mit gleichem Grad (Ring, Gitter mit 8 Partnern), θ = 20 % fast alle |

## Ehrliche Grenzen

- **Deterministische Schwellen, gleiche Schwelle für alle, kein Rückschritt, statisches Netz, keine Gegenmaßnahme.** Mit Wahrscheinlichkeiten je Kontakt (wie in Experimenten mit Menschen) verschwimmt der Kipppunkt; bei verteilten Schwellen entscheidet ihre Verteilung (Granovetter 1978).
- **Startgruppe statt Einzelstarter:** der Befund hängt von ihrer Größe und ihrem Zusammenhalt (Regler *g*).
- **Modellbefund:** die Demo zeigt Verhalten im Modell, keine Wirkung in der Wirklichkeit; die Lücke zwischen Modellen der sozialen Einflüsse und empirischen Tests ist groß (Flache u. a. 2017).
- **Synthetische Netze** mit *n* bis 250 (Kaskadenfenster: 1 000), Mediane über acht feste Netze; die Streuung zwischen den Netzen ist nicht ausgewiesen. Das Gitter hat Randknoten; das Zwei-Gruppen-Netz ist ein Handbeispiel; die Verbünde-Experimente haben *n* = 240 (gleich große Gruppen).
- **Der Median des Endanteils allein täuscht:** bei den Verbünden mit *r* = 2 liegt er bei 98 %, aber nur 67,5 % der Läufe füllen das Netz; darum zeigt Experiment 1 beide Größen.
- **Kaskadenfenster: eigene Rechnung.** Die Bedingung Σ *k*(*k* − 1) *p*<sub>*k*</sub> > *z* über die Betriebe mit Grad ≤ ⌊1/θ⌋ im Poisson-Netz ist die hier hergeleitete Form (Molloy–Reed auf den verwundbaren Teil) und lässt sich als *z* · *Q*(*K*\* − 1, *z*) > 1 schreiben, wie sie nach dem frei zugänglichen Text von Watts (2002) für Poisson-Netze mit einheitlicher Schwelle steht. Die dort genannten Zahlenwerte (nach einer Abfrage der Veröffentlichung *z* ≈ 1,05 und *z* ≈ 6,14 für θ = 0,18, nicht sicher einer Abbildung zuzuordnen) stimmen am oberen Ende nicht mit 5,76 überein; das ist **nicht geklärt**. Das Fenster ist zudem nur eine Bedingung für eine zusammenhängende Gruppe verwundbarer Betriebe; die Simulation mit *n* = 1 000 zeigt es nur ungefähr.
- **Literatur:** die bibliografischen Angaben im 📐-Expander sind nachgeschlagen (Centola und Macy 2007, Seiten 702–734; Watts 2002, 5766–5771; Granovetter 1978, 1420–1443; Flache u. a. 2017); die Arbeiten selbst sind nicht vollständig gelesen.

## Verifikation

- **Kern:** Handwerte auf Mini-Instanzen (`tests/conftest.py`, `tests/test_algorithm.py`): Pfad (stockt), Dreiecksstreifen (Knoten *i* übernimmt in Runde *i* − 1), Stern, zwei Vierer-Cliquen mit Brücke *K*<sub>*w*,*w*</sub> (*r* = 2 geht bei *w* = 1 nicht, bei *w* = 2 durch), Anteilsregel mit Rundung ohne Fließkommarauschen, Startgruppe, Zustand nach Runde *t*, „knapp davor“, Kaskadenfenster.
- **Orakel:** `tests/test_oracle_komplexe_ansteckung.py` – *r* = 1 gegen `networkx`, Endzustand gegen Aufzählung aller Teilmengen, Reihenfolge-Unabhängigkeit, Runden gegen eine naive Schleife, Kaskadenfenster gegen `scipy` und gegen die Gammafunktion, Ring gegen `networkx`, Brückenstruktur gegen eine unabhängige Zählung.
- **Netze:** gültig in allen Ecken der Regler und für alle Typen, deterministisch je Seed (auch über Prozesse mit verschiedenem Hash-Seed), Blockmodell-Wahrscheinlichkeiten von Hand, Anteil innen und mittlerer Grad statistisch (`tests/test_scenario.py`).
- **Verdikte:** jede Schwelle und jede Zahl im Text an von Hand gesetzten Werten (`tests/test_verdicts.py`), Randfälle (Regler-Ecken ohne Warnungen, Startgruppe größer als der Grad, Schwelle größer als jeder Grad, kleinste Netze in allen Experimenten, jede Runde der Abbildung) in `tests/test_edge_cases.py`.
- **Befunde:** jede Zahl dieser README in `tests/test_claims.py`.
- **Mutationsprüfung des Kerns:** (`kpa_algorithm.py`, 120 Stellen, ohne die langsamen Aussagen-Tests in der Suite der Überlebenden): nach Ergänzung von Tests keine Überlebenden; 15 Stellen sind als äquivalent festgehalten (Gitterfeinheit und Schrittzahl der Bisektion in der Fensterrechnung, Gleichheit bei exakt null, Reihenfolge einer Menge, Grenzfälle der Aufzählung, bei denen die kleinste abgeschlossene Menge eindeutig ist, `z >= 0` statt `z > 0` in der Poisson-Wahrscheinlichkeit). Zustand in `tests/mutation_state.json`.
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, jedes Preset zeigt, wofür es benannt ist.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, jeder Netztyp mit beiden Regeln, Runden-Regler, Permalink, alle fünf Experimente) und Footer-Test.
- **Layout:** Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben; jede Änderung eines Reglers hebt die Markierung auf (`tests/test_layout.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `kpa_algorithm.py` | Kern: Schwellen-Ausbreitung, Fixpunkt durch Aufzählung (Orakel), Startgruppe, „knapp davor“, Kaskadenfenster |
| `kpa_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `kpa_evaluation.py` | Analyse, Verdikt-Logik, Messreihen über feste Netze |
| `kpa_layout.py` | Fester Kopf (Stylesheet) |
| `kpa_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kpa_scenario.py` | Netze: Generatoren (Kopie aus `k-core-demo`), Ring, Blockmodell, zwei Gruppen, Anordnung |
| `kpa_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx, scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen und Handwerte, Orakel, Netze, Verdikte, Randfälle, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe, Befunde |

## Bewusst nicht umgesetzt

- **Wahrscheinlichkeit je Kontakt** (probabilistische komplexe Ansteckung) und **verteilte Schwellen:** eigene Fragen; als möglicher Ausbau (gelb).
- **Experimente mit Menschen** (Centola 2010 u. a.): nur genannt, nicht nachgestellt.
- **Gewichtete oder gerichtete Netze, zeitliche Netze, Gegenmaßnahmen:** Stück 13 (zeitliche Netze) und Stück 7 (Eindämmung).
- **Netze über 250 Betriebe live** (Kaskadenfenster 1 000): die Messreihen rechnen im Browser, die Dauer wächst mit Netzgröße und Zahl der Läufe.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
