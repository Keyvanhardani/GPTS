import os
import re
import json
import logging
import asyncio
import shutil
import time  # Für kurzen Sleep nach dem Schließen von Files
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from moviepy.editor import *

# Hier importieren wir die Audio-FX von MoviePy

# OpenAI (aktuelle Version >=1.0.0, mit TTS support)
from openai import OpenAI

# AsyncWebCrawler
from crawl4ai import AsyncWebCrawler

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})


font="C:/Windows/Fonts/arialbd.ttf"



# --------------------------------------------------------------------
# 1. Environment laden
# --------------------------------------------------------------------
load_dotenv(override=True)
openai_api_key = os.environ.get("OPENAI_API_KEY")
news_api_key = os.environ.get("NEWS_API_KEY")
pexels_api_key = os.environ.get("PEXELS_API_KEY")

# --------------------------------------------------------------------
# 2. Logging
# --------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --------------------------------------------------------------------
# 3. OpenAI-Client
# --------------------------------------------------------------------
client = OpenAI(api_key=openai_api_key)

# --------------------------------------------------------------------
# 4. Asynchrones Scrapen
# --------------------------------------------------------------------
async def scrap(url_):
    async with AsyncWebCrawler(verbose=True, headless=False) as crawler:
        result = await crawler.arun(url=url_)
        return result.markdown

