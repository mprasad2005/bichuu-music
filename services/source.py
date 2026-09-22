from pathlib import Path
import asyncio
from urllib.request import Request, urlopen
import yt_dlp
from config import (
    DOWNLOAD_DIR,
    FFMPEG_LOCATION,
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    YTDLP_COOKIES_FILE,
)

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

async def search_and_download(query: str):
    # Keep source handling isolated so another provider/API can be plugged in later.
    def work():
        opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
                ),
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                },
            },
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        if FFMPEG_LOCATION:
            opts["ffmpeg_location"] = FFMPEG_LOCATION
        if YTDLP_COOKIES_FILE:
            opts["cookiefile"] = YTDLP_COOKIES_FILE
        search = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search, download=True)
            if "entries" in info:
                info = info["entries"][0]
            filename = ydl.prepare_filename(info)
            mp3 = str(Path(filename).with_suffix(".mp3"))
            thumbnail = None
            thumbnail_url = info.get("thumbnail")
            if thumbnail_url:
                thumbnail = str(Path(DOWNLOAD_DIR) / f"{info['id']}.jpg")
                try:
                    request = Request(
                        thumbnail_url,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    with urlopen(request, timeout=20) as response:
                        Path(thumbnail).write_bytes(response.read())
                except Exception:
                    thumbnail = None
            return {
                "title": info.get("title", "Unknown"),
                "url": info.get("webpage_url", query),
                "duration": info.get("duration") or 0,
                "thumbnail": thumbnail,
                "file": mp3,
            }
    return await asyncio.to_thread(work)

async def import_playlist(query: str):
    if "spotify.com" in query.lower():
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise ValueError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to import Spotify playlists.")

        def spotify_work():
            import importlib
            import re

            spotipy = importlib.import_module("spotipy")
            spotify_auth = importlib.import_module("spotipy.oauth2")

            match = re.search(r"playlist/([A-Za-z0-9]+)", query)
            if not match:
                raise ValueError("Invalid Spotify playlist URL.")
            client = spotipy.Spotify(
                auth_manager=spotify_auth.SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET,
                )
            )
            results = []
            offset = 0
            while True:
                page = client.playlist_items(
                    match.group(1),
                    offset=offset,
                    limit=100,
                    fields="items(track(name,artists(name))),next",
                )
                for item in page.get("items", []):
                    track = item.get("track") or {}
                    title = track.get("name")
                    artists = ", ".join(a["name"] for a in track.get("artists", []))
                    if title:
                        results.append({"title": title, "query": f"{artists} - {title}"})
                if not page.get("next"):
                    return results
                offset += 100

        return await asyncio.to_thread(spotify_work)

    def work():
        opts = {
            "extract_flat": "in_playlist",
            "ignoreerrors": True,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,
        }
        if YTDLP_COOKIES_FILE:
            opts["cookiefile"] = YTDLP_COOKIES_FILE
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
        entries = info.get("entries", []) if info else []
        return [
            {
                "title": entry.get("title", "Unknown"),
                "query": entry.get("webpage_url") or entry.get("url"),
            }
            for entry in entries
            if entry and (entry.get("webpage_url") or entry.get("url"))
        ]

    return await asyncio.to_thread(work)
