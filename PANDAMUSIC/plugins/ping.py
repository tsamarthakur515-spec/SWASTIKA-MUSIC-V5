# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# image + ᴘɪɴɢɪɴɢ... → edit final caption | premium emojis | smallcaps
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
    _SUCCESS = ButtonStyle.SUCCESS
    _DANGER = ButtonStyle.DANGER
except Exception:
    _PRIMARY = "primary"
    _SUCCESS = "success"
    _DANGER = "danger"

_BOT_START_TIME = time.time()

# Loading caption (smallcaps style)
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


def _final_caption(ms: int, uptime: str) -> str:
    """Final menu caption — premium emojis + smallcaps."""
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
                # SUCCESS style + star premium emoji from custom_emojis.py
                _btn(
                    smallcaps("owner"),
                    style=_SUCCESS,
                    emoji_id=E.STAR,
                    url=owner_url,
                ),
            ]
        ]
    )


@bot.on_message(cdx("ping") & filters.incoming)
async def ping_command(client, message: Message):
    print("[ping] command received", flush=True)

    photo = getattr(console, "STATS_IMAGE_URL", None) or getattr(
        console, "START_IMAGE_URL", None
    )

    # Delete user /ping command
    try:
        await message.delete()
    except Exception:
        pass

    status = None

    # 1) Send image + ᴘɪɴɢɪɴɢ... caption
    if photo:
        try:
            status = await message.reply_photo(
                photo=photo,
                caption=_PINGING_CAPTION,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] photo+pinging failed: {e}", flush=True)

    if status is None:
        try:
            status = await message.reply_text(
                _PINGING_CAPTION,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] text+pinging failed: {e}", flush=True)
            try:
                status = await message.reply_text(smallcaps("pinging") + "...")
            except Exception as e2:
                print(f"[ping] plain pinging failed: {e2}", flush=True)
                return

    # 2) Measure
    ms = 0
    uptime = "0s"
    try:
        ms = await _get_latency(client)
        uptime = _get_uptime()
    except Exception as e:
        print(f"[ping] latency error: {e}", flush=True)

    final = _final_caption(ms, uptime)
    keyboard = _ping_keyboard()

    # 3) Edit caption → final menu
    try:
        await status.edit_caption(
            caption=final,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        try:
            await status.edit_text(
                final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            print(f"[ping] edit final failed: {e}", flush=True)
            try:
                await message.reply_text(
                    final, reply_markup=keyboard, parse_mode=ParseMode.HTML
                )
            except Exception as e2:
                print(f"[ping] final reply failed: {e2}", flush=True)

    print("[ping] ok", flush=True)


print("[ping] plugin loaded OK", flush=True)
