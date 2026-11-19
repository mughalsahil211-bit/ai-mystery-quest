# AI Mystery Quest – Interactive Detective Game

A beginner-friendly Flask detective game. Investigate suspects, collect clues, solve logic challenges, request progressive hints, and consult Detective AI.

## Features
- Responsive detective-bureau interface.
- Demo cases available immediately without an API key.
- Optional Groq-powered case generation, hints, and case-aware chat.
- Evidence collection, puzzle scoring, final accusations, and JSON history.
- API key stays on the Python server in `.env`; it is never sent to the browser.

## Requirements
- Python 3.9+
- Optional: Groq API key from the Groq developer console.

## Run on Windows (PowerShell)
1. Extract the ZIP.
2. Open PowerShell inside the extracted `ai_mystery_quest` folder.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
4. Activate it:
   ```powershell
   .venv\\Scripts\\Activate.ps1
   ```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.
5. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
6. Copy `.env.example` to `.env`. Leave `GROQ_API_KEY` blank to use Demo Mode, or paste your own key after `=`.
7. Start the app:
   ```powershell
   py app.py
   ```
8. Open **http://127.0.0.1:5000** in your browser.

## Run on macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## How to play
1. Read the case story and inspect each suspect's motive and alibi.
2. Collect evidence. Each clue adds 20 points.
3. Solve the logic challenge. Correct answers earn the points shown; incorrect attempts cost 10 points.
4. Request hints if needed. Each hint costs 25 points.
5. Choose your accusation. A correct verdict earns 250 points; an incorrect verdict costs 50 points.
6. Open Case Archives to review previous investigations.

## Groq AI setup
- Create a Groq API key in your Groq account.
- Add it to `.env` as `GROQ_API_KEY=...`.
- Restart Flask.
- The app uses `GROQ_MODEL` from `.env`; default is `llama-3.3-70b-versatile`.
- If the key is missing, the SDK is unavailable, or a request fails, the app falls back to demo responses/cases.

## Project structure
```text
ai_mystery_quest/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   ├── cases.json
│   └── history.json
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Notes
- Game history is stored locally in `data/history.json`.
- Demo cases are defined in `app.py`, so the game still works when `data/cases.json` is empty.
- This is a local learning/demo project. For public deployment, add user accounts, CSRF protection, rate limiting, database storage, and a production WSGI server. Set a strong `FLASK_SECRET_KEY` and never commit `.env`.
