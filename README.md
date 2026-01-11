# Telegram TXT Bot (Railway-ready)

## Files
- bot.py
- requirements.txt
- Dockerfile

## Run locally
```bash
pip install -r requirements.txt
python bot.py
```

## Deploy on Railway (Docker)
1. Create a GitHub repo (PRIVATE recommended).
2. Upload the files in this folder.
3. In Railway:
   - New Project → Deploy from GitHub repo
   - It will build using Dockerfile and start the bot.

## Commands
- /start : show help
- /x : start collecting texts
- send text messages or .txt files
- /a : export collected text to output.txt
- /f : clear collected texts (start fresh)
- /e : enter merge mode (send .txt files)
- /d : merge sent files into merged.txt
- /k : clear merge files (start fresh)
- /y 500 : split next sent .txt file into parts of 500 lines (sends parts as .txt files)
