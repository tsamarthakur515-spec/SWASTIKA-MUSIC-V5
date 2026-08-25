# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# Improved smooth ping: real DB status, latency label, dual buttons
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import asyncio
import time
from typing import Optional

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, call, console, cdx
from ..modules.custom_emojis import (
    E,
    tg_emoji,
    CE_PING_TITLE,
    CE_PING_VERSION,
    CE_PING_MS,
    CE_PING_UPTIME,
    CE_PING_DATABASE,
)
from ..modules.formatters import smallcaps

try:
    from pyrogram.enums import ButtonStyle

    _SUCCESS = ButtonStyle.SUCCESS
    _PRIMARY = ButtonStyle.PRIMARY
except Exception:
    _SUCCESS = "success"
    _PRIMARY = "primary"

_BOT_START_TIME = time.time()


def _get_uptime() -> str:
    elapsed = int(time.time() - _BOT_START_TIME)
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
        return smallcaps("n/a")
    if ms < 80:
        return f"🟢 {smallcaps('excellent')}"
    if ms < 150:
        return f"🟡 {smallcaps('good')}"
    if ms < 300:
        return f"🟠 {smallcaps('average')}"
    return f"🔴 {smallcaps('slow')}"


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


def _ping_keyboard() -> InlineKeyboardMarkup:
    row = [
        _btn(
            smallcaps("owner"),
            style=_SUCCESS,
            emoji_id=E.STAR,
            url=_owner_url(),
        )
    ]
    support = _support_url()
    if support:
        row.append(
            _btn(
                smallcaps("support"),
                style=_PRIMARY,
                emoji_id=E.BUTTERFLY,
                url=support,
            )
        )
    return InlineKeyboardMarkup([row])


async def _get_latency(client) -> int:
    try:
        t0 = time.perf_counter()
        await asyncio.wait_for(client.get_me(), timeout=1.5)
        return int(round((time.perf_counter() - t0) * 1000))
    except Exception as e:
        print(f"[ping] latency skip: {e}", flush=True)
        return 0


async def _db_status() -> str:
    """Real DB check — green if pool alive, else offline/memory."""
    try:
        from ..modules.database import _ok, _pool

        if not _ok() or _pool is None:
            return f"⚪ {smallcaps('offline')} ({smallcaps('memory')})"
        async with _pool.acquire() as conn:
            await asyncio.wait_for(conn.fetchval("SELECT 1"), timeout=1.0)
        return f"🟢 {smallcaps('connected')}"
    except Exception:
        return f"🔴 {smallcaps('error')}"


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


async def _build_caption(client, ms: int, uptime: str, db: str) -> str:
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

    return (
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>𝗦𝘄𝗮𝘀𝘁𝗶𝗸𝗮 𝗠𝘂𝘀𝗶𝗰 𝘃𝟱</b>\n"
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>@{uname}</b> — {smallcaps('ping pong')}\n\n"
        f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>{smallcaps('version')}</b> : <code>v5.0.0</code>\n"
        f"{tg_emoji(CE_PING_MS, '✨')} <b>{smallcaps('latency')}</b> : <code>{ms_text}</code> · {label}\n"
        f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>{smallcaps('uptime')}</b> : <code>{uptime}</code>\n"
        f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>{smallcaps('database')}</b> : <code>{db}</code>\n"
        f"{tg_emoji(E.FIRE, '🔥')} <b>{smallcaps('active vc')}</b> : <code>{active}</code>\n"
        f"{tg_emoji(E.WOLF, '🐺')} <b>{smallcaps('assistants')}</b> : <code>{assistants_n}</code>\n\n"
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <i>{smallcaps('powered by swastika music')}</i>"
    )


@bot.on_message(cdx("ping") & filters.incoming)
async def ping_command(client, message: Message):
    print("[ping] command received", flush=True)

    photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
        console, "START_IMAGE_URL", None
    )

    try:
        await message.delete()
    except Exception:
        pass

    # Parallel: latency + DB check (faster)
    ms_task = asyncio.create_task(_get_latency(client))
    db_task = asyncio.create_task(_db_status())
    ms, db = await asyncio.gather(ms_task, db_task)

    uptime = _get_uptime()
    final = await _build_caption(client, ms, uptime, db)
    keyboard = _ping_keyboard()

    try:
        if photo:
            await message.reply_photo(
                photo=photo,
                caption=final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply_text(
                final, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        print(f"[ping] ok ms={ms} db={db}", flush=True)
        return
    except Exception as e:
        print(f"[ping] photo+kb failed: {e}", flush=True)

    # Fallback: plain buttons
    try:
        plain_row = [InlineKeyboardButton(smallcaps("owner"), url=_owner_url())]
        support = _support_url()
        if support:
            plain_row.append(InlineKeyboardButton(smallcaps("support"), url=support))
        plain_kb = InlineKeyboardMarkup([plain_row])
        if photo:
            await message.reply_photo(
                photo=photo,
                caption=final,
                reply_markup=plain_kb,
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply_text(
                final, reply_markup=plain_kb, parse_mode=ParseMode.HTML
            )
        print(f"[ping] ok (plain kb) ms={ms}", flush=True)
        return
    except Exception as e2:
        print(f"[ping] plain kb failed: {e2}", flush=True)

    try:
        await message.reply_text(final, parse_mode=ParseMode.HTML)
        print(f"[ping] ok (text only) ms={ms}", flush=True)
    except Exception as e3:
        print(f"[ping] text failed: {e3}", flush=True)


print("[ping] plugin loaded OK", flush=True)
