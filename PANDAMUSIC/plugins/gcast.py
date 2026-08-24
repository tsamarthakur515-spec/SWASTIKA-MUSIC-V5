import asyncio
from pyrogram.errors import FloodWait

from .. import bot, cdx, sudoers
from ..modules.database import get_served_chats, get_served_users


async def _send_to_targets(client, message, targets: list, is_user: bool):
    """Send reply or text to a list of targets. Returns (sent, failed)."""
    sent = 0
    failed = 0

    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
        use_forward = True
        query = None
    else:
        if len(message.command) < 2:
            return -1, -1  # signal: no content
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
    """Broadcast only to users."""
    try:
        await message.delete()
    except Exception:
        pass

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "**🤖 Reply to any media/text**\n"
            "**or give text after command**\n\n"
            "`/ubroadcast` — send to **users** only"
        )

    status = await message.reply_text("**📤 Broadcasting to users...**")

    served_users = []
    susers = await get_served_users()
    for user in susers:
        served_users.append(int(user["user_id"]))

    sent, failed = await _send_to_targets(client, message, served_users, is_user=True)

    if sent == -1:
        return await status.edit_text(
            "**🤖 Reply to any media/text or give some text!**"
        )

    total = sent + failed
    await status.edit_text(
        f"**✅ User Broadcast Done**\n\n"
        f"👤 **Users Sent :** `{sent}`\n"
        f"❌ **Failed :** `{failed}`\n"
        f"📊 **Total Tried :** `{total}`"
    )


@bot.on_message(cdx(["gbroadcast"]) & sudoers)
async def group_broadcast(client, message):
    """Broadcast only to groups/chats."""
    try:
        await message.delete()
    except Exception:
        pass

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "**🤖 Reply to any media/text**\n"
            "**or give text after command**\n\n"
            "`/gbroadcast` — send to **groups** only"
        )

    status = await message.reply_text("**📤 Broadcasting to groups...**")

    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))

    sent, failed = await _send_to_targets(client, message, chats, is_user=False)

    if sent == -1:
        return await status.edit_text(
            "**🤖 Reply to any media/text or give some text!**"
        )

    total = sent + failed
    await status.edit_text(
        f"**✅ Group Broadcast Done**\n\n"
        f"💬 **Groups Sent :** `{sent}`\n"
        f"❌ **Failed :** `{failed}`\n"
        f"📊 **Total Tried :** `{total}`"
    )


@bot.on_message(cdx(["broadcast", "gcast"]) & sudoers)
async def full_broadcast(client, message):
    """Broadcast to both users + groups."""
    try:
        await message.delete()
    except Exception:
        pass

    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "**🤖 Reply to any media/text**\n"
            "**or give text after command**\n\n"
            "`/broadcast` — send to **users + groups**\n"
            "`/ubroadcast` — users only\n"
            "`/gbroadcast` — groups only"
        )

    status = await message.reply_text("**📤 Broadcasting to users + groups...**")

    # Users
    served_users = []
    susers = await get_served_users()
    for user in susers:
        served_users.append(int(user["user_id"]))

    user_sent, user_failed = await _send_to_targets(
        client, message, served_users, is_user=True
    )

    if user_sent == -1:
        return await status.edit_text(
            "**🤖 Reply to any media/text or give some text!**"
        )

    # Groups
    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))

    gc_sent, gc_failed = await _send_to_targets(
        client, message, chats, is_user=False
    )

    total_sent = user_sent + gc_sent
    total_failed = user_failed + gc_failed
    total = total_sent + total_failed

    await status.edit_text(
        f"**✅ Full Broadcast Done**\n\n"
        f"👤 **Users Sent :** `{user_sent}`\n"
        f"❌ **Users Failed :** `{user_failed}`\n\n"
        f"💬 **Groups Sent :** `{gc_sent}`\n"
        f"❌ **Groups Failed :** `{gc_failed}`\n\n"
        f"📊 **Total Sent :** `{total_sent}`\n"
        f"📊 **Total Failed :** `{total_failed}`\n"
        f"📊 **Total Tried :** `{total}`"
    )