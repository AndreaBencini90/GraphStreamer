# GraphStreamer

Sistema Python che anima grafi in Gephi in tempo reale, tramite il Graph Streaming Plugin.

Due modalita' principali:
- **Unfold** — i nodi collassano al centro e si rivelano in fasi narrative (desiderio / attrazione / legame)
- **Pulse** — il grafo pulsa a tempo come un metronomo visivo
- **Audio** — il grafo reagisce ai beat e alle frequenze di un file audio

---

## Quick Start

```bash
# 1. Crea e attiva il virtual environment
py -m venv venv
.\venv\Scripts\python -m pip install -r requirements.txt

# 2. Apri Gephi, carica il grafo, ferma ForceAtlas, avvia Master Server

# 3. Lancia
.\venv\Scripts\python src\unfold.py   # animazione narrativa
.\venv\Scripts\python src\pulse.py    # pulsazione ritmica
.\venv\Scripts\python src\main.py file.wav  # audio-driven
```

---

## Struttura

| Cartella / File | Contenuto |
|-----------------|-----------|
| `src/unfold.py` | Animazione in fasi: collassa → rivela per gruppo molecolare |
| `src/pulse.py` | Pulsazione a BPM configurabili |
| `src/main.py` | Loop audio → beat → azioni Gephi |
| `src/audio_analyzer.py` | Beat tracking + bande frequenza |
| `src/gephi_client.py` | Client HTTP per Graph Streaming Plugin |
| `config/unfold.yaml` | Parametri unfold: fasi, velocita', snapshot, workspace |
| `config/pulse.yaml` | Parametri pulse: BPM, forze, durata |
| `config/mapping.yaml` | Mappa frequenze/beat → azioni sul grafo |
| `unfold_positions.json` | Snapshot posizioni nodi (generato automaticamente) |
| `docs/` | Documentazione completa |

---

## Configurazione rapida (unfold)

Tutto in `config/unfold.yaml`:

```yaml
gephi:
  workspace: "love_phases"    # nome workspace Gephi

unfold:
  transition_seconds: 3.0     # durata animazione singolo nodo
  fps: 10
  refresh_positions: false    # true = rilegge posizioni da Gephi

  phases:
    - label_groups: ["GnRH", "Sostanza P"]           # FASE 1 - DESIDERIO
      nodes_per_second: 1
      duration_seconds: 20
    - label_groups: ["CRF", "Menk-PC", "Menk-Bic"]  # FASE 2 - ATTRAZIONE
      nodes_per_second: 5
      duration_seconds: 20
    - label_groups: ["Ossitocina", "Vasopressina", "Beta-Endorfina"]  # FASE 3 - LEGAME
      nodes_per_second: 20
      duration_seconds: 20
```

---

## Documentazione

-> [docs/GUIDA_UNFOLD.md](docs/GUIDA_UNFOLD.md) — guida completa unfold con parametri e troubleshooting
-> [docs/GUIDA_TEST.md](docs/GUIDA_TEST.md) — setup passo-passo dalla prima installazione
-> [docs/INDEX.md](docs/INDEX.md) — indice completo documentazione
