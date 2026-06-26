# Architettura Tecnica

## 1. Visione d'insieme

Pipeline a livelli, ognuno indipendente e sostituibile:

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌────────────────┐
│ INPUT AUDIO │ → │   ANALISI    │ → │   MAPPING     │ → │  GEPHI CLIENT  │
│ file / mic  │   │ beat/spettro │   │ evento→azione │   │ HTTP streaming │
└─────────────┘   └──────────────┘   └───────────────┘   └────────────────┘
                                                                  │
                                                                  ▼
                                                          ┌────────────────┐
                                                          │  GEPHI (UI)    │
                                                          │ Master Server  │
                                                          └────────────────┘
```

Principio guida: **l'analisi audio non sa nulla di Gephi**, e il client Gephi non sa
nulla di audio. Il livello di mapping è l'unico punto in cui i due mondi si incontrano,
ed è progettato per essere riconfigurabile (vedi §5).

## 2. Moduli

### 2.1 `audio_input/`
Responsabile di fornire campioni audio al resto del sistema, astraendo la sorgente.

- `FileSource`: carica un file (mp3/wav) con `librosa.load`. Espone l'array di campioni
  e il sample rate. Usato in Fase 1.
- `MicSource`: cattura dal microfono con `sounddevice` (PortAudio) in callback su buffer
  scorrevole. Usato in Fase 2.

Interfaccia comune (concettuale):
```
class AudioSource:
    sample_rate: int
    def read_block() -> np.ndarray   # blocco di campioni
    def total_duration() -> float    # solo file; None per mic
```

### 2.2 `analysis/`
Estrae eventi musicali dai campioni.

- `BeatDetector`
  - **Modalità file (offline):** `librosa.beat.beat_track` sull'intera traccia →
    restituisce `tempo` (BPM) e `beat_times` (array di secondi). Deterministico e preciso.
  - **Modalità live:** rilevamento onset su finestra scorrevole
    (`librosa.onset.onset_strength` + soglia adattiva, oppure spectral flux custom),
    con stima del tempo aggiornata incrementalmente.
- `SpectralBands`
  - Calcola l'energia in 3 bande tramite STFT: bassi (~20–250 Hz), medi (~250–4000 Hz),
    acuti (~4000–16000 Hz). Restituisce 3 valori normalizzati 0–1 per frame.
  - Serve per la visualizzazione Opzione B e per il mapping per banda (Fase 3).

Output del livello: un flusso di **eventi tipizzati**, es.:
```
BeatEvent(time=12.34)
BandEvent(time=12.34, bass=0.8, mid=0.3, treble=0.1)
OnsetEvent(time=12.50, strength=0.6)
```

### 2.3 `mapping/`
Cuore dell'estensibilità. Traduce eventi musicali → azioni sul grafo, **secondo una
configurazione dichiarativa** (non hard-coded).

- `Action`: descrizione astratta di cosa fare al grafo
  (es. "pulsa il nodo X", "imposta colore del nodo Y", "crea arco temporaneo").
- `MappingRule`: associazione (tipo_evento + condizione) → Action.
- `Mapper`: riceve gli eventi, valuta le regole, emette le azioni.

Vedi §5 per il formato della configurazione.

### 2.4 `gephi_client/`
Unico modulo che parla con Gephi. Incapsula il protocollo Graph Streaming.

- `GephiStreamClient`
  - Costruito con `base_url` (es. `http://localhost:8080/workspace1`).
  - Metodi: `add_node`, `update_node`, `delete_node`, `add_edge`, `update_edge`,
    `delete_edge`.
  - Ogni metodo costruisce il JSON evento corretto e fa `POST ...?operation=updateGraph`.
  - Usa `requests` con una sessione persistente; gli errori di rete non devono bloccare
    l'audio (log + skip).

### 2.5 `engine/`
Orchestratore. Tiene l'orologio, fa girare la pipeline, gestisce il loop di animazione.

- `Clock`: tempo di riproduzione. In modalità file è ancorato al playback audio.
- `AnimationLoop`: a ~30–60 fps invia gli aggiornamenti di decadimento (pulsazioni che
  rientrano, bande che seguono lo spettro). Necessario perché la pulsazione non è un
  evento singolo ma una transizione nel tempo.

## 3. Flusso di dati — Fase 1 (file)

```
1. FileSource carica traccia.
2. BeatDetector (offline) → beat_times[].
3. (opz.) SpectralBands pre-calcola energia per frame.
4. Engine avvia playback audio + Clock.
5. AnimationLoop a 30 fps:
   - se Clock ha superato il prossimo beat_time:
       Mapper(BeatEvent) → Action(pulse flag node)
       GephiStreamClient.update_node(flag, size=GRANDE, color=ACCESO)
   - per ogni nodo in pulsazione attiva:
       decadi size/color verso lo stato di riposo
       GephiStreamClient.update_node(...)
   - (opz. Opzione B) aggiorna nodi-banda con energia spettrale corrente.
6. A fine traccia: stop pulito, nodi tornano a riposo.
```

## 4. Protocollo Gephi Graph Streaming (RIFERIMENTO CRITICO)

Dettagli verificati direttamente durante il setup. **Da rispettare alla lettera.**

### 4.1 URL del workspace
Il path è il **nome del workspace in minuscolo e senza spazi**.
Il plugin internamente fa: `nome.replaceAll(" ", "").toLowerCase()`.

- Workspace `Workspace 1` → path `workspace1`
- Workspace `Project`     → path `project`

