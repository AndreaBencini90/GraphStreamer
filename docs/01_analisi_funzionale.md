# Analisi Funzionale — "Grafo che ascolta la musica"

## 1. Obiettivo del progetto

Costruire un sistema che **ascolta una traccia musicale** (da file o da microfono), ne
**rileva il ritmo e le caratteristiche spettrali**, e traduce questi eventi in
**azioni visive su un grafo Gephi** in tempo reale, tramite il Graph Streaming Plugin.

L'effetto percepito: il grafo "pulsa", si espande e cambia colore **a tempo di musica**,
rendendo evidente all'osservatore che *il grafo sta ascoltando*.

Il progetto fa parte della ricerca artistica generativa dell'autore (visualizzazioni di
rete, strutture probabilistiche). L'obiettivo non è un visualizzatore audio commerciale,
ma uno **strumento espressivo** dove la mappatura suono→azione è essa stessa parte
dell'opera.

## 2. Concetto chiave: "flag sì / flag no" a tempo

Il comportamento di base richiesto è ritmico e binario:

- Il sistema identifica un **ritmo ricorrente** (il battito, il beat).
- A ogni battito esegue **una singola azione ripetuta** (un "flag").
- L'azione si alterna o si ripete a tempo, come un metronomo visivo.

Questo è il **movimento minimo** da cui partire: un solo evento (il beat) mappato su una
sola azione (la pulsazione di un nodo). Tutto il resto è estensione di questo nucleo.

## 3. Principio di estensibilità (rimappabilità)

Requisito esplicito: l'architettura deve permettere, in futuro, di **rimappare eventi
diversi su azioni diverse** senza riscrivere il sistema.

Esempi di mappature future:
- beat → pulsazione del nodo centrale
- nota/banda dei bassi → espansione di un cluster
- nota/banda degli acuti → cambio colore di un sottografo
- onset (attacco di nota) → creazione di un arco temporaneo

La logica di mappatura va quindi **isolata in un livello dedicato e configurabile**
(vedi Architettura), non cablata nel codice di analisi audio.

## 4. Ambito per fasi

### Fase 0 — Canale Gephi (COMPLETATA, già verificata manualmente)
Il canale Python→Gephi funziona. Comando di test già validato:
invio di un nodo via `updateGraph` → il nodo compare nel grafo.
Path confermato: `http://localhost:8080/workspace1`.

### Fase 1 — MVP: file audio → beat → pulsazione (PRIORITÀ)
- Input: file audio (mp3/wav).
- Analisi **offline** della traccia per estrarre i tempi dei battiti (beat times).
- Riproduzione audio sincronizzata.
- A ogni beat: un nodo "flag" **pulsa** (size aumenta + colore cambia, poi decade).
- Animazione **minimale** ma chiaramente percepibile.

Criterio di successo: guardando Gephi durante la riproduzione, l'osservatore vede il
nodo pulsare esattamente a tempo con la musica.

### Fase 2 — Input da microfono (live)
- Cattura audio dal microfono in streaming.
- Rilevamento **in tempo reale** di onset/beat su finestra scorrevole.
- Stesse azioni della Fase 1, ma senza pre-analisi.
- Maggiore tolleranza alla latenza (il live è intrinsecamente meno preciso dell'offline).

### Fase 3 — Mapping configurabile
- Introduzione del livello di mappatura dichiarativo.
- Separazione dello spettro in bande (bassi / medi / acuti).
- File di configurazione che associa (tipo_evento, banda, condizione) → azione_grafo.
- Possibilità di cambiare la mappatura senza toccare il codice.

### Fase 4 — Visualizzazione note + punto d'azione (DA VALUTARE INSIEME)
Punto aperto sollevato dall'autore: *"magari è meglio rappresentare le note musicali e
il punto dove è stimata l'azione"*.

Proposta da discutere (vedi §6): nodi-banda dedicati che si illuminano in funzione
dell'energia spettrale, così l'osservatore vede **cosa** il grafo sta sentendo, non solo
**quando** agisce.

## 5. Comportamenti funzionali (Fase 1, dettaglio)

| ID | Comportamento | Descrizione |
|----|---------------|-------------|
| F1 | Caricamento traccia | Il sistema accetta un percorso a file audio e lo carica. |
| F2 | Estrazione beat | Calcola i tempi (in secondi) di ogni battito della traccia. |
| F3 | Riproduzione sincronizzata | Riproduce l'audio e tiene un orologio allineato. |
| F4 | Trigger d'azione | Quando l'orologio raggiunge un beat time, emette un evento "beat". |
| F5 | Pulsazione nodo | All'evento beat, il nodo flag aumenta size + cambia colore. |
| F6 | Decadimento | Dopo la pulsazione, size e colore tornano gradualmente allo stato di riposo. |
| F7 | Indicatore "in ascolto" | Lo stato visivo deve rendere evidente che il grafo è attivo e sta ricevendo audio. |

## 6. Decisione di design aperta — visualizzazione

Tre opzioni per rendere chiaro che "il grafo ascolta", da scegliere insieme:

**Opzione A — Nodo flag singolo.**
Un solo nodo centrale che pulsa a tempo. Minimale, pulito, ma mostra solo il *quando*.

**Opzione B — Nodo flag + 3 nodi-banda (RACCOMANDATA per la Fase 1 estesa).**
Un nodo centrale che pulsa sul beat, più tre nodi (bassi/medi/acuti) la cui dimensione
segue l'energia spettrale in tempo reale. L'osservatore vede sia il *quando* (beat) sia
il *cosa* (contenuto frequenziale). Resta minimale ma molto più espressivo.

**Opzione C — Overlay con notazione musicale.**
Mappare le frequenze su note (Do, Re, Mi...) e mostrare la nota stimata + il punto in cui
scatta l'azione. Più complesso, più "didascalico"; valutare se serve davvero o se
appesantisce l'estetica.

Raccomandazione: partire con **A** in Fase 1 per validare la sincronia, poi passare a
**B**. Tenere **C** come esplorazione successiva, da decidere quando vediamo il
risultato di B.

## 7. Vincoli e note

- Sistema operativo target: **Windows** (l'autore lavora su Windows).
- Gephi con Graph Streaming Plugin, Master Server attivo, workspace `workspace1`.
- Il sistema **non** deve dipendere da Internet: tutto gira in locale.
- La latenza accettabile in Fase 1 (file) è quasi nulla (analisi offline + sync).
  In Fase 2 (mic) è tollerata una latenza di poche decine di ms.
