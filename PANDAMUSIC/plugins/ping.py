# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# Image always attaches · each line separate quote
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import asyncio
import io
import platform
import time
from typing import Optional, Tuple, Union

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, call, console, cdx
from ..modules.custom_emojis import tg_emoji, CE_CLOSE
from ..modules.formatters import smallcaps

try:
    from pyrogram.enums import ButtonStyle

    _SUCCESS = ButtonStyle.SUCCESS
    _PRIMARY = ButtonStyle.PRIMARY
    _DANGER = ButtonStyle.DANGER
except Exception:
    _SUCCESS = "success"
    _PRIMARY = "primary"
    _DANGER = "danger"

try:
    import psutil
except Exception:
    psutil = None

try:
    import pyrogram as _pyrogram
except Exception:
    _pyrogram = None

try:
    import aiohttp
except Exception:
    aiohttp = None

CE_PING = "6111504695728020416"
PING_IMAGE = "https://files.catbox.moe/wfqfeh.jpg"
_VERSION = "v5.0.0"

_PHOTO_BYTES: Optional[bytes] = None


def em(fallback: str = "⚡") -> str:
    return tg_emoji(CE_PING, fallback)


def q(line: str) -> str:
    """One line = one quote block."""
    return f"<blockquote>{line}</blockquote>"


def _boot_ts() -> float:
    return float(getattr(console, "_boot_", None) or time.time())


def _get_uptime() -> str:
    elapsed = max(0, int(time.time() - _boot_ts()))
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _latency_label(ms: int) -> str:
    if ms <= 0:
        return "N/A"
    if ms < 80:
        return "🟢 Excellent"
    if ms < 150:
        return "🟡 Good"
    if ms < 300:
        return "🟠 Average"
    return "🔴 Slow"


def _btn(text, style=None, emoji_id=None, **kwargs):
    if emoji_id:
        kwargs["icon_custom_emoji_id"] = str(emoji_id)
    if style is not None:
        try:
            return InlineKeyboardButton(text, style=style, **kwargs)
        except TypeError:
            pass
        try:
            return InlineKeyboardButton(
                text, style=str(getattr(style, "name", style)).lower(), **kwargs
            )
        except TypeError:
            pass
    try:
        return InlineKeyboardButton(text, **kwargs)
    except TypeError:
        kwargs.pop("icon_custom_emoji_id", None)
        return InlineKeyboardButton(text, **kwargs)


def _owner_url() -> str:
    owner = (getattr(console, "OWNER_USERNAME", None) or "").lstrip("@")
    if owner:
        return f"https://t.me/{owner}"
    oid = getattr(console, "OWNER_ID", 0) or 0
    if oid:
        return f"tg://user?id={oid}"
    return "https://t.me/tsamarthakur515"


def _support_url() -> Optional[str]:
    chat = (getattr(console, "SUPPORT_CHAT", None) or "").lstrip("@")
    if not chat:
        return None
    if chat.startswith("http"):
        return chat
    if chat.startswith("+"):
        return f"https://t.me/{chat}"
    return f"https://t.me/{chat}"


def _channel_url() -> Optional[str]:
    ch = (getattr(console, "SUPPORT_CHANNEL", None) or "").lstrip("@")
    if not ch:
        return None
    if ch.startswith("http"):
        return ch
    return f"https://t.me/{ch}"


def _ping_keyboard() -> InlineKeyboardMarkup:
    row1 = [
        _btn(smallcaps("owner"), style=_SUCCESS, emoji_id=CE_PING, url=_owner_url())
    ]
    support = _support_url()
    if support:
        row1.append(
            _btn(smallcaps("support"), style=_PRIMARY, emoji_id=CE_PING, url=support)
        )
    rows = [row1]
    channel = _channel_url()
    row2 = []
    if channel:
        row2.append(
            _btn(smallcaps("updates"), style=_PRIMARY, emoji_id=CE_PING, url=channel)
        )
    row2.append(
        _btn(smallcaps("close"), style=_DANGER, emoji_id=CE_CLOSE, callback_data="close")
    )
    rows.append(row2)
    return InlineKeyboardMarkup(rows)


async def _get_latency(client) -> int:
    try:
        t0 = time.perf_counter()
        await asyncio.wait_for(client.get_me(), timeout=1.5)
        return int(round((time.perf_counter() - t0) * 1000))
    except Exception as e:
        print(f"[ping] latency skip: {e}", flush=True)
        return 0


async def _db_status() -> str:
    try:
        from ..modules.database import _ok, _pool

        if not _ok() or _pool is None:
            return "⚪ Offline (Memory Mode)"
        async with _pool.acquire() as conn:
            await asyncio.wait_for(conn.fetchval("SELECT 1"), timeout=1.0)
        return "🟢 Connected"
    except Exception:
        return "🔴 Error"


async def _served_counts() -> Tuple[int, int]:
    try:
        from ..modules.database import count_served_users, count_served_chats

        users, chats = await asyncio.gather(
            count_served_users(), count_served_chats()
        )
        return int(users or 0), int(chats or 0)
    except Exception:
        return 0, 0


def _active_vc_count() -> int:
    try:
        return len(getattr(call, "active_chats", []) or [])
    except Exception:
        return 0


def _assistant_count() -> int:
    try:
        from ..modules.clients import assistants

        return len(assistants) or (1 if getattr(console, "STRING1", None) else 0)
    except Exception:
        return 1 if getattr(console, "STRING1", None) else 0