# --------------------------------------------------------------------
# 5. ChatCompletion-Prompt
# --------------------------------------------------------------------
def generate_content(prompt: str) -> str:
    """
    Ruft das ChatCompletions-Endpoint auf (OpenAI >=1.0.0).
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Oder gpt-4 / gpt-3.5-turbo / etc.
            messages=[
                {
                    "role": "developer",
                    "content": "You are a helpful assistant. Return only valid text or JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8
        )
        # content ist jetzt eine Property, kein Subskript
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error in generate_content: {str(e)}")
        return ""

# --------------------------------------------------------------------
# 6. News via NewsAPI
# --------------------------------------------------------------------
# https://newsapi.org/v2/everything?q=2025&from=2024-12-25&to=2024-12-25&sortBy=popularity&apiKey=f54b0ad7269941cab3db0a5609c6baee
def get_tech_news(api_key, days=1):
    url = "https://newsapi.org/v2/everything"
    date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    params = {
        'apiKey': api_key,
        'q': 'München',
        #'category': 'technology',
        #'country': 'us',
        'from': date,
        'to': date,
        'sortBy': 'popularity',
        'pageSize': 100
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('articles'):
            articles = []
            for a in data['articles']:
                articles.append({
                    'title': a.get('title'),
                    'description': a.get('description'),
                    'url': a.get('url'),
                    'source': a['source']['name'],
                    'published_at': a.get('publishedAt')
                })
            return {
                'status': 'success',
                'total_results': len(articles),
                'articles': articles
            }
        else:
            return {
                'status': 'success',
                'total_results': 0,
                'articles': []
            }
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching news: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# --------------------------------------------------------------------
# 7. Top-Artikel auswählen
# --------------------------------------------------------------------
def get_top(json_string_for_articles):
    prompt = (
        "From the given list of articles, choose top 5 tech articles that "
        "can catch the attention of the readers. "
        f"{json_string_for_articles} "
        "Give output as a JSON array of indexes. "
        "Example: ```json\n[1,2,3,4,5]\n```"
    )
    response_text = generate_content(prompt)
    return get_json(response_text)

# --------------------------------------------------------------------
# 8. Reel-Prompt
# --------------------------------------------------------------------
def reel_prompt(title, text):
    return f"""
    Create a concise and engaging script for a short Instagram Reels video using the tech article: "{title}".
    Article details: {text}

    The script will be narrated as is in the video.
    Use 'keywords' array for video search from Pexels.

    but dont give the text with Scene! just the text for each Scene. not Scene 1:text!
    use a creative design for "keywords".

    Output JSON:
    {{
        "title": "Title of the article (suitable for Reels)",
        "script": ["Scene 1 text", "Scene 2 text", "Scene 3 text"],
        "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
    """

# --------------------------------------------------------------------
# 9. JSON-Parsing
# --------------------------------------------------------------------
def get_json(text):
    try:
        if "```" in text:
            txt_extract = text.split("```")[1]
            txt_extract = txt_extract.replace("json", "").strip()
            return json.loads(txt_extract)
        else:
            return json.loads(text.strip())
    except Exception as e:
        logging.error(f"Error parsing JSON: {str(e)}\nGiven text was:\n{text}")
        return None

# --------------------------------------------------------------------
# 10. Dateinamen säubern
# --------------------------------------------------------------------
def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

# --------------------------------------------------------------------
# 11. Pexels-Videos herunterladen
# --------------------------------------------------------------------
def download_pexels_videos(query, base_path, api_key, num_videos=3):
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": min(num_videos, 80),
    }
    url = "https://api.pexels.com/videos/search"

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    videos = data.get("videos", [])
    downloaded_videos = []
    for i, video in enumerate(videos):
        if i >= num_videos:
            break

        video_files = video.get("video_files", [])
        best_quality = sorted(video_files, key=lambda x: x.get("width", 0), reverse=True)
        if best_quality:
            download_url = best_quality[0]["link"]
            try:
                v_resp = requests.get(download_url, stream=True)
                v_resp.raise_for_status()
                file_extension = os.path.splitext(download_url)[1] or ".mp4"
                file_name = f"{query}_{video.get('id')}{file_extension}"
                file_name = os.path.join(base_path, file_name)

                with open(file_name, 'wb') as f:
                    for chunk in v_resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                print(f"Downloaded: {file_name}")
                downloaded_videos.append(file_name)
            except Exception as e:
                print(f"Error downloading video: {e}")
    return downloaded_videos

# --------------------------------------------------------------------
# 12. TTS via OpenAI
# --------------------------------------------------------------------
def generate_tts(text: str, output_path: str, voice="nova", model="tts-1"):
    """
    Nutzt die OpenAI TTS API, um den Text in Audio umzuwandeln.
    Speichert das Ergebnis als MP3 in output_path.
    """
    try:
        logging.info(f"Generating TTS via OpenAI. Voice={voice}, Model={model}...")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        # Direkt in Datei streamen
        response.stream_to_file(output_path)
    except Exception as e:
        logging.error(f"Error generating TTS audio: {str(e)}")

# --------------------------------------------------------------------
# 13. Reel erstellen
# --------------------------------------------------------------------
def create_multiline_subtitles(scene_text, video_width, video_height):
    """
    Erzeugt ein TextClip-Objekt, das den Text auf maximal 80% der Videobreite
    hält und automatisch in mehrere Zeilen umbricht.
    """

    subtitle_font_size = int(video_height * 0.035)   # ca. 3.5% der Höhe
    subtitle_box_width = int(video_width * 0.8)      # max 80% der Videobreite
    subtitle_y_offset = video_height - 225           # 180px vom unteren Rand
    subtitle_color = 'white'

    txt_clip = TextClip(
        txt=scene_text,
        fontsize=subtitle_font_size,
        color=subtitle_color,
        font="C:/Windows/Fonts/arialbd.ttf",  # oder ein anderer Font
        stroke_color='black',
        stroke_width=2,
        method='caption',          # => automatische Zeilenumbrüche
        align='center',            # mittig ausgerichtet
        size=(subtitle_box_width, None),  # begrenzt die Breite, Höhe dynamisch
        interline=5                # Zeilenabstand zwischen mehreren Zeilen
    ).set_position(
        ("center", subtitle_y_offset)
    )

    return txt_clip

def create_reel(content, base_folder, save_reel_path, audio_path):
    """
    Beispiel: Verwendet das obige TextClip-Template, um mehrzeilige,
    horizontale Untertitel am unteren Bildrand zu platzieren.
    """

    width, height = 480, 854
    clips = []
    audio = None

    downloaded_videos = download_pexels_videos(
        ', '.join(content['keywords']),
        base_folder,
        pexels_api_key,
        num_videos=3
    )
    if not downloaded_videos:
        print("No videos downloaded. Exiting.")
        return

    # Video-Clips vorbereiten
    video_clips = []
    for i in range(len(content['script'])):
        video_path = downloaded_videos[i % len(downloaded_videos)]
        try:
            clip = VideoFileClip(video_path).fx(vfx.resize, height=height)
            # Breitencrop/-padding
            if clip.w > width:
                margin = (clip.w - width) // 2
                clip = clip.crop(x1=margin, y1=0, x2=clip.w - margin, y2=height)
            elif clip.w < width:
                w_diff = width - clip.w
                x_padding = w_diff // 2
                clip = clip.margin(left=x_padding, right=x_padding, color=(0, 0, 0))

            video_clips.append(clip)
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            return

    try:
        audio = AudioFileClip(audio_path)
        total_audio_duration = audio.duration
        clip_duration = total_audio_duration / len(content['script'])

        # Pro Szenentext einen CompositeClip
        for i, scene_text in enumerate(content['script']):
            base_clip = video_clips[i].subclip(0, min(clip_duration, video_clips[i].duration))

            # Untertitel-Clip erzeugen
            txt_clip = create_multiline_subtitles(
                scene_text, width, height
            ).set_duration(clip_duration)

            final_clip = CompositeVideoClip([base_clip, txt_clip])
            clips.append(final_clip)

        # Alle Clips aneinanderhängen
        final_reel = concatenate_videoclips(clips, method="compose", bg_color=(0, 0, 0))
        final_reel = final_reel.set_audio(audio)

        # Speichern
        reel_path = os.path.join(save_reel_path, f"{sanitize_filename(content['title'])}.mp4")
        final_reel.write_videofile(
            reel_path,
            codec='libx264',
            fps=30,
            preset="ultrafast",
            threads=8,
            audio_codec="aac"
        )
        print(f"Reel saved to: {reel_path}")

    except Exception as e:
        print(f"Error creating reel: {e}")

    finally:
        if audio is not None:
            audio.close()
        time.sleep(0.5)





# --------------------------------------------------------------------
# 14. Hauptprozess
# --------------------------------------------------------------------
async def process_news_for_reel(base_path):
    os.makedirs(base_path, exist_ok=True)
    print("-" * 30)
    print("Starting Tech News Reels Creation")
    print("-" * 30)

    # News holen
    news_json = get_tech_news(news_api_key)
    if news_json.get('status') == 'error':
        print(f"Error fetching news: {news_json.get('message')}")
        return

    # Top-Artikel via OpenAI
    top_indices = get_top(json.dumps(news_json))
    if not top_indices:
        print("Error: Could not determine top articles.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    base_folder = os.path.join(os.getcwd(), today)
    os.makedirs(base_folder, exist_ok=True)

    # Schleife über die Top-Artikel
    for idx in top_indices:
        try:
            article = news_json['articles'][idx]
            title = article.get('title') or "No Title"
            url = article.get('url') or ""
            desc = article.get('description') or ""

            # Scrape
            try:
                text_from_url = await scrap(url)
                if not text_from_url:
                    text_from_url = f"{desc} Title: {title}"
            except Exception as e:
                print(f"Error scraping data: {str(e)}")
                text_from_url = f"{desc} Title: {title}"

            # Prompt ans Modell
            prompt = reel_prompt(title, text_from_url)
            response_text = generate_content(prompt)
            reel_content = get_json(response_text)
            if not reel_content:
                print(f"Skipping article due to JSON parsing failure: {title}")
                continue

            # TTS-Audio mit OpenAI
            print(f"Generating TTS audio for: {title}")
            audio_path = os.path.join(base_path, f"{sanitize_filename(title)}_audio.mp3")
            # Spreche den Script-Text => z. B. "Scene 1 text Scene 2 text Scene 3 text"
            generate_tts(" ".join(reel_content['script']), audio_path)
            time.sleep(3)

            # Reel erstellen
            print(f"Creating Reel for: {title}")
            create_reel(reel_content, base_path, base_folder, audio_path)
            print("-" * 30)

        except Exception as e:
            print(f"Error processing article: {str(e)}")

# --------------------------------------------------------------------
# 15. __main__
# --------------------------------------------------------------------
if __name__ == "__main__":
    base_path = "temp"
    asyncio.run(process_news_for_reel(base_path))

    # Falls du am Ende die temporären Dateien löschen willst:
    try:
        shutil.rmtree(base_path)
    except Exception as e:
        print(f"Warning: Could not remove temp folder: {str(e)}")
