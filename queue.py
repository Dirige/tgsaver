"""Download queue - serial downloads to protect NAS"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    message_id: int
    chat_id: int
    file_name: str
    save_path: str
    status: str = "pending"  # pending / downloading / done / failed
    progress: float = 0.0
    error: Optional[str] = None
    done_event: asyncio.Event = field(default_factory=asyncio.Event)


class DownloadQueue:
    def __init__(self, max_concurrent: int = 2):
        self._queue: asyncio.Queue[DownloadTask] = asyncio.Queue()
        self._active: dict[int, DownloadTask] = {}
        self._max = max_concurrent
        self._workers: list[asyncio.Task] = []

    def start(self, download_fn: Callable):
        """Start worker tasks."""
        for i in range(self._max):
            task = asyncio.create_task(self._worker(i, download_fn))
            self._workers.append(task)

    async def _worker(self, worker_id: int, download_fn: Callable):
        while True:
            task = await self._queue.get()
            self._active[task.message_id] = task
            task.status = "downloading"
            logger.info(f"Worker {worker_id}: downloading {task.file_name}")
            try:
                await download_fn(task)
                task.status = "done"
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                logger.error(f"Worker {worker_id}: failed {task.file_name}: {e}")
            finally:
                task.done_event.set()
                self._active.pop(task.message_id, None)
                self._queue.task_done()

    async def submit(self, task: DownloadTask) -> DownloadTask:
        """Add task to queue and return it (await task.done_event to wait)."""
        await self._queue.put(task)
        logger.info(f"Queued: {task.file_name} (position: {self._queue.qsize()})")
        return task

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def active_tasks(self) -> list[DownloadTask]:
        return list(self._active.values())
