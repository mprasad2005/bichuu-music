from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from database.db import authorize_user, unauthorize_user

async def is_admin(client, message):
    if not message.from_user:
        return False
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)

def target_user_id(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1 and message.command[1].isdigit():
        return int(message.command[1])
    return None

def register(app, player):
    @app.on_message(filters.command("musicadmins"))
    async def musicadmins(_, message):
        if not await is_admin(app, message):
            return await message.reply_text("Admins only.")
        await message.reply_text(
            "Admin mode can be enabled through the database/settings layer."
        )

    @app.on_message(filters.command("auth"))
    async def auth(_, message):
        if not await is_admin(app, message):
            return await message.reply_text("Admins only.")
        user_id = target_user_id(message)
        if not user_id:
            return await message.reply_text("Reply to a user or use /auth <user_id>.")
        authorize_user(message.chat.id, user_id)
        await message.reply_text(f"User {user_id} is authorized to use /playforce.")

    @app.on_message(filters.command("unauth"))
    async def unauth(_, message):
        if not await is_admin(app, message):
            return await message.reply_text("Admins only.")
        user_id = target_user_id(message)
        if not user_id:
            return await message.reply_text("Reply to a user or use /unauth <user_id>.")
        unauthorize_user(message.chat.id, user_id)
        await message.reply_text(f"User {user_id} is no longer authorized.")

    @app.on_message(filters.command("stats"))
    async def stats(_, message):
        from database.db import get_stats
        s = get_stats(message.chat.id)
        await message.reply_text(f"📊 Plays: {s['plays']}\n⏭ Skips: {s['skips']}")
