# 🧪 Guida Test MVP — GraphStreamer

Questa guida spiega come far girare il progetto per la prima volta su Windows.

---

## Prerequisiti

- **Python 3.8+** installato e disponibile da terminale (`python --version`)
- **Gephi** aperto con il **Graph Streaming Plugin** installato
- Un **file audio** in formato `.wav` (anche breve, 30 secondi bastano)

> Se non hai un .wav sotto mano, puoi convertire un mp3 con: `ffmpeg -i canzone.mp3 canzone.wav`
> Oppure scarica un sample gratuito da https://freesound.org

---

## Step 1 — Setup ambiente Python

```bash
cd c:\Users\048115571\Documents\GraphStreamer

# Crea virtual environment
python -m venv .venv

# Attiva il virtual environment
.venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt
```

Verifica che funzioni:
```bash
python -c "import librosa; import requests; import yaml; print('OK')"
```

Se stampa `OK` sei a posto.

---

## Step 2 — Prepara Gephi

1. Apri Gephi
2. Crea un nuovo progetto (File → New Project)
3. **Rinomina il workspace** in `workspace1` (doppio click sulla tab del workspace in alto)
4. Vai nel pannello **Streaming** (in basso a sinistra/destra)
5. Espandi **Master** → **Master Server**
6. **Avvia** il Master Server (tasto destro → Start, o pulsante ▶)

**Verifica:** apri il browser e vai su:
```
http://localhost:8080/workspace1?operation=getGraph
```
La pagina deve restare in caricamento (non errore 404). Se carica all'infinito = funziona.

---

## Step 3 — Test connessione manuale

Dal terminale (con il venv attivo):
```bash
curl "http://localhost:8080/workspace1?operation=updateGraph" -d "{\"an\":{\"test\":{\"label\":\"Test\",\"size\":20,\"r\":1,\"g\":0,\"b\":0,\"x\":0,\"y\":0}}}"
```

Guarda Gephi: deve comparire un nodo rosso chiamato "Test". Se lo vedi, la connessione è OK.

> In Gephi potrebbe servire cliccare **Reset Zoom** (lente in basso a sinistra) per centrare la vista sul nodo.

---

## Step 4 — Lancia GraphStreamer

```bash
cd src
python main.py "C:\percorso\al\tuo\file.wav"
```

Sostituisci il percorso con il tuo file audio reale.

**Cosa devi vedere:**
- Nel terminale: `Analyzing: ...` poi `Streaming X frames to Gephi`
- In Gephi: il nodo **pulsa** (diventa grande sui beat, piccolo tra i beat) e **cambia colore** in base alle frequenze:
  - 🔴 Rosso = bassi (kick, basso)
  - 🟢 Verde = medi (voce, chitarra)
  - 🔵 Blu = acuti (hi-hat, piatti)

Premi `Ctrl+C` nel terminale per fermare.

---

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| `ModuleNotFoundError` | Hai attivato il venv? `.venv\Scripts\activate` |
| Nodo non appare in Gephi | Master Server è attivo? Workspace si chiama `workspace1`? |
| `Connection refused` | Gephi non è aperto o il server è spento |
| Nodo non pulsa / colore fisso | Il file audio è troppo corto o silenzioso, prova un brano ritmato |
| `librosa` errore su `.mp3` | Installa ffmpeg: `pip install ffmpeg-python` oppure usa un `.wav` |

---

## Prossimi passi

Quando il test funziona:
1. Prova con brani diversi (elettronica, classica, rock) per vedere come reagisce
2. Modifica `config/mapping.yaml` per cambiare soglie e range di colore
3. Aggiungi più nodi al grafo in Gephi prima di lanciare — vedrai il nodo "center" pulsare in mezzo agli altri
