# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py  (stable + premium emojis + image)
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

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
    CE_PING_DANGER,
)
from ..modules.formatters import smallcaps

try:
    from pyrogram.enums import ButtonStyle

    _PRIMARY = ButtonStyle.PRIMARY
    _DANGER = ButtonStyle.DANGER
except Exception:
    _PRIMARY = "primary"
    _DANGER = "danger"

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


async def _get_latency(client) -> int:
    try:
        val = await client.ping
        return int(round(float(val) * 1000))
    except Exception:
        pass
    try:
        t0 = time.time()
        await client.get_me()
        return int(round((time.time() - t0) * 1000))
    except Exception:
        return 0


def _ping_caption(ms: int, uptime: str) -> str:
    return (
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>{smallcaps('ping pong')}</b>\n\n"
        f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>{smallcaps('version')}</b> : <code>v5.0.0</code>\n"
        f"{tg_emoji(CE_PING_MS, '✨')} <b>{smallcaps('ms')}</b> : <code>{ms}ms</code>\n"
        f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>{smallcaps('uptime')}</b> : <code>{uptime}</code>\n"
        f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>{smallcaps('database')}</b> : <code>🟢 {smallcaps('connected')}</code>"
    )


def _ping_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _btn(
                    smallcaps("action"),
                    style=_DANGER,
                    emoji_id=CE_PING_DANGER,
                    callback_data="ping_action",
                ),
                _btn(
                    smallcaps("owner"),
                    style=_PRIMARY,
                    emoji_id=E.STAR,
                    url="https://t.me/tsamarthakur515",
                ),
            ]
        ]
    )


@bot.on_message(cdx("ping") & filters.incoming)
async def ping_command(client, message: Message):
    print("[ping] command received", flush=True)

    ms = 0
    uptime = "0s"
    try:
        ms = await _get_latency(client)
        uptime = _get_uptime()
    except Exception as e:
        print(f"[ping] latency/uptime error: {e}", flush=True)

    caption = _ping_caption(ms, uptime)
    keyboard = _ping_keyboard()
    photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
        console, "START_IMAGE_URL", None
    )

    sent = None

    # 1) Try photo
    if photo:
        try:
            sent = await message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] photo failed: {e}", flush=True)

    # 2) Fallback text + keyboard
    if sent is None:
        try:
            sent = await message.reply_text(
                caption,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] text+kb failed: {e}", flush=True)

    # 3) Fallback plain text (no HTML / no buttons)
    if sent is None:
        try:
            plain = (
                f"⚡ PING PONG\n"
                f"⭐ Version : v5.0.0\n"
                f"✨ MS : {ms}ms\n"
                f"🔧 Uptime : {uptime}\n"
                f"⚙️ Database : connected"
            )
            sent = await message.reply_text(plain)
        except Exception as e:
            print(f"[ping] plain reply failed: {e}", flush=True)
            return

    # Delete user /ping (optional)
    try:
        await message.delete()
    except Exception:
        pass

    print("[ping] ok", flush=True)


print("[ping] plugin loaded OK", flush=True)
