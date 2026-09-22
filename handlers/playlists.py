from pyrogram import filters

from database.db import add_playlist, list_playlist, list_playlist_names, remove_playlist
from services.source import import_playlist


def register(app, player):
    @app.on_message(filters.command("addpl"))
    async def addpl(_, message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /addpl <song name or URL>")
        value = message.text.split(None, 1)[1].strip()
        if message.reply_to_message:
            track = player.queues.get_current(message.chat.id)
            if not track:
                return await message.reply_text("Nothing is currently playing.")
            name = value
            query = track.url
            title = track.title
        else:
            name = "favorites"
            query = value
            title = value
        if not add_playlist(message.chat.id, message.from_user.id, name, query):
            return await message.reply_text("This song is already in your playlist.")
        await message.reply_text(f"Added {title} to {name}.")

    @app.on_message(filters.command("delpl"))
    async def delpl(_, message):
        if len(message.command) < 3 or not message.command[2].isdigit():
            return await message.reply_text("Usage: /delpl <playlist_name> <song_number>")
        name = message.command[1]
        index = int(message.command[2]) - 1
        items = list_playlist(message.chat.id, message.from_user.id, name)
        if index < 0 or index >= len(items):
            return await message.reply_text("That song number does not exist.")
        remove_playlist(message.chat.id, message.from_user.id, name, items[index])
        await message.reply_text("Removed from playlist.")

    @app.on_message(filters.command("playlist"))
    async def playlist(_, message):
        args = message.command[1:]
        user_id = message.from_user.id
        if not args:
            names = list_playlist_names(message.chat.id, user_id)
            return await message.reply_text(
                "Your playlists:\n" + "\n".join(f"- {name}" for name in names)
                if names else "You have no playlists yet."
            )
        name = args[0]
        items = list_playlist(message.chat.id, user_id, name)
        if not items:
            return await message.reply_text("Playlist is empty or does not exist.")
        await message.reply_text(
            f"{name}\n" + "\n".join(f"{i}. {query}" for i, query in enumerate(items, 1))
        )

    @app.on_message(filters.command("playpl"))
    async def playpl(_, message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /playpl <playlist_name>")
        name = message.command[1]
        items = list_playlist(message.chat.id, message.from_user.id, name)
        if not items:
            return await message.reply_text("Playlist is empty or does not exist.")
        for query in items:
            await player.enqueue(message.chat.id, query, message.from_user.id)
        if not player.queues.get_current(message.chat.id):
            await player.play_next(message.chat.id)
        await message.reply_text(f"Loaded {len(items)} songs from {name}.")

    @app.on_message(filters.command("import"))
    async def import_command(_, message):
        if len(message.command) < 2:
            return await message.reply_text("Usage: /import <YouTube playlist URL> [playlist_name]")
        url = message.command[1]
        name = " ".join(message.command[2:]).strip() or "imported"
        try:
            entries = await import_playlist(url)
            for entry in entries:
                add_playlist(message.chat.id, message.from_user.id, name, entry["query"])
            await message.reply_text(f"Imported {len(entries)} songs into {name}.")
        except Exception as exc:
            await message.reply_text(f"Import failed: {exc}", parse_mode=None)
