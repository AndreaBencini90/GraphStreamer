# Guida Unfold — animazione grafo a fasi

## Cosa fa

`src/unfold.py` anima un grafo Gephi in tre passi:

1. Collassa tutti i nodi al centro del canvas
2. Li rivela uno a uno verso la loro posizione finale, con ease-out
3. Lo fa in **fasi configurabili**: ogni fase ha velocita' diversa e puo' includere solo certi tipi di molecole

L'ordine narrativo attuale: desiderio → attrazione → legame.

---

## Prerequisiti

- Virtual environment attivo (`.\venv\Scripts\python`)
- Gephi aperto con il grafo **love_phases** caricato
- **ForceAtlas fermato** (pannello Layout → Stop) — se e' attivo sovrascrive le posizioni
- Master Server attivo nel pannello Streaming di Gephi

---

## Come lanciare

```bash
.\venv\Scripts\python src\unfold.py
```

Da qualsiasi posizione nel progetto. Lo script trova da solo `config/unfold.yaml`.

---

## Cosa appare nel terminale

```
Carico posizioni da unfold_positions.json...
567 nodi caricati.

  gruppo ['GnRH', 'Sostanza P']: 45 nodi
  gruppo ['CRF', 'Menk-PC', 'Menk-Bic']: 120 nodi
  gruppo ['Ossitocina', 'Vasopressina', 'Beta-Endorfina']: 180 nodi

Ho in memoria 567 nodi e 3 fasi.
  fase 1: 1 nodi/sec per 20s  (~20 nodi, da t=0s)
  fase 2: 5 nodi/sec per 20s  (~100 nodi, da t=20s)
  fase 3: 20 nodi/sec per 20s  (~400 nodi, da t=40s)
  durata stimata: 63s

Raccolgo tutto al centro...
Comincio a dispiegare la struttura.

  [#...................]  12/567  —  qualcosa si muove nel disordine
  [####................]  89/567  —  i nodi cercano il loro posto nello spazio
  ...
```

---

## Parametri da modificare in `config/unfold.yaml`

### transition_seconds
Durata dell'animazione di ogni singolo nodo (da centro a posizione finale).
- `1.0` = scatto rapido, quasi teleport
- `3.0` = volo fluido (attuale)
- `6.0` = lentissimo, poetico

### phases — struttura di base

```yaml
phases:
  - label_groups: ["GnRH", "Sostanza P"]   # molecole di questa fase
    nodes_per_second: 1                      # quanti nodi partono al secondo
    duration_seconds: 20                     # per quanti secondi
```

`nodes_per_second` controlla la densita' visiva:
- `1` = un nodo al secondo, si vede ogni singolo movimento
- `5` = piccolo flusso
- `20` = cascata veloce
- `100+` = esplosione quasi istantanea

### Narrativa attuale (8 molecole, 3 fasi)

| Fase | Nome | Molecole | Velocita' |
|------|------|----------|-----------|
| 1 | DESIDERIO | GnRH, Sostanza P | 1 nodo/sec × 20s |
| 2 | ATTRAZIONE | CRF, Menk-PC, Menk-Bic | 5 nodi/sec × 20s |
| 3 | LEGAME | Ossitocina, Vasopressina, Beta-Endorfina | 20 nodi/sec × 20s |

I nodi non assegnati ad alcuna molecola vengono rivelati alla fine, alla velocita' dell'ultima fase.

---

## Aggiornare lo snapshot (refresh_positions)

Lo snapshot (`unfold_positions.json`) contiene le posizioni e i dati molecola salvati da Gephi.

Serve rifarlo quando:
- hai riapplicato ForceAtlas e le posizioni sono cambiate
- e' la prima volta che usi label_groups (il vecchio snapshot potrebbe non avere il campo `group`)

Come farlo:
1. Apri Gephi con il grafo, applica ForceAtlas, poi **Stop**
2. Avvia Master Server
3. In `config/unfold.yaml` metti `refresh_positions: true`
4. Lancia `.\venv\Scripts\python src\unfold.py`
5. Dopo che ha letto i nodi e salvato, rimetti `refresh_positions: false`

---

## Troubleshooting

| Problema | Causa probabile | Soluzione |
|----------|-----------------|-----------|
| Nodi non si muovono | ForceAtlas attivo in Gephi | Stop nel pannello Layout |
| "Nessun nodo trovato" | Master Server spento o grafo non caricato | Riavvia Master Server |
| label_groups non ordina i nodi | Snapshot vecchio senza dati molecola | Esegui una volta con `refresh_positions: true` |
| Gephi restituisce 0 nodi in refresh | Timeout di connessione | Riprova, o controlla che il workspace si chiami `love_phases` |
| "Snapshot senza dati molecola" | Il campo `group` e' vuoto | Come sopra, esegui refresh |
