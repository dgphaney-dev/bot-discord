import asyncio
import datetime
import json
from typing import Set

class ConsoleStream:
    """Gerencia conexões WebSocket para streaming em tempo real do console para a Dashboard."""
    _instance = None
    _subscribers: Set[asyncio.Queue] = set()
    _history = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConsoleStream, cls).__new__(cls)
            cls._subscribers = set()
            cls._history = []
        return cls._instance

    @classmethod
    def log(cls, tag: str, message: str, level: str = "INFO"):
        """Registra e transmite uma linha de log para os consoles conectados."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": now,
            "tag": tag.upper(),
            "message": message,
            "level": level.upper()
        }
        cls._history.append(entry)
        if len(cls._history) > 100:
            cls._history.pop(0)

        # Notifica todos os WebSockets conectados
        for queue in list(cls._subscribers):
            try:
                queue.put_nowait(entry)
            except Exception:
                pass

    @classmethod
    def get_history(cls):
        return list(cls._history)

    @classmethod
    def subscribe(cls) -> asyncio.Queue:
        q = asyncio.Queue()
        cls._subscribers.add(q)
        return q

    @classmethod
    def unsubscribe(cls, q: asyncio.Queue):
        cls._subscribers.discard(q)
