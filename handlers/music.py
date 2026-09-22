import asyncio
import logging
import re
import time

from pyrogram import filters
from utils.buttons import player_buttons, queue_buttons
from database.db import is_authorized
from handlers.admin import is_admin

logger = logging.getLogger(__name__)
progress_tasks = {}
progress_states = {}

def format_duration(seconds):
    minutes, seconds = divmod(int(seconds or 0), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"

def progress_text(elapsed, duration):
    duration = max(int(duration or 0), 1)
    elapsed = min(max(int(elapsed), 0), duration)
    filled = round(16 * elapsed / duration)
    return f"{format_duration(elapsed)} |{'━' * filled}{'─' * (16 - filled)}| -{format_duration(duration - elapsed)}"

def now_playing_text(track, elapsed=0, paused=False):
    state = "⏸ Paused" if paused else "🎵 Started streaming"
    return (
        f"{state}\n\n"
        f"▶ Title: {track.title}\n"
        f"⏱ Duration: {format_duration(track.duration)}\n"
        f"👤 Requested by: {track.requester_name}"
    )

def queued_text(track, position):
    return (
        f"⏳ Added to queue: {position}\n\n"
        f"▶ Title: {track.title}\n"
        f"⏱ Duration: {format_duration(track.duration)}\n"
        f"👤 Requested by: {track.requester_name}"
    )

def stop_progress(chat_id):
    task = progress_tasks.pop(chat_id, None)
    if task:
        task.cancel()

def current_elapsed(chat_id):
    state = progress_states.get(chat_id)
    if not state:
        return 0
    if state["paused"]:
        return state["elapsed"]
    return state["elapsed"] + time.monotonic() - state["started_at"]

def set_paused(chat_id, paused):
    state = progress_states.get(chat_id)
    if not state:
        return
    if paused and not state["paused"]:
        state["elapsed"] = current_elapsed(chat_id)
        state["paused"] = True
    elif not paused and state["paused"]:
        state["started_at"] = time.monotonic()
        state["paused"] = False

async def update_progress(chat_id, sent_message, track):
    try:
        while progress_states.get(chat_id, {}).get("track") is track:
            state = progress_states[chat_id]
            elapsed = current_elapsed(chat_id)
            text = now_playing_text(track, elapsed, state["paused"])
            if sent_message.photo:
                await sent_message.edit_caption(
                    text,
                    reply_markup=player_buttons(elapsed, track.duration, state["paused"]),
                )
            else:
                await sent_message.edit_text(
                    text,
                    reply_markup=player_buttons(elapsed, track.duration, state["paused"]),
                )
            if track.duration and elapsed >= track.duration:
                return
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Could not update playback progress for chat %s", chat_id)

async def send_now_playing(message, track, status=None):
    chat_id = message.chat.id
    stop_progress(chat_id)
    progress_states[chat_id] = {
        "track": track,
        "reply_to_message_id": message.id,
        "elapsed": 0,
        "started_at": time.monotonic(),
        "paused": False,
    }
    caption = now_playing_text(track)
    if status:
        await status.delete()
    if track.thumbnail:
        try:
            sent_message = await message.reply_photo(
                track.thumbnail,
                caption=caption,
                reply_markup=player_buttons(),
            )
        except Exception:
            logger.exception("Could not send track thumbnail for %r", track.title)
            sent_message = await message.reply_text(caption, reply_markup=player_buttons())
    else:
        sent_message = await message.reply_text(caption, reply_markup=player_buttons())
    start_progress(chat_id, sent_message, track)
    return sent_message

def start_progress(chat_id, sent_message, track):
    progress_tasks[chat_id] = asyncio.create_task(
        update_progress(chat_id, sent_message, track)
    )

async def send_now_playing_to_chat(app, chat_id, track, reply_to_message_id=None):
    stop_progress(chat_id)
    progress_states[chat_id] = {
        "track": track,
        "reply_to_message_id": reply_to_message_id,
        "elapsed": 0,
        "started_at": time.monotonic(),
        "paused": False,
    }
    caption = now_playing_text(track)
    if track.thumbnail:
        try:
            sent_message = await app.send_photo(
                chat_id,
                track.thumbnail,
                caption=caption,
                reply_markup=player_buttons(),
                reply_to_message_id=reply_to_message_id,
            )
        except Exception:
            logger.exception("Could not send track thumbnail for %r", track.title)
            sent_message = await app.send_message(
                chat_id,
                caption,
                reply_markup=player_buttons(),
                reply_to_message_id=reply_to_message_id,
            )
    else:
        sent_message = await app.send_message(
            chat_id,
            caption,
            reply_markup=player_buttons(),
            reply_to_message_id=reply_to_message_id,
        )
    start_progress(chat_id, sent_message, track)
    return sent_message

def register(app, player):
    @app.on_message(filters.command("play"))
    async def play(_, message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: `/play <song name or URL>`")
        query = message.text.split(None, 1)[1]
        status = await message.reply_text("🔎 Searching and preparing audio...")
        try:
            track = await player.enqueue(
                message.chat.id,
                query,
                message.from_user.id,
                message.from_user.first_name,
            )
            if not player.queues.get_current(message.chat.id):
                await player.play_next(message.chat.id)
                await send_now_playing(message, track, status)
            else:
                position = len(player.queues.peek_all(message.chat.id))
                await status.delete()
                await message.reply_text(
                    queued_text(track, position),
                    reply_markup=queue_buttons(position),
                    parse_mode=None,
                )
        except Exception as e:
            logger.exception("Could not play query %r", query)
            await status.edit_text(
                f"Could not play this track.\n{type(e).__name__}: {e}",
                parse_mode=None,
            )

    @app.on_message(filters.command("playforce"))
    async def playforce(_, message):
        allowed = await is_admin(app, message) or is_authorized(
            message.chat.id, message.from_user.id
        )
        if not allowed:
            return await message.reply_text("Only group admins and authorized users can use /playforce.")
        if len(message.command) < 2:
            return await message.reply_text("Usage: /playforce <song name or URL>")
        query = message.text.split(None, 1)[1]
        try:
            track = await player.enqueue(
                message.chat.id,
                query,
                message.from_user.id,
                message.from_user.first_name,
            )
            if not player.queues.get_current(message.chat.id):
                await player.play_next(message.chat.id)
                await send_now_playing(message, track)
            else:
                position = len(player.queues.peek_all(message.chat.id))
                await message.reply_text(
                    queued_text(track, position),
                    reply_markup=queue_buttons(position),
                    parse_mode=None,
                )
        except Exception as e:
            logger.exception("Could not force play query %r", query)
            await message.reply_text(f"Could not play this track: {type(e).__name__}: {e}", parse_mode=None)

    @app.on_message(filters.command("seek"))
    async def seek(_, message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /seek 30s, /seek 30m, or /seek 1h")
        match = re.fullmatch(r"(\d+)([smh]?)", message.command[1].lower())
        if not match:
            return await message.reply_text("Use a duration such as 30s, 30m, or 1h.")
        value = int(match.group(1))
        multiplier = {"": 1, "s": 1, "m": 60, "h": 3600}[match.group(2)]
        track = await player.seek(message.chat.id, value * multiplier)
        await message.reply_text(
            f"Seeked to {value}{match.group(2) or 's'} in {track.title}."
            if track else "Nothing is currently playing."
        )

    @app.on_message(filters.command("pause"))
    async def pause(_, message):
        await player.calls.pause(message.chat.id)
        set_paused(message.chat.id, True)
        await message.reply_text("⏸ Paused.")

    @app.on_message(filters.command("resume"))
    async def resume(_, message):
        await player.calls.resume(message.chat.id)
        set_paused(message.chat.id, False)
        await message.reply_text("▶️ Resumed.")

    @app.on_message(filters.command("skip"))
    async def skip(_, message):
        track = await player.skip(message.chat.id)
        if not track:
            stop_progress(message.chat.id)
            progress_states.pop(message.chat.id, None)
            return await message.reply_text("Queue finished.")
        await send_now_playing(message, track)

    @app.on_message(filters.command("stop"))
    async def stop(_, message):
        await player.stop(message.chat.id)
        stop_progress(message.chat.id)
        progress_states.pop(message.chat.id, None)
        await message.reply_text("⏹ Stopped and cleared the queue.")

    @app.on_message(filters.command("leave"))
    async def leave(_, message):
        await player.stop(message.chat.id)
        stop_progress(message.chat.id)
        progress_states.pop(message.chat.id, None)
        await message.reply_text("👋 Left the voice chat.")

    @app.on_message(filters.command("end"))
    async def end(_, message):
        await player.stop(message.chat.id)
        stop_progress(message.chat.id)
        progress_states.pop(message.chat.id, None)
        await message.reply_text("⏹ Playback ended and the queue was cleared.")

    @app.on_message(filters.command("queue"))
    async def queue(_, message):
        await message.reply_text("📋 **Queue**\n\n" + player.queue_text(message.chat.id))

    @app.on_message(filters.command("nowplaying"))
    async def nowplaying(_, message):
        track = player.queues.get_current(message.chat.id)
        if not track:
            return await message.reply_text("Nothing is currently playing.")
        await send_now_playing(message, track)

    @app.on_message(filters.command("volume"))
    async def volume(_, message):
        await message.reply_text(
            "Volume control is wired as an extension point; add the exact PyTgCalls "
            "volume method supported by the installed release before enabling it."
        )
