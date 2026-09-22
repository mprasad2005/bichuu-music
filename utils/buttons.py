from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def queue_buttons(position):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶ Play Now", callback_data=f"music:playnow:{position}")],
    ])

def player_buttons(elapsed=0, duration=0, paused=False):
    duration = max(int(duration or 0), 1)
    elapsed = min(max(int(elapsed), 0), duration)
    filled = round(12 * elapsed / duration)
    timeline = f"{'⏸' if paused else '▶'} {elapsed // 60}:{elapsed % 60:02d} {'━' * filled}{'─' * (12 - filled)} {duration // 60}:{duration % 60:02d}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(timeline, callback_data="music:progress")],
        [
            InlineKeyboardButton("▶", callback_data="music:resume"),
            InlineKeyboardButton("⏸", callback_data="music:pause"),
            InlineKeyboardButton("⏭", callback_data="music:skip"),
        ],
        [
            InlineKeyboardButton("⏹ End", callback_data="music:stop"),
            InlineKeyboardButton("♡", callback_data="music:addpl"),
            InlineKeyboardButton("☷ Queue", callback_data="music:queue"),
        ],
    ])
