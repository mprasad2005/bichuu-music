from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class Track:
    title: str
    url: str
    duration: int = 0
    requester_id: int = 0
    requester_name: str = "Unknown"
    thumbnail: str | None = None
    local_file: str | None = None

class QueueManager:
    def __init__(self):
        self.queues = defaultdict(deque)
        self.current = {}

    def add(self, chat_id, track):
        self.queues[chat_id].append(track)

    def pop(self, chat_id):
        return self.queues[chat_id].popleft() if self.queues[chat_id] else None

    def promote(self, chat_id, position):
        items = self.queues[chat_id]
        if position < 1 or position > len(items):
            return None
        items.rotate(-(position - 1))
        track = items.popleft()
        items.rotate(position - 1)
        items.appendleft(track)
        return track

    def clear(self, chat_id):
        self.queues[chat_id].clear()

    def peek_all(self, chat_id):
        return list(self.queues[chat_id])

    def set_current(self, chat_id, track):
        self.current[chat_id] = track

    def get_current(self, chat_id):
        return self.current.get(chat_id)

    def remove_current(self, chat_id):
        return self.current.pop(chat_id, None)
