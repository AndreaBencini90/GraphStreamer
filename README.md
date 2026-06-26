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

---

## ⚙️ Configurazione (`config/`)

| File | Ruolo |
|------|-------|
| `mapping.yaml` | Mappa frequenze/beat → azioni sul grafo (size, colore) |

---

## 📚 Documentazione (`docs/`)

→ [Vai all'indice documentazione](docs/INDEX.md)
