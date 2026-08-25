# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# image + ᴘɪɴɢɪɴɢ... → edit final | premium emojis | owner SUCCESS star
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

_PINGING_CAPTION = (
    f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>{smallcaps('pinging')}...</b>"
)


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


def _owner_button() -> InlineKeyboardButton:
    """SUCCESS color + premium star (E.STAR) + owner URL."""
    owner = (getattr(console, "OWNER_USERNAME", None) or "").lstrip("@")
    owner_url = f"https://t.me/{owner}" if owner else "https://t.me/tsamarthakur515"
    text = smallcaps("owner")
    star_id = str(E.STAR)

    # 1) SUCCESS + custom emoji icon
    for style in (_SUCCESS, "success", None):
        kwargs = {"url": owner_url, "icon_custom_emoji_id": star_id}
        try:
            if style is not None:
                return InlineKeyboardButton(text, style=style, **kwargs)
            return InlineKeyboardButton(text, **kwargs)
        except TypeError:
            continue
        except Exception:
            continue

    # 2) URL + emoji only (no style)
    try:
        return InlineKeyboardButton(
            text, url=owner_url, icon_custom_emoji_id=star_id
        )
    except TypeError:
        pass

    # 3) Plain URL fallback
    return InlineKeyboardButton(f"⭐ {text}", url=owner_url)


def _ping_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[_owner_button()]])


async def _get_latency(client) -> int:
    async def _measure() -> int:
        t0 = time.perf_counter()
        await client.get_me()
        return int(round((time.perf_counter() - t0) * 1000))

    try:
        return await asyncio.wait_for(_measure(), timeout=2.0)
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


async def _edit_final(status, final: str, keyboard: InlineKeyboardMarkup):
    try:
        await status.edit_caption(
            caption=final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception as e:
        print(f"[ping] edit_caption+kb: {e}", flush=True)

    try:
        await status.edit_text(
            final, reply_markup=keyboard, parse_mode=ParseMode.HTML
        )
        return True
    except Exception as e:
        print(f"[ping] edit_text+kb: {e}", flush=True)

    # Caption only, then try attach keyboard separately if needed
    try:
        await status.edit_caption(caption=final, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"[ping] edit_caption: {e}", flush=True)
        try:
            await status.edit_text(final, parse_mode=ParseMode.HTML)
        except Exception as e2:
            print(f"[ping] edit_text: {e2}", flush=True)

    # Resend with keyboard (URL-only — no callback types)
    try:
        chat_id = status.chat.id
        photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
            console, "START_IMAGE_URL", None
        )
        try:
            await status.delete()
        except Exception:
            pass
        if photo:
            await bot.send_photo(
                chat_id,
                photo=photo,
                caption=final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_message(
                chat_id,
                final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        return True
    except Exception as e:
        print(f"[ping] resend: {e}", flush=True)
        return False


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

    status = None
    if photo:
        try:
            status = await message.reply_photo(
                photo=photo,
                caption=_PINGING_CAPTION,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] photo failed: {e}", flush=True)

    if status is None:
        try:
            status = await message.reply_text(
                _PINGING_CAPTION, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"[ping] text failed: {e}", flush=True)
            return

    ms = await _get_latency(client)
    uptime = _get_uptime()
    final = _final_caption(ms, uptime)
    keyboard = _ping_keyboard()

    ok = await _edit_final(status, final, keyboard)
    print(f"[ping] ok={ok} ms={ms}", flush=True)


print("[ping] plugin loaded OK", flush=True)
