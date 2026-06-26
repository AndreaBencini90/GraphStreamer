# 🎵 GraphStreamer

Grafo che ascolta la musica — beat detection e frequency mapping verso Gephi in tempo reale.

---

## 📂 Indice del progetto

| Cartella | Contenuto |
|----------|-----------|
| [`docs/`](docs/INDEX.md) | Documentazione completa (analisi funzionale, architettura, requisiti) |
| [`src/`](src/) | Codice sorgente Python |
| [`config/`](config/) | File di configurazione YAML per il mapping audio → azioni |

---

## 🚀 Quick Start

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Avvia Master Server in Gephi (Streaming panel → Master → Start)

# 3. Lancia
cd src
python main.py <file_audio.wav>
```

---

## 📖 Struttura codice (`src/`)

| File | Ruolo |
|------|-------|
| `main.py` | Loop principale — sincronizza audio con Gephi |
| `audio_analyzer.py` | Analisi audio: beat tracking + bande di frequenza |
| `gephi_client.py` | Client HTTP per Gephi Graph Streaming Plugin |
| `unfold.py` | Animazione: nodi partono dal centro e si aprono uno a uno |
| `pulse.py` | Animazione: grafo pulsa con forze a tempo configurabile |
| `generate_test_audio.py` | Genera un file WAV di test con beat |

---

## ⚙️ Configurazione (`config/`)

| File | Ruolo |
|------|-------|
| `mapping.yaml` | Mappa frequenze/beat → azioni sul grafo (size, colore) |
| `unfold.yaml` | Config animazione unfold (durata, velocità, fps) |
| `pulse.yaml` | Config pulsazione a tempo (BPM, forze, durata) |

---

## 📚 Documentazione (`docs/`)

→ [Vai all'indice documentazione](docs/INDEX.md)
