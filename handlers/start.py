from pyrogram import filters

def register(app):
    @app.on_message(filters.command("start"))
    async def start(_, message):
        await message.reply_text(
            "Music Bot\n\n"
            "Use /play <song> to start music.\n"
            "/playforce /seek /queue /pause /resume /skip /stop /nowplaying\n\n"
            "Admin: /auth, /unauth\n"
            "Playlists: /addpl <song name or URL>, reply with /addpl <playlist name> for a custom list, /playlist, /playpl <name>, /delpl <name> <number>, /import <playlist URL>",
            parse_mode=None,
        )
