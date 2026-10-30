"""Small per-chat FIFO queues for local audio files."""
from asyncio import Queue, QueueEmpty
from typing import Dict, Optional

_queues: Dict[int, Queue] = {}

async def put(chat_id: int, **kwargs) -> int:
    queue = _queues.setdefault(int(chat_id), Queue())
    await queue.put(dict(kwargs))
    return queue.qsize()

def get(chat_id: int) -> Optional[dict]:
    queue = _queues.get(int(chat_id))
    if queue is None:
        return None
    try:
        item = queue.get_nowait()
        queue.task_done()
        return item
    except QueueEmpty:
        return None

def is_empty(chat_id: int) -> bool:
    queue = _queues.get(int(chat_id))
    return queue is None or queue.empty()

def task_done(chat_id: int):
    # Kept for compatibility with older handlers; queue.get() accounts for tasks.
    return None

def clear(chat_id: int):
    queue = _queues.get(int(chat_id))
    if queue is not None:
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except QueueEmpty:
                break

def reset(chat_id: int):
    clear(chat_id)
    _queues.pop(int(chat_id), None)
