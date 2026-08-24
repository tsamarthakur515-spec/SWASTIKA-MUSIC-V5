import aiofiles
import aiohttp
import asyncio
import os
import random
import re
import shutil
import subprocess
import time
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from pyrogram import filters
from pyrogram.enums import ParseMode

from youtubesearchpython.__future__ import VideosSearch

from .. import bot, call, cdz, console
from ..modules.formatters import panel_caption, queue_caption, smallcaps
from ..modules.custom_emojis import tg_emoji, E
from ..modules.helpers import AssistantErr
from .maintenance import block_if_maintenance

CACHE_DIR = "cache"
FONT_PATH = "PANDAMUSIC/resource/font.ttf"
FALLBACK_THUMB = "PANDAMUSIC/resource/thumbnail.png"

POWERED_LINE_1 = "POWERED BY : SWASTIKA MUSIC"
POWERED_LINE_2 = "YT MUSIC API: ARU YT API"

ADMIN_REQUIRED_MSG = (
    "ᴌᴀᴋᴇ ʙᴏᴛ ᴀɴᴅ ᴀssɪsᴛᴀɴᴛ ᴀᴅᴌɪɴ ғɪʀsᴛ\n"
    "ᴡɪᴛʜ ᴀʟʟ ᴘᴇʀᴌɪssɪᴏɴs ᴛʜᴇɴ ᴘʟᴀʏ\n\n"
    "• Manage Video Chats\n"
    "• Invite Users via Link\n"
    "• Delete Messages (optional)"
)


def _is_remote_path(path: str) -> bool:
    return str(path or "").startswith(("http://", "https://"))


async def _status(aux, text: str, emoji_id: str = None):
    eid = emoji_id or E.LOADER
    body = f"{tg_emoji(eid, '🌀')} {smallcaps(text)}"
    try:
        await aux.edit(body, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            await aux.edit(text)
        except Exception:
            pass


def parse_query(query: str) -> str:
    if bool(
        re.match(
            r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/|live/)?([A-Za-z0-9_-]{11})(?:[?&].*)?$",
            query,
        )
    ):
        match = re.search(
            r"(?:v=|/(?:embed|v|shorts|live)/|youtu\.be/)([A-Za-z0-9_-]{11})", query
        )
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    return query


def parse_tg_link(link: str):
    parsed = urlparse(link)
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2:
        return str(parts[0]), int(parts[1])
    return None, None


async def fetch_song(query: str):
    try:
        search = VideosSearch(query, limit=1)
        result = (await search.next()).get("result", [])
        if not result:
            return {"error": "No video found"}
        vidid = result[0].get("id")
        if not vidid:
            return {"error": "Failed to get video ID"}
        url = "http://46.250.243.52:1470/song"
        params = {"query": vidid}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except Exception:
                        return {"error": "Invalid JSON response"}
                return {"error": f"API returned status {response.status}"}
    except Exception as e:
        return {"error": str(e)}


def convert_to_seconds(duration: str) -> int:
    try:
        parts = list(map(int, str(duration).split(":")))
        total = 0
        multiplier = 1
        for value in reversed(parts):
            total += value * multiplier
            multiplier *= 60
        return total
    except Exception:
        return 0


def seconds_to_hhmmss(seconds):
    seconds = max(0, int(seconds or 0))
    if seconds < 3600:
        minutes = seconds // 60
        sec = seconds % 60
        return f"{minutes}:{sec:02d}"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60
    return f"{hours}:{minutes:02d}:{sec:02d}"


def file_has_video(path: str, retries: int = 2, delay: float = 0.2) -> bool:
    if _is_remote_path(path):
        return True
    if shutil.which("ffprobe") is None:
        print("[ffprobe video check] ffprobe binary not found on PATH", flush=True)
        return False
    last_err = None
    for attempt in range(retries):
        try:
            out = subprocess.check_output(
                [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=codec_type", "-of", "csv=p=0",  path,
                ],
                stderr=subprocess.DEVNULL, timeout=12,
            )
            if b"video" in out.lower():
                return True
            last_err = "no video stream reported"
        except Exception as e:
            last_err = e
        if attempt < retries - 1:
            time.sleep(delay)
    print(f"[ffprobe video check] failed after {retries} attempt(s): {last_err}", flush=True)
    return False
