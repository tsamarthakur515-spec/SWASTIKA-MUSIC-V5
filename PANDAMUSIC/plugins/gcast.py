import asyncio
from pyrogram.errors import FloodWait

from .. import bot, cdx, sudoers
from ..modules.database import get_served_chats, get_served_users


async def _send_to_targets(client, message, targets: list, is_user: bool):
    sent = 0
    failed = 0
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        use_forward = True
        query = None
    else:
        if len(message.command) < 2:
            return -1, -1
        query = message.text.split(None, 1)[1]
        use_forward = False
        x = y = None
    for i in targets:
        try:
            if use_forward:
                await bot.forward_messages(i, y, x)
            else:
                await bot.send_message(i, text=query)
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if use_forward:
                    await bot.forward_messages(i, y, x)
                else:
                    await bot.send_message(i, text=query)
                sent += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1
    return sent, failed


@bot.on_message(cdx(["ubroadcast"]) & sudoers)
async def user_broadcast(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("**Reply to media/text or give text**\n`/ubroadcast` — users only")
    status = await message.reply_text("**Broadcasting to users...**")
    served_users = [int(u["user_id"]) for u in await get_served_users()]
    sent, failed = await _send_to_targets(client, message, served_users, True)
    if sent == -1:
        return await status.edit_text("**Reply to media/text or give text!**")
    await status.edit_text(f"**User Broadcast Done**\nUsers: `{sent}` Failed: `{failed}`")


@bot.on_message(cdx(["gbroadcast"]) & sudoers)
async def group_broadcast(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("**Reply to media/text or give text**\n`/gbroadcast` — groups only")
    status = await message.reply_text("**Broadcasting to groups...**")
    chats = [int(c["chat_id"]) for c in await get_served_chats()]
    sent, failed = await _send_to_targets(client, message, chats, False)
    if sent == -1:
        return await status.edit_text("**Reply to media/text or give text!**")
    await status.edit_text(f"**Group Broadcast Done**\nGroups: `{sent}` Failed: `{failed}`")


@bot.on_message(cdx(["broadcast", "gcast"]) & sudoers)
async def full_broadcast(client, message):
    try:
        await message.delete()
    except Exception:
        pass
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("`/broadcast` users+groups\n`/ubroadcast` users\n`/gbroadcast` groups")
    status = await message.reply_text("**Broadcasting to users + groups...**")
    served_users = [int(u["user_id"]) for u in await get_served_users()]
    user_sent, user_failed = await _send_to_targets(client, message, served_users, True)
    if user_sent == -1:
        return await status.edit_text("**Reply to media/text or give text!**")
    chats = [int(c["chat_id"]) for c in await get_served_chats()]
    gc_sent, gc_failed = await _send_to_targets(client, message, chats, False)
    await status.edit_text(
        f"**Full Broadcast Done**\nUsers: `{user_sent}` Groups: `{gc_sent}`\nFailed users: `{user_failed}` groups: `{gc_failed}`"
    )