def _ram_text() -> str:
    if not psutil:
        return "—"
    try:
        vm = psutil.virtual_memory()
        used = vm.used / (1024 ** 3)
        total = vm.total / (1024 ** 3)
        return f"{used:.1f}/{total:.1f} GiB ({vm.percent}%)"
    except Exception:
        return "—"


def _cpu_text() -> str:
    if not psutil:
        return "—"
    try:
        return f"{psutil.cpu_percent(interval=None)}%"
    except Exception:
        return "—"


def _ping_photo_url() -> str:
    url = getattr(console, "PING_IMAGE_URL", None) or PING_IMAGE
    if url and str(url).startswith("http"):
        return str(url)
    return PING_IMAGE


async def _load_photo() -> Union[str, io.BytesIO]:
    global _PHOTO_BYTES
    url = _ping_photo_url()

    if _PHOTO_BYTES:
        bio = io.BytesIO(_PHOTO_BYTES)
        bio.name = "ping.jpg"
        return bio

    if aiohttp is not None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if data and len(data) > 1000:
                            _PHOTO_BYTES = data
                            bio = io.BytesIO(data)
                            bio.name = "ping.jpg"
                            print(f"[ping] image downloaded {len(data)} bytes", flush=True)
                            return bio
        except Exception as e:
            print(f"[ping] download fail: {e}", flush=True)

    return url


async def _build_caption(
    client,
    ms: int,
    uptime: str,
    db: str,
    users: int,
    chats: int,
) -> str:
    me = getattr(client, "me", None)
    if me is None:
        try:
            me = await client.get_me()
        except Exception:
            me = None
    uname = (getattr(me, "username", None) or "Swastika_musics_bot").lstrip("@")
    label = _latency_label(ms)
    active = _active_vc_count()
    assistants_n = _assistant_count()
    ms_text = f"{ms}ms" if ms > 0 else "—"
    ram = _ram_text()
    cpu = _cpu_text()
    plat = platform.system() or "Linux"
    pyro_ver = getattr(_pyrogram, "__version__", "N/A") if _pyrogram else "N/A"

    # Each line = own quote (cleaner look)
    lines = [
        q(f"{em()} <b>Swastika Music v5</b>"),
        q(f"{em()} <b>@{uname}</b> — SYSTEM LIVE"),
        q(f"{em()} <b>VERSION</b> : <code>{_VERSION}</code>"),
        q(f"{em()} <b>LATENCY</b> : <code>{ms_text}</code> · {label}"),
        q(f"{em()} <b>UPTIME</b> : <code>{uptime}</code>"),
        q(f"{em()} <b>DATABASE</b> : <code>{db}</code>"),
        q(f"{em()} <b>ACTIVE VC</b> : <code>{active}</code>"),
        q(f"{em()} <b>ASSISTANTS</b> : <code>{assistants_n}</code>"),
        q(f"{em()} <b>USERS</b> : <code>{users}</code>"),
        q(f"{em()} <b>CHATS</b> : <code>{chats}</code>"),
        q(f"{em()} <b>RAM</b> : <code>{ram}</code>"),
        q(f"{em()} <b>CPU</b> : <code>{cpu}</code>"),
        q(f"{em()} <b>OS</b> : <code>{plat}</code>"),
        q(f"{em()} <b>PYROGRAM</b> : <code>{pyro_ver}</code>"),
        q(f"{em()} <i>POWERED BY SWASTIKA MUSIC</i>"),
    ]
    return "\n".join(lines)


@bot.on_message(cdx("ping") & filters.incoming)
async def ping_command(client, message: Message):
    print("[ping] command received", flush=True)

    chat_id = message.chat.id

    try:
        await message.delete()
    except Exception:
        pass

    photo_task = asyncio.create_task(_load_photo())
    ms, db, counts = await asyncio.gather(
        _get_latency(client),
        _db_status(),
        _served_counts(),
    )
    users, chats = counts
    photo = await photo_task

    uptime = _get_uptime()
    final = await _build_caption(client, ms, uptime, db, users, chats)
    keyboard = _ping_keyboard()

    try:
        await client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        print(f"[ping] ok photo ms={ms} db={db}", flush=True)
        return
    except Exception as e:
        print(f"[ping] send_photo+kb failed: {e}", flush=True)

    try:
        plain_row1 = [InlineKeyboardButton("Owner", url=_owner_url())]
        support = _support_url()
        if support:
            plain_row1.append(InlineKeyboardButton("Support", url=support))
        plain_row2 = [InlineKeyboardButton("Close", callback_data="close")]
        channel = _channel_url()
        if channel:
            plain_row2.insert(0, InlineKeyboardButton("Updates", url=channel))
        plain_kb = InlineKeyboardMarkup([plain_row1, plain_row2])

        if isinstance(photo, io.BytesIO):
            photo.seek(0)

        await client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=final,
            reply_markup=plain_kb,
            parse_mode=ParseMode.HTML,
        )
        print(f"[ping] ok plain photo ms={ms}", flush=True)
        return
    except Exception as e2:
        print(f"[ping] plain photo failed: {e2}", flush=True)

    try:
        if isinstance(photo, io.BytesIO):
            photo.seek(0)
        await client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=final,
            parse_mode=ParseMode.HTML,
        )
        print(f"[ping] ok photo no-kb ms={ms}", flush=True)
        return
    except Exception as e3:
        print(f"[ping] photo no-kb failed: {e3}", flush=True)

    try:
        await client.send_message(
            chat_id=chat_id,
            text=final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        print(f"[ping] ok text ms={ms}", flush=True)
    except Exception as e4:
        print(f"[ping] text failed: {e4}", flush=True)


print("[ping] plugin loaded OK", flush=True)
