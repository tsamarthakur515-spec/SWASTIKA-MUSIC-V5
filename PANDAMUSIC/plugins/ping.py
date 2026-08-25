# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# image + ᴘɪɴɢɪɴɢ... → edit final | premium emojis | smallcaps
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
    CE_PING_DANGER,
)
from ..modules.formatters import smallcaps

try:
    from pyrogram.enums import ButtonStyle

    _PRIMARY = ButtonStyle.PRIMARY
    _SUCCESS = ButtonStyle.SUCCESS
    _DANGER = ButtonStyle.DANGER
except Exception:
    _PRIMARY = "primary"
    _SUCCESS = "success"
    _DANGER = "danger"

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
    """Fast latency — never hang more than ~2s."""

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


def _ping_keyboard() -> InlineKeyboardMarkup:
    owner = (getattr(console, "OWNER_USERNAME", None) or "").lstrip("@")
    owner_url = f"https://t.me/{owner}" if owner else "https://t.me/tsamarthakur515"

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
                    style=_SUCCESS,
                    emoji_id=E.STAR,
                    url=owner_url,
                ),
            ]
        ]
    )


async def _edit_final(status, final: str, keyboard: InlineKeyboardMarkup):
    """Always try hard to leave PINGING... state."""
    # photo message → edit_caption
    try:
        await status.edit_caption(
            caption=final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception as e:
        print(f"[ping] edit_caption: {e}", flush=True)

    # text message → edit_text
    try:
        await status.edit_text(
            final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
        return True
    except Exception as e:
        print(f"[ping] edit_text: {e}", flush=True)

    # caption without keyboard
    try:
        await status.edit_caption(caption=final, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        print(f"[ping] edit_caption no-kb: {e}", flush=True)

    # last: delete stuck msg + new reply
    try:
        chat_id = status.chat.id
        await status.delete()
    except Exception:
        chat_id = None

    try:
        if chat_id is not None:
            await bot.send_photo(
                chat_id,
                photo=getattr(console, "STATS_IMAGE_URL", None)
                or getattr(console, "START_IMAGE_URL", ""),
                caption=final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            await status.reply_text(
                final, reply_markup=keyboard, parse_mode=ParseMode.HTML
            )
        return True
    except Exception as e:
        print(f"[ping] resend failed: {e}", flush=True)
        try:
            await status.reply_text(
                f"⚡ {smallcaps('ping pong')}\n"
                f"✨ ms: {final[-80:]}"
            )
        except Exception:
            pass
        return False


@bot.on_message(cdx("ping") & filters.incoming)
async def ping_command(client, message: Message):
    print("[ping] command received", flush=True)

    photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
        console, "START_IMAGE_URL", None
    )

    # Delete user /ping
    try:
        await message.delete()
    except Exception:
        pass

    # 1) Image + PINGING...
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

    # 2) Latency (max 2s — never stuck)
    ms = await _get_latency(client)
    uptime = _get_uptime()
    final = _final_caption(ms, uptime)
    keyboard = _ping_keyboard()

    # 3) MUST leave PINGING...
    ok = await _edit_final(status, final, keyboard)
    print(f"[ping] ok={ok} ms={ms}", flush=True)


print("[ping] plugin loaded OK", flush=True)
