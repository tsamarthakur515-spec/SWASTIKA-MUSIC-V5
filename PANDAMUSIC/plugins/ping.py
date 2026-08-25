# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py
# /ping — Bot Status with Premium Emojis & Colored Buttons
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import time
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

# Bot start time for uptime calculation
_BOT_START_TIME = time.time()


def _get_uptime() -> str:
    """Calculate bot uptime in human readable format"""
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
    """Create button with optional custom emoji icon"""
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


@bot.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    """
    /ping — Shows bot latency, version, uptime, database status
    """
    try:
        # Initial message with pinging animation
        initial_text = f"{tg_emoji(CE_PING_TITLE, '⚡')} ᴘɪɴɢɪɴɢ......"
        msg = await message.reply(initial_text, parse_mode=ParseMode.HTML)
        
        # Calculate metrics
        bot_latency = round(client.latency * 1000)
        uptime = _get_uptime()
        database_status = "🟢 ᴄᴏɴɴᴇᴄᴛᴇᴅ"
        version = "v5.0.0"
        
        # Create premium styled embed-like message
        caption = (
            f"{tg_emoji(CE_PING_TITLE, '⚡')} {smallcaps('ᴘɪɴɢ ᴘᴏɴɢ')}\n\n"
            f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>ᴠᴇʀsɪᴏɴ</b> : <code>{version}</code>\n"
            f"{tg_emoji(CE_PING_MS, '✨')} <b>ᴍs</b> : <code>{bot_latency}ms</code>\n"
            f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>ᴜᴘᴛɪᴍᴇ</b> : <code>{uptime}</code>\n"
            f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>ᴅᴀᴛᴀʙᴀsᴇ</b> : <code>{database_status}</code>\n"
        )
        
        # Create keyboard with danger button + owner button
        keyboard = InlineKeyboardMarkup(
            [
                [
                    _btn("⚠️ ᴀᴄᴛɪᴏɴ", style=_DANGER, emoji_id=CE_PING_DANGER, callback_data="ping_action"),
                    _btn("👑 ᴏᴡɴᴇʀ", style=_PRIMARY, emoji_id=E.STAR_W1, url="https://t.me/tsamarthakur515"),
                ],
            ]
        )
        
        # Edit message with final response
        await msg.edit(caption, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        console.log("[ping] /ping command executed successfully", style="green")
        
    except Exception as e:
        console.log(f"[ping] Error in ping command: {str(e)}", style="red")
        try:
            await message.reply(
                f"❌ Error: {str(e)[:100]}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass
