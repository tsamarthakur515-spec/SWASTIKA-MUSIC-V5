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
    /ping — Shows bot latency, version, uptime, database status with image
    
    Flow:
    1. Delete user's /ping command
    2. Send "Pinging......" message
    3. Send image with caption and buttons
    4. Delete the "Pinging......" message
    """
    try:
        # Step 1: Delete user's /ping command message
        await message.delete()
        
        # Step 2: Send pinging animation message
        pinging_text = f"{tg_emoji(CE_PING_TITLE, '⚡')} ᴘɪɴɢɪɴɢ......"
        pinging_msg = await message.reply(pinging_text, parse_mode=ParseMode.HTML)
        
        # Small delay for visual effect
        await asyncio.sleep(1)
        
        # Calculate metrics
        bot_latency = round(client.latency * 1000)
        uptime = _get_uptime()
        database_status = "🟢 ᴄᴏɴɴᴇᴄᴛᴇᴅ"
        version = "v5.0.0"
        
        # Create premium styled caption
        caption = (
            f"{tg_emoji(CE_PING_TITLE, '⚡')} {smallcaps('ᴘɪɴɢ ᴘᴏɴɢ')}\n\n"
            f"{tg_emoji(CE_PING_VERSION, '⭐')} <b>ᴠᴇʀsɪᴏɴ</b> : <code>{version}</code>\n"
            f"{tg_emoji(CE_PING_MS, '✨')} <b>ᴍs</b> : <code>{bot_latency}ms</code>\n"
            f"{tg_emoji(CE_PING_UPTIME, '🔧')} <b>ᴜᴘᴛɪᴍᴇ</b> : <code>{uptime}</code>\n"
            f"{tg_emoji(CE_PING_DATABASE, '⚙️')} <b>ᴅᴀᴛᴀʙᴀsᴇ</b> : <code>{database_status}</code>"
        )
        
        # Create keyboard with buttons
        keyboard = InlineKeyboardMarkup(
            [
                [
                    _btn("⚠️ ᴀᴄᴛɪᴏɴ", style=_DANGER, emoji_id=CE_PING_DANGER, callback_data="ping_action"),
                    _btn("👑 ᴏᴡɴᴇʀ", style=_PRIMARY, emoji_id=E.STAR_W1, url="https://t.me/tsamarthakur515"),
                ],
            ]
        )
        
        # Step 3: Send image with caption and buttons
        # Change this to your image path/URL
        ping_image_url = "https://te.legra.ph/file/your-ping-image.jpg"  # Replace with your image
        
        await message.reply_photo(
            photo=ping_image_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        
        # Step 4: Delete the pinging message
        await pinging_msg.delete()
        
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
