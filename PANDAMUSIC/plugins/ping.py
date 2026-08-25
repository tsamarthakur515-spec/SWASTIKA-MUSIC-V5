# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# Smooth single reply (same pattern as /stats /start)
# No loading → delete → resend flicker
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import asyncio
import time

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console, cdx
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
except Exception:
    _SUCCESS = "success"

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


def _btn(text, style=None, emoji_id=None, **kwargs):
    """Same pattern as start.py / stats.py (works on kurigram send)."""
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
    return f"https://t.me/{owner}" if owner else "https://t.me/tsamarthakur515"


def _ping_keyboard() -> InlineKeyboardMarkup:
    """One SUCCESS owner URL button + premium star (E.STAR)."""
    return InlineKeyboardMarkup(
        [
            [
                _btn(
                    smallcaps("owner"),
                    style=_SUCCESS,
                    emoji_id=E.STAR,
                    url=_owner_url(),
                )
            ]
        ]
    )


async def _get_latency(client) -> int:
    try:
        t0 = time.perf_counter()
        await asyncio.wait_for(client.get_me(), timeout=1.5)
        return int(round((time.perf_counter() - t0) * 1000))
    except Exception as e:
        print(f"[ping] latency skip: {e}", flush=True)
        return 0


def _final_caption(ms: int, uptime: str) -> str:
    return (
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>{smallcaps('ping pong')}</b>\n\n"
        f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>{smallcaps('version')}</b> : <code>v5.0.0</code>\n"
        f"{tg_emoji(CE_PING_MS, '✨')} <b>{smallcaps('ms')}</b> : <code>{ms}ms</code>\n"
        f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>{smallcaps('uptime')}</b> : <code>{uptime}</code>\n"
        f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>{smallcaps('database')}</b> : <code>🟢 {smallcaps('connected')}</code>"
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

    # Measure first — no loading message (smooth)
    ms = await _get_latency(client)
    uptime = _get_uptime()
    final = _final_caption(ms, uptime)
    keyboard = _ping_keyboard()

    # Single clean reply (same style as /stats)
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
        print(f"[ping] ok ms={ms}", flush=True)
        return
    except Exception as e:
        print(f"[ping] photo+kb failed: {e}", flush=True)

    # Fallback: plain button (no style / custom emoji)
    try:
        plain_kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton(smallcaps("owner"), url=_owner_url())]]
        )
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

    # Last fallback: text only
    try:
        await message.reply_text(final, parse_mode=ParseMode.HTML)
        print(f"[ping] ok (text only) ms={ms}", flush=True)
    except Exception as e3:
        print(f"[ping] text failed: {e3}", flush=True)


print("[ping] plugin loaded OK", flush=True)
