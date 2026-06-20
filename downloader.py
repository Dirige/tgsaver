"""Pyrogram downloader - user client, no 20MB limit"""

import os
import logging
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message
import config

logger = logging.getLogger(__name__)

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not config.TG_SESSION_STRING:
            raise RuntimeError("TG_SESSION_STRING not set. Run login.py first.")
        proxy = {
            "scheme": config.PROXY_SCHEME,
            "hostname": config.PROXY_HOST,
            "port": config.PROXY_PORT,
        }
        _client = Client(
            name="tg_saver",
            api_id=config.TG_API_ID,
            api_hash=config.TG_API_HASH,
            session_string=config.TG_SESSION_STRING,
            proxy=proxy,
            no_updates=True,
        )
    return _client


async def connect():
    """Connect the Pyrogram client."""
    c = get_client()
    if not c.is_connected:
        await c.start()
    me = await c.get_me()
    logger.info(f"Pyrogram connected as {me.first_name} (id={me.id})")


async def download_media(chat_id: int, message_id: int, save_path: str, progress_callback=None):
    """Download a message's media to save_path."""
    c = get_client()
    msg: Message = await c.get_messages(chat_id, message_id)
    if msg is None or msg.media is None:
        raise ValueError(f"Message {message_id} not found or has no media")
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    return await c.download_media(
        msg,
        file_name=save_path,
        progress=progress_callback,
    )
