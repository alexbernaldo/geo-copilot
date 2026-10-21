"""EventBus en memoria: suscriptores por proyecto y formato SSE (ver contracts/events.md)."""

from __future__ import annotations

import json
import queue
import threading
import time
from typing import Any

PING_SECONDS = 15.0
COUNTER_MIN_INTERVAL = 0.25  # máx. 4 por segundo
COST_MIN_INTERVAL = 1.0      # máx. 1 por segundo


def sse_message(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[queue.Queue]] = {}
        self._lock = threading.Lock()
        self._last: dict[tuple[str, str], float] = {}
        self._pending: dict[tuple[str, str], dict[str, Any]] = {}

    def subscribe(self, pid: str) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=2000)
        with self._lock:
            self._subs.setdefault(pid, []).append(q)
        return q

    def unsubscribe(self, pid: str, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subs.get(pid, []):
                self._subs[pid].remove(q)

    def publish(self, pid: str, event: str, data: dict[str, Any]) -> None:
        with self._lock:
            subs = list(self._subs.get(pid, []))
        for q in subs:
            try:
                q.put_nowait((event, data))
            except queue.Full:  # un cliente lento no bloquea el trabajo
                pass

    def publish_limited(self, pid: str, event: str, data: dict[str, Any]) -> None:
        """Publica respetando la frecuencia máxima de `counter` y `cost`; el último valor se conserva para `flush`."""
        interval = COUNTER_MIN_INTERVAL if event == "counter" else COST_MIN_INTERVAL
        key = (pid, event)
        now = time.monotonic()
        with self._lock:
            if now - self._last.get(key, 0.0) < interval:
                self._pending[key] = data
                return
            self._last[key] = now
            self._pending.pop(key, None)
        self.publish(pid, event, data)

    def flush(self, pid: str) -> None:
        """Emite los últimos `counter`/`cost` retenidos (al terminar un paso o el trabajo)."""
        for event in ("counter", "cost"):
            with self._lock:
                data = self._pending.pop((pid, event), None)
                self._last[(pid, event)] = time.monotonic()
            if data is not None:
                self.publish(pid, event, data)
