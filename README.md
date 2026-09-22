# Telegram Music Bot — Modular Base

A modular Telegram group music bot built around Pyrogram + PyTgCalls + FFmpeg + yt-dlp.

## Included
- `/play`, `/pause`, `/resume`, `/skip`, `/stop`, `/queue`, `/nowplaying`
- `/volume`, `/skip`, `/stop`, `/end`, `/leave`
- Inline playback controls
- Per-chat queue
- SQLite persistence for settings, playlists and basic statistics
- Admin-only moderation controls for player commands
- `/playlist add|remove|list|play`
- Per-group settings
- Basic usage statistics
- External source adapter (`yt-dlp`) kept isolated in `services/source.py`
- Docker deployment files
- Environment configuration
- Clean module boundaries for adding external features later

## Important
PyTgCalls currently requires Python 3.10+ and an MTProto client/API credentials. The project supports Pyrogram/Telethon/Hydrogram clients. See the current PyTgCalls project for the latest API details.

A bot token alone is not enough for every voice-chat workflow; configure an assistant MTProto user session with `API_ID`, `API_HASH`, and `STRING_SESSION`.

Use only audio you are authorized to access/stream and comply with the terms of the source service.

## Setup
1. Install Python 3.10+ and FFmpeg.
2. Create a Telegram bot with BotFather.
3. Obtain `API_ID` and `API_HASH` from Telegram.
4. Generate a Pyrogram user `STRING_SESSION`.
5. Copy `.env.example` to `.env` and fill it.
6. `pip install -r requirements.txt`
7. Run `python main.py`.

## Commands
- `/play <song>` queues a song; `/playforce <song>` is restricted to group admins and users authorized with `/auth`.
- `/seek 30s`, `/seek 30m`, or `/seek 1h` seeks the current song.
- Reply to a song message with `/addpl <name>`, then use `/playlist`, `/playpl <name>`, and `/delpl <name> <number>`.
- `/import <YouTube or Spotify playlist URL> [name]` imports a playlist. Spotify imports require `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env`.

The assistant user should be added to the target group and have permission to join/use the voice chat.

## Docker
`docker compose up --build`

## Future extension points
- Spotify/search providers
- YouTube search provider
- Lyrics provider
- Web dashboard
- Redis queue
- Mongo/PostgreSQL
- Announcement queues
- Multi-bot architecture
- Custom external APIs
