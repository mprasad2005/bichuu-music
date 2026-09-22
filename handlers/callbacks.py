from pyrogram import filters
from database.db import add_playlist
from handlers.music import progress_states, send_now_playing, set_paused, stop_progress

def register(app, player):
    @app.on_callback_query(filters.regex(r"^music:"))
    async def controls(_, query):
        action = query.data.split(":", 1)[1]
        chat_id = query.message.chat.id
        try:
            if action == "pause":
                await player.calls.pause(chat_id)
                set_paused(chat_id, True)
                text = "⏸ Paused."
            elif action == "resume":
                await player.calls.resume(chat_id)
                set_paused(chat_id, False)
                text = "▶️ Resumed."
            elif action == "skip":
                track = await player.skip(chat_id)
                if track:
                    await query.answer()
                    return await send_now_playing(query.message, track)
                text = "Queue finished."
            elif action.startswith("playnow:"):
                position = int(action.split(":", 1)[1])
                if not player.queues.promote(chat_id, position):
                    return await query.answer("This queue item is no longer available.", show_alert=True)
                track = await player.skip(chat_id) if player.queues.get_current(chat_id) else await player.play_next(chat_id)
                await query.answer("Playing now")
                return await send_now_playing(query.message, track)
            elif action == "stop":
                await player.stop(chat_id)
                stop_progress(chat_id)
                progress_states.pop(chat_id, None)
                text = "⏹ Stopped."
            elif action == "queue":
                text = player.queue_text(chat_id)
            elif action == "progress":
                state = progress_states.get(chat_id)
                if not state:
                    return await query.answer("Nothing is currently playing.", show_alert=True)
                elapsed = int(state["elapsed"])
                if not state["paused"]:
                    import time
                    elapsed += int(time.monotonic() - state["started_at"])
                return await query.answer(
                    f"{elapsed // 60}:{elapsed % 60:02d} / {state['track'].duration // 60}:{state['track'].duration % 60:02d}"
                )
            elif action == "addpl":
                track = player.queues.get_current(chat_id)
                if not track:
                    return await query.answer("Nothing is currently playing.", show_alert=True)
                added = add_playlist(
                    chat_id,
                    query.from_user.id,
                    "favorites",
                    track.url,
                )
                if not added:
                    return await query.answer(
                        "This song is already in your favorites playlist.",
                        show_alert=True,
                    )
                return await query.answer("Song added to your favorites playlist.")
            else:
                text = "Unknown action."
            await query.answer()
            await query.message.reply_text(text)
        except Exception as e:
            await query.answer("Action failed", show_alert=True)
