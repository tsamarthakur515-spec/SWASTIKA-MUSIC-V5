# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# image + ᴘɪɴɢɪɴɢ... → delete → final photo+caption+owner button
# (kurigram: edit_caption with reply_markup breaks KeyboardButtonUrl)
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

    # 1) Loading message (NO keyboard — avoids kurigram edit+kb bug)
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

    # 2) Measure
    ms = await _get_latency(client)
    uptime = _get_uptime()
    final = _final_caption(ms, uptime)
    keyboard = _ping_keyboard()
    chat_id = status.chat.id

    # 3) Delete loading → send FINAL with keyboard (same path as /stats /start)
    try:
        await status.delete()
    except Exception as e:
        print(f"[ping] delete loading: {e}", flush=True)

    sent = False

    if photo:
        try:
            await client.send_photo(
                chat_id,
                photo=photo,
                caption=final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent = True
        except Exception as e:
            print(f"[ping] send_photo+kb: {e}", flush=True)
            # try without style/emoji keyboard
            try:
                plain_kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(smallcaps("owner"), url=_owner_url())]]
                )
                await client.send_photo(
                    chat_id,
                    photo=photo,
                    caption=final,
                    reply_markup=plain_kb,
                    parse_mode=ParseMode.HTML,
                )
                sent = True
            except Exception as e2:
                print(f"[ping] send_photo plain kb: {e2}", flush=True)
                try:
                    await client.send_photo(
                        chat_id,
                        photo=photo,
                        caption=final,
                        parse_mode=ParseMode.HTML,
                    )
                    sent = True
                except Exception as e3:
                    print(f"[ping] send_photo no kb: {e3}", flush=True)

    if not sent:
        try:
            await client.send_message(
                chat_id,
                final,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
            sent = True
        except Exception as e:
            print(f"[ping] send_message+kb: {e}", flush=True)
            try:
                await client.send_message(
                    chat_id,
                    final + f"\n\n⭐ <a href=\"{_owner_url()}\">{smallcaps('owner')}</a>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
                sent = True
            except Exception as e2:
                print(f"[ping] send_message plain: {e2}", flush=True)

    print(f"[ping] ok={sent} ms={ms}", flush=True)


print("[ping] plugin loaded OK", flush=True)
