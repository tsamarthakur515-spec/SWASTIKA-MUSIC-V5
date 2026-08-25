# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py  (stable + premium emojis + image)
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import time
import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console
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
    """Premium emoji caption (menu style)."""
    body = (
        f"{tg_emoji(CE_PING_TITLE, '⚡')} <b>{smallcaps('ping pong')}</b>\n\n"
        f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>{smallcaps('version')}</b> : <code>v5.0.0</code>\n"
        f"{tg_emoji(CE_PING_MS, '✨')} <b>{smallcaps('ms')}</b> : <code>{ms}ms</code>\n"
        f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>{smallcaps('uptime')}</b> : <code>{uptime}</code>\n"
        f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>{smallcaps('database')}</b> : <code>🟢 {smallcaps('connected')}</code>"
    )
    return f"<blockquote expandable>{body}</blockquote>"


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


@bot.on_message(filters.command("ping") & ~filters.forwarded)
async def ping_command(client, message: Message):
    # Measure first — no "pinging..." status message
    try:
        ms = await _get_latency(client)
        uptime = _get_uptime()
        caption = _ping_caption(ms, uptime)
        keyboard = _ping_keyboard()
        photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
            console, "START_IMAGE_URL", None
        )

        # Prefer photo reply (image + caption + buttons)
        sent = None
        if photo:
            try:
                sent = await message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                console.log(f"[ping] photo failed: {e}", style="yellow")

        if sent is None:
            try:
                sent = await message.reply_text(
                    caption,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                console.log(f"[ping] cannot reply: {e}", style="red")
                return

        # Delete user's /ping command
        try:
            await message.delete()
        except Exception:
            pass

        console.log("[ping] ok", style="green")

    except Exception as e:
        console.log(f"[ping] error: {e}", style="red")
        try:
            await message.reply_text(
                f"{tg_emoji(CE_PING_DANGER, '❌')} Ping error: <code>{str(e)[:120]}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
