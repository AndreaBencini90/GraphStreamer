# Requisiti Tecnici e Setup

## 1. Ambiente

- **Sistema operativo:** Windows 10/11 (target dell'autore).
- **Python:** 3.9 – 3.12 raccomandato (`librosa` e `sounddevice` hanno wheel stabili).
  Verificare con:
  ```cmd
  python --version
  ```
  Se Python non è installato: scaricarlo da python.org e spuntare
  "Add Python to PATH" durante l'installazione.
- **Gephi:** con Graph Streaming Plugin installato e Master Server attivabile.

## 2. Dipendenze Python

Contenuto di `requirements.txt`:

```
librosa>=0.10.0
soundfile>=0.12.0
sounddevice>=0.4.6
numpy>=1.24.0
scipy>=1.10.0
requests>=2.31.0
PyYAML>=6.0
```

Note:
- `librosa` tira dentro `numpy`/`scipy`, ma li elenchiamo esplicitamente per chiarezza.
- `soundfile` serve a `librosa` per leggere/scrivere WAV.
- Per leggere **MP3** su Windows può servire `ffmpeg` nel PATH (vedi §4).
- `sounddevice` richiede PortAudio: su Windows arriva già con la wheel pip.

## 3. Installazione

In un terminale (Prompt dei comandi):

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

(Se si usa un solo ambiente globale senza venv, basta l'ultima riga.)

## 4. MP3 su Windows (eventuale)

`librosa` decodifica MP3 tramite backend audio. Se il caricamento di un `.mp3` fallisce:

- Opzione semplice: lavorare in Fase 1 con file **WAV** (nessun backend extra).
- Opzione completa: installare **ffmpeg** e aggiungerlo al PATH
  (download da ffmpeg.org → estrarre → aggiungere la cartella `bin` alle variabili
  d'ambiente PATH). Riavviare il terminale dopo.

Test rapido del caricamento:
```python
import librosa
y, sr = librosa.load("traccia.wav", sr=None)
print(len(y), sr)
```

## 5. Setup Gephi (riepilogo operativo)

1. Aprire Gephi e creare/aprire un progetto.
2. Rinominare il workspace in `workspace1` (doppio click sulla tab del workspace, oppure
   menu Workspace → Rename).
3. Pannello in basso a sinistra → tab **Streaming**.
4. Espandere **Master** → tasto destro su **Master Server** → **Start**.
   (Se era già avviato prima della rinomina: **Stop** e poi **Start**.)
5. Verifica nel browser:
   ```
   http://localhost:8080/workspace1?operation=getGraph
   ```
   La pagina resta "in caricamento" senza errore = connesso correttamente (lo stream
   resta aperto in ascolto). Un **404** significa path sbagliato o server non riavviato
   dopo la rinomina.

### Parametri di rete di default
- Host: `localhost`
- Porta HTTP: `8080` (HTTPS su `8443`, non usato)
- Workspace path: `workspace1` (minuscolo, senza spazi)
- Autenticazione: nessuna
- URL base per il client Python: `http://localhost:8080/workspace1`

## 6. Verifica end-to-end del canale (prima di scrivere il software)

Da Prompt dei comandi, con Master Server attivo:

```cmd
curl "http://localhost:8080/workspace1?operation=updateGraph" -d "{\"an\":{\"A\":{\"label\":\"Ciao\",\"size\":10,\"r\":1,\"g\":0,\"b\":0,\"x\":0,\"y\":0}}}"
```

Atteso:
- La risposta riecheggia il JSON inviato.
- In Gephi compare un nodo rosso "Ciao" (premere **Reset Zoom** in basso a sinistra se
  non è inquadrato).

Se questo funziona, l'ambiente è pronto e il coding agent può procedere
all'implementazione partendo dalla Fase 1 dell'analisi funzionale.

## 7. Checklist pre-sviluppo

- [ ] `python --version` ≥ 3.9
- [ ] `pip install -r requirements.txt` completato senza errori
- [ ] Caricamento di un file audio di test riuscito (WAV o MP3)
- [ ] Gephi aperto, workspace = `workspace1`
- [ ] Master Server avviato (dopo eventuale rinomina)
- [ ] `getGraph` nel browser resta connesso senza 404
- [ ] Test `curl updateGraph` → nodo visibile in Gephi
