# Come collegare il repository da un altro PC

## 1. Clonare il repository
```bash
git clone https://github.com/AndreaBencini90/GraphStreamer.git
cd GraphStreamer
```

## 2. Accedere a GitHub da un altro PC
Se Git richiede autenticazione, usa:
- il tuo username GitHub
- oppure un Personal Access Token invece della password

## 3. Aggiornare e inviare modifiche
```bash
git pull origin main
git add .
git commit -m "Aggiornamento"
git push origin main
```

## 4. Se vuoi usare un altro PC senza rifare tutto
Il repository è già collegato al remoto:
```bash
git remote -v
```
