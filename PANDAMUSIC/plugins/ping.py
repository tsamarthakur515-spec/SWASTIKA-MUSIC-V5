# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# /ping — Bot Status with Premium Emojis & Colored Buttons + Image
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import time
import asyncio
from datetime import datetime

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
    _SUCCESS = ButtonStyle.SUCCESS
    _DANGER = ButtonStyle.DANGER
except Exception:
    _PRIMARY = "primary"
    _SUCCESS = "success"
    _DANGER = "danger"

_BOT_START_TIME = time.time()


def _get_uptime() -> str:
    elapsed = int(time.time() - _BOT_START_TIME)
    days, remainder = divmod(elapsed, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _btn(text: str, style=None, emoji_id: str = None, **kwargs) -> InlineKeyboardButton:
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
    """Safe latency in ms — never hangs / crashes"""
    try:
        # Pyrogram: await client.ping → seconds
        val = await client.ping
        return int(round(float(val) * 1000))
    except Exception:
        pass
    try:
        start = time.time()
        await client.get_me()
        return int(round((time.time() - start) * 1000))
    except Exception:
        return 0


@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    pinging_msg = None
    chat_id = message.chat.id
    try:
        # Delete /ping command (ignore if no permission)
        try:
            await message.delete()
        except Exception:
            pass

        pinging_text = f"{tg_emoji(CE_PING_TITLE, '⚡')} ᴘɪɴɢɪɴɢ......"
        pinging_msg = await client.send_message(
            chat_id, pinging_text, parse_mode=ParseMode.HTML
        )

        await asyncio.sleep(0.5)

        bot_latency = await _get_latency(client)
        uptime = _get_uptime()
        database_status = "🟢 ᴄᴏɴɴᴇᴄᴛᴇᴅ"
        version = "v5.0.0"

        caption = (
            f"{tg_emoji(CE_PING_TITLE, '⚡')} {smallcaps('ᴘɪɴɢ ᴘᴏɴɢ')}\n\n"
            f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>ᴠᴇʀsɪᴏɴ</b> : <code>{version}</code>\n"
            f"{tg_emoji(CE_PING_MS, '✨')} <b>ᴍs</b> : <code>{bot_latency}ms</code>\n"
            f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>ᴜᴘᴛɪᴍᴇ</b> : <code>{uptime}</code>\n"
            f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>ᴅᴀᴛᴀʙᴀsᴇ</b> : <code>{database_status}</code>"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    _btn("⚠️ ᴀᴄᴛɪᴏɴ", style=_DANGER, emoji_id=CE_PING_DANGER, callback_data="ping_action"),
                    _btn("👑 ᴏᴡɴᴇʀ", style=_PRIMARY, emoji_id=E.STAR_W1, url="https://t.me/tsamarthakur515"),
                ],
            ]
        )

        ping_image_url = "https://files.catbox.moe/nd3z3n.jpg"

        # Photo with timeout — agar image hang ho to text bhejo
        try:
            await asyncio.wait_for(
                client.send_photo(
                    chat_id,
                    photo=ping_image_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                ),
                timeout=12,
            )
        except Exception as photo_err:
            console.log(f"[ping] photo failed: {photo_err}", style="yellow")
            await client.send_message(
                chat_id,
                caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

        console.log("[ping] /ping command executed successfully", style="green")

    except Exception as e:
        console.log(f"[ping] Error in ping command: {str(e)}", style="red")
        try:
            await client.send_message(chat_id, f"❌ Error: {str(e)[:100]}")
        except Exception:
            pass
    finally:
        if pinging_msg:
            try:
                await pinging_msg.delete()
            except Exception:
                pass