URL completo per scrivere:
```
http://localhost:8080/workspace1?operation=updateGraph
```
URL per leggere lo stream (resta appeso in ascolto, è normale):
```
http://localhost:8080/workspace1?operation=getGraph
```

### 4.2 Gotcha del riavvio (IMPORTANTE)
Se si rinomina il workspace **dopo** aver avviato il Master Server, il server continua a
servire il vecchio path. Sequenza corretta:
1. Rinomina il workspace.
2. Master Server → **Stop**.
3. Master Server → **Start**.
4. Solo ora il nuovo path è valido.

### 4.3 Formato eventi JSON
Ogni evento è un oggetto JSON inviato nel body del POST. Più eventi possono essere
concatenati separati da newline.

| Operazione | Chiave | Esempio |
|-----------|--------|---------|
| Add node | `an` | `{"an":{"flag":{"label":"Flag","size":10,"r":1,"g":0,"b":0,"x":0,"y":0}}}` |
| Change node | `cn` | `{"cn":{"flag":{"size":25,"r":1,"g":0.8,"b":0}}}` |
| Delete node | `dn` | `{"dn":{"flag":{}}}` |
| Add edge | `ae` | `{"ae":{"e1":{"source":"flag","target":"bass","directed":false,"weight":1}}}` |
| Change edge | `ce` | `{"ce":{"e1":{"weight":2}}}` |
| Delete edge | `de` | `{"de":{"e1":{}}}` |

Attributi nodo: `label`, `size` (float), `r`/`g`/`b` (0–1), `x`/`y` (posizione),
più attributi custom liberi. I colori sono **0–1**, non 0–255.

### 4.4 Comando di test già validato (curl, Windows)
```cmd
curl "http://localhost:8080/workspace1?operation=updateGraph" -d "{\"an\":{\"A\":{\"label\":\"Ciao\",\"size\":10,\"r\":1,\"g\":0,\"b\":0,\"x\":0,\"y\":0}}}"
```
Risposta attesa: l'eco del JSON inviato + nodo rosso "Ciao" visibile in Gephi.

## 5. Livello di mapping — formato configurazione

Obiettivo: cambiare la mappatura suono→azione **modificando un file**, non il codice.

Proposta: configurazione YAML/JSON con una lista di regole. Bozza:

```yaml
nodes:
  flag:   { label: "Flag",   rest_size: 8,  rest_color: [0.2, 0.2, 0.2], x: 0,   y: 0 }
  bass:   { label: "Bassi",  rest_size: 6,  rest_color: [0.1, 0.1, 0.4], x: -50, y: 0 }
  mid:    { label: "Medi",   rest_size: 6,  rest_color: [0.1, 0.4, 0.1], x: 0,   y: -50 }
  treble: { label: "Acuti",  rest_size: 6,  rest_color: [0.4, 0.1, 0.1], x: 50,  y: 0 }

rules:
  - on: beat
    action: pulse
    target: flag
    params: { peak_size: 25, peak_color: [1, 0.85, 0], decay_ms: 250 }

  - on: band
    band: bass
    action: scale_to_energy
    target: bass
    params: { min_size: 6, max_size: 30 }

  # esempio futuro — rimappare un onset acuto su creazione arco
  # - on: onset
  #   when: { band: treble, min_strength: 0.5 }
  #   action: flash_edge
  #   params: { source: flag, target: treble, ttl_ms: 400 }
```

Il `Mapper` legge questo file all'avvio. Aggiungere un comportamento = aggiungere una
regola, senza toccare analisi o client.

## 6. Scelte tecnologiche e motivazioni

| Esigenza | Scelta | Perché |
|----------|--------|--------|
| Carico/decodifica audio | `librosa` | standard de-facto, gestisce mp3/wav, integra l'analisi |
| Beat tracking offline | `librosa.beat.beat_track` | preciso e deterministico sul file intero |
| Analisi spettrale | `librosa` STFT | già disponibile, bande facili da estrarre |
| Cattura microfono | `sounddevice` | wheel precompilate su Windows, callback a bassa latenza |
| Riproduzione audio | `sounddevice` | stessa libreria, sync semplice con l'analisi |
| HTTP verso Gephi | `requests` | semplice, sessione persistente |
| Config mapping | `PyYAML` | leggibile, editabile a mano dall'autore-artista |

Nota su `aubio`: ottimo per beat tracking real-time, ma l'installazione su Windows è
storicamente problematica. Per la Fase 2 valutare prima un onset detector basato su
`librosa`/spectral-flux su buffer scorrevole; ricorrere ad `aubio` solo se la qualità
real-time non basta.

## 7. Gestione errori e robustezza

- Il client Gephi non deve mai bloccare il loop audio: try/except attorno alle POST,
  log dell'errore, continua.
- Se il Master Server non risponde all'avvio: messaggio chiaro all'utente con
  promemoria della sequenza (rinomina → stop → start) e dell'URL atteso.
- All'uscita: riportare i nodi allo stato di riposo (cleanup), opzionalmente lasciarli.

## 8. Struttura cartelle suggerita

```
grafo_ascolta/
├── audio_input/
│   ├── file_source.py
│   └── mic_source.py
├── analysis/
│   ├── beat_detector.py
│   └── spectral_bands.py
├── mapping/
│   ├── mapper.py
│   └── actions.py
├── gephi_client/
│   └── stream_client.py
├── engine/
│   ├── clock.py
│   └── animation_loop.py
├── config/
│   └── mapping.yaml
├── main.py
└── requirements.txt
```
