# GPTS – GPT Short Creator

**GPTS (GPT Short Creator)** ist ein Python-basiertes Projekt, das automatisiert kurze Tech-News-Reels erzeugt, inklusive:
- **News-Abfragen** via [NewsAPI](https://newsapi.org/)
- **Textzusammenfassungen** über die [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat/)
- **Text-to-Speech** mithilfe der [OpenAI TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech)
- **Videomaterial** von [Pexels](https://www.pexels.com/)
- **Zusammensetzen** und **Rendern** mit [MoviePy](https://zulko.github.io/moviepy/)

## Features

- **Asynchrone Webrecherche**: Holt Artikel und URLs per AsyncWebCrawler.
- **Intelligente Zusammenfassung**: Nutzt GPT-Modelle, um die **Top-Artikel** auszuwählen und daraus ein Reels-Skript zu generieren.
- **TTS mit OpenAI**: Erzeugt gesprochenen Audiotrack in MP3-Format.
- **Automatisches Video-Cut**: Schneidet mehrere Clips zusammen, fügt Untertitel hinzu und rendert einen fertigen **Instagram Reel**.

## Installation & Setup

1. **Repo klonen**:
   ```bash
   git clone https://github.com/Keyvanhardani/GPTS.git
   cd GPTS
   ```
2. **Umgebung aufsetzen** (z. B. mit `venv`):
   ```bash
   python -m venv venv
   source venv/bin/activate  # (Linux/Mac)
   venv\Scripts\activate     # (Windows)
   ```
3. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```
4. **API-Keys eintragen**  
   Lege eine `.env` in der Projekt-Root an:
   ```bash
   OPENAI_API_KEY=...
   NEWS_API_KEY=...
   PEXELS_API_KEY=...
   ```

5. **ImageMagick**:
   - Ebenso sicherstellen, dass [ImageMagick](https://imagemagick.org/) installiert ist und MoviePy darauf zugreifen kann.
   - change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

## Nutzung

1. **News abfragen**  
   Das Skript zieht aktuelle Tech-News von [NewsAPI](https://newsapi.org/) (oder via Everything-Endpunkt).
2. **Top-Artikel bestimmen**  
   Per ChatCompletion-Endpunkt: Das Modell wählt interessante Artikel aus.
3. **Reels-Skript generieren**  
   OpenAI erstellt ein kurzes Skript + Keywords, um passende Clips von Pexels herunterzuladen.
4. **Audio generieren**  
   OpenAI TTS wandelt das Skript in gesprochenes Audio um.
5. **Video schneiden**  
   MoviePy kombiniert Videoclips + Audio + Untertitel = fertiges Reel!

## Quickstart

```bash
python app.py
```
- Legt automatisch einen Temp-Ordner an
- Holt die News
- Erstellt Reels in einem Tages-Ordner, z. B. `2024-12-27/`
- Speichert die fertigen MP4-Dateien

## Beispiele

| Feature | Screenshot |
|---------|-----------|
| APP | ![Screenshot](screenshot.png) |
| TTS-Generierung | [TTS-Openai](temp/tts-openai.mp3) |
| Pexels-Download-1 | [Video 1](temp/AI-01.mp4) | 
| Pexels-Download-2 | [Video 2](temp/AI-02.mp4) |  
| Pexels-Download-3 | [Video 3](temp/AI-03.mp4) |
| MoviePy-Schnitt | [Final Video](2024-12-27/AI.mp4) |

## Roadmap

- [ ] Besseres Prompt Engineering für noch präzisere Artikel-Auswahl  
- [ ] Benutzerdefinierte TTS-Stimmen  
- [ ] Umsetzung in Docker-Container  
- [ ] CLI-Interface für Skript-Parameter

## TODO
- UI Expansion: Create a graphical user interface to manage article selection, TTS voices, etc.
- Linux Pipeline: Optimize the script for Linux-based environments, ensuring all dependencies are installed.
- Short Translation: Offer reel subtitles or entire scripts in multiple languages, selectable in the UI.

## Lizenz

- GNU General Public License v2.0 
