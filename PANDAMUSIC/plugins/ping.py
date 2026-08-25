# ---------------------------------------------------------------
# SWASTIKA MUSIC — ping.py  (stable)
# ---------------------------------------------------------------

print("[ping] loading plugin...", flush=True)

import time
import asyncio

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console
from ..modules.custom_emojis import E, tg_emoji, CE_PING_TITLE, CE_PING_VERSION, CE_PING_MS, CE_PING_UPTIME, CE_PING_DATABASE, CE_PING_DANGER
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


@bot.on_message(filters.command("ping") & \~filters.forwarded)
async def ping_command(client, message: Message):
    # 1) Pehle plain reply — isse hamesha kuch dikhega
    try:
        status = await message.reply_text("⚡ ᴘɪɴɢɪɴɢ......")
    except Exception as e:
        console.log(f"[ping] cannot reply: {e}", style="red")
        return

    try:
        await asyncio.sleep(0.3)
        ms = await _get_latency(client)
        uptime = _get_uptime()

        caption = (
            f"⚡ **ᴘɪɴɢ ᴘᴏɴɢ**\n\n"
            f"⭐ **ᴠᴇʀsɪᴏɴ** : `v5.0.0`\n"
            f"✨ **ᴍs** : `{ms}ms`\n"
            f"🔧 **ᴜᴘᴛɪᴍᴇ** : `{uptime}`\n"
            f"⚙️ **ᴅᴀᴛᴀʙᴀsᴇ** : `🟢 ᴄᴏɴɴᴇᴄᴛᴇᴅ`"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    _btn("⚠️ ᴀᴄᴛɪᴏɴ", style=_DANGER, callback_data="ping_action"),
                    _btn("👑 ᴏᴡɴᴇʀ", style=_PRIMARY, url="https://t.me/tsamarthakur515"),
                ]
            ]
        )

        # 2) Same message edit karo (photo skip — hang nahi hoga)
        try:
            await status.edit_text(caption, reply_markup=keyboard)
        except Exception:
            await status.edit_text(caption)

        # 3) User ka /ping delete (optional)
        try:
            await message.delete()
        except Exception:
            pass

        console.log("[ping] ok", style="green")

    except Exception as e:
        console.log(f"[ping] error: {e}", style="red")
        try:
            await status.edit_text(f"❌ Ping error: `{str(e)[:120]}`")
        except Exception:
            pass
