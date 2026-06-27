# Guida Test — GraphStreamer

Come provare il progetto su Windows.

---

## Prerequisiti

- Python 3.8+ (usa `py` su Windows)
- Gephi con Graph Streaming Plugin installato
- Repository clonato in locale

---

## Step 1 — Setup ambiente Python

```bash
cd c:\Users\benci\Documents\GraphArte\GraphStreamer

py -m venv venv

.\venv\Scripts\python -m pip install -r requirements.txt
```

Verifica:
```bash
.\venv\Scripts\python -c "import librosa; import requests; import yaml; print('OK')"
```

---

## Step 2 — Prepara Gephi

1. Apri Gephi e carica il tuo file `.gephi` / `.graphml` / `.gexf`
2. Applica ForceAtlas per posizionare i nodi, poi **fermalo** (pannello Layout → Stop)
3. Vai nel pannello **Streaming** → espandi **Master** → **Master Server** → **Start**
4. Verifica: apri browser su `http://localhost:8080/love_phases?operation=getGraph`
   - La pagina resta in caricamento = OK
   - Errore 404 = workspace nome sbagliato o server spento

> Il workspace si chiama `love_phases` (tutto minuscolo, senza spazi).
> Se lo hai rinominato dopo aver avviato il server: Stop → Start.

---

## Step 3 — Testa la connessione

```bash
.\venv\Scripts\python -c "import requests; r=requests.get('http://localhost:8080/love_phases?operation=getGraph', timeout=(3,2), stream=True); print('Connesso OK')"
```

Se stampa "Connesso OK" sei pronto.

---

## Step 4a — Lancia Unfold (animazione grafo)

```bash
.\venv\Scripts\python src\unfold.py
```

Guarda Gephi: tutti i nodi collassano al centro, poi si rivelano in tre fasi (desiderio → attrazione → legame).

Configurazione in `config/unfold.yaml`.

---

## Step 4b — Lancia Pulse (pulsazione ritmica)

```bash
.\venv\Scripts\python src\pulse.py
```

Il grafo pulsa a BPM configurabili. Configurazione in `config/pulse.yaml`.

---

## Step 4c — Lancia con audio (main.py)

```bash
.\venv\Scripts\python src\main.py percorso\al\file.wav
```

Il grafo reagisce ai beat e alle frequenze dell'audio. Configurazione in `config/mapping.yaml`.

---

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| `ModuleNotFoundError` | Usa `.\venv\Scripts\python`, non `python` |
| Nodi non si muovono | ForceAtlas ancora attivo in Gephi? Fermalo. |
| "Nessun nodo trovato" | Carica un grafo in Gephi prima di lanciare |
| Errore 404 sul workspace | Il workspace si chiama `love_phases`? Master Server attivo? |
| label_groups conta 0 nodi | Esegui una volta con `refresh_positions: true` per leggere i dati molecola |
