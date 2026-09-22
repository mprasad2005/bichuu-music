from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from core.queue import QueueManager, Track
from database.db import add_stat, get_settings
from services.source import search_and_download

class Player:
    def __init__(self, calls: PyTgCalls):
        self.calls = calls
        self.queues = QueueManager()

    async def enqueue(self, chat_id, query, requester_id, requester_name="Unknown"):
        data = await search_and_download(query)
        track = Track(
            title=data["title"],
            url=data["url"],
            duration=data["duration"],
            requester_id=requester_id,
            requester_name=requester_name,
            thumbnail=data.get("thumbnail"),
            local_file=data["file"],
        )
        self.queues.add(chat_id, track)
        return track

    async def play_next(self, chat_id):
        track = self.queues.pop(chat_id)
        if not track:
            self.queues.remove_current(chat_id)
            return None

        self.queues.set_current(chat_id, track)
        await self.calls.play(
            chat_id,
            MediaStream(
                track.local_file,
                video_flags=MediaStream.Flags.IGNORE,
            ),
        )
        add_stat(chat_id, "plays")
        return track

    async def on_stream_end(self, chat_id):
        if not self.queues.get_current(chat_id):
            return None
        self.queues.remove_current(chat_id)
        return await self.play_next(chat_id)

    async def seek(self, chat_id, seconds):
        track = self.queues.get_current(chat_id)
        if not track or not track.local_file:
            return None
        await self.calls.play(
            chat_id,
            MediaStream(
                track.local_file,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=f"-ss {int(seconds)}",
            ),
        )
        return track

    async def stop(self, chat_id):
        await self.calls.leave_call(chat_id)
        self.queues.clear(chat_id)
        self.queues.remove_current(chat_id)

    async def skip(self, chat_id):
        add_stat(chat_id, "skips")
        self.queues.remove_current(chat_id)
        return await self.play_next(chat_id)

    def queue_text(self, chat_id):
        items = self.queues.peek_all(chat_id)
        current = self.queues.get_current(chat_id)
        lines = []
        if current:
            lines.append(f"▶️ {current.title}")
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item.title}")
        return "\n".join(lines) if lines else "Queue is empty."
