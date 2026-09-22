import asyncio
import logging

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client
from pyrogram import errors as pyrogram_errors
from pyrogram import utils as pyrogram_utils

pyrogram_utils.MIN_CHANNEL_ID = -10**18

if not hasattr(pyrogram_errors, "GroupcallForbidden"):
    pyrogram_errors.GroupcallForbidden = pyrogram_errors.GroupCallInvalid
if not hasattr(pyrogram_errors, "GroupcallInvalid"):
    pyrogram_errors.GroupcallInvalid = pyrogram_errors.GroupCallInvalid

from pytgcalls import PyTgCalls
from pytgcalls import filters as call_filters
from pytgcalls.types import StreamEnded

from config import BOT_TOKEN, API_ID, API_HASH, STRING_SESSION, LOG_LEVEL
from database.db import init_db
from core.player import Player
from handlers import start, music, admin, playlists, callbacks

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

assistant = Client(
    "music_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    no_updates=True,
)

calls = PyTgCalls(assistant)
player = Player(calls)

init_db()

start.register(bot)
music.register(bot, player)
admin.register(bot, player)
playlists.register(bot, player)
callbacks.register(bot, player)


@calls.on_update(call_filters.stream_end(StreamEnded.Type.AUDIO))
async def on_stream_end(_, update):
    state = music.progress_states.get(update.chat_id, {})
    reply_to_message_id = state.get("reply_to_message_id")
    track = await player.on_stream_end(update.chat_id)
    if track:
        await music.send_now_playing_to_chat(
            bot,
            update.chat_id,
            track,
            reply_to_message_id,
        )

if __name__ == "__main__":
    # PyTgCalls handles the voice-call client; Pyrogram bot handles commands/UI.
    calls.start()
    bot.run()
