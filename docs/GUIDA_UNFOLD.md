# 🎬 Guida Unfold — Nodi che si aprono uno a uno

## Cosa fa

- Legge il grafo già presente in Gephi (nodi + archi + posizioni)
- Collassa tutti i nodi in un punto al centro
- Uno per uno, ogni nodo si muove dal centro alla sua posizione finale
- Animazione fluida con ease-out
- Durata e velocità configurabili

---

## Prerequisiti

- Virtual environment attivo con dipendenze installate
- Gephi aperto con un **grafo già caricato** (con nodi posizionati)
- Master Server attivo su `workspace1`

---

## Step 1 — Carica un grafo in Gephi

Apri uno dei tuoi file `.gephi` o `.graphml` o `.gexf` in Gephi. Assicurati che i nodi abbiano posizioni (esegui un layout tipo Force Atlas una volta, poi fermalo).

---

## Step 2 — Avvia Master Server

1. Pannello Streaming → espandi Master → Master Server
2. Start

Verifica: `http://localhost:8080/workspace1?operation=getGraph` deve caricare (non 404).

---

## Step 3 — Lancia unfold

```bash
cd c:\Users\048115571\Documents\GraphStreamer
.venv\Scripts\activate
cd src
python unfold.py
```

Guarda Gephi: i nodi partono tutti dal centro e si aprono uno alla volta.

---

## Configurazione

Modifica `config/unfold.yaml`:

```yaml
unfold:
  duration_seconds: 60       # durata totale animazione
  transition_seconds: 1.0    # tempo per ogni nodo (centro → posizione finale)
  fps: 30                    # fluidità
```

Esempi:
- Vuoi che duri 2 minuti? → `duration_seconds: 120`
- Vuoi transizioni più lente? → `transition_seconds: 2.0`
- Vuoi che sia più veloce tra un nodo e l'altro? → riduci `duration_seconds`

---

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| "Nessun nodo trovato" | Carica un grafo in Gephi prima di lanciare |
| Nodi non si muovono | Master Server attivo? Workspace = `workspace1`? |
| Animazione troppo veloce | Aumenta `duration_seconds` o `transition_seconds` |
| Animazione a scatti | Aumenta `fps` (max 60) |
