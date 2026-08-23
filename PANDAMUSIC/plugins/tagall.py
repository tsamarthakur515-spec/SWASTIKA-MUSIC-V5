print("[tagall] loading plugin...", flush=True)

import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ParseMode
from pyrogram.types import Message
from .. import bot, console

BATCH_SIZE = 5
BATCH_DELAY = 1.2


async def is_privileged(client, chat_id: int, user_id: int) -> bool:
    try:
        if user_id and user_id == getattr(console, "OWNER_ID", 0):
            return True
        if user_id in getattr(console, "sudoers", []):
            return True
    except Exception:
        pass
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


def mention_html(user) -> str:
    name = (user.first_name or "User").replace("<", "").replace(">", "")
    if user.last_name:
        name = f"{name} {user.last_name}".replace("<", "").replace(">", "")
    if len(name) > 20:
        name = name[:18] + ".."
    return f'<a href="tg://user?id={user.id}">{name}</a>'


async def _collect_members(client, chat_id: int):
    members = []
    try:
        async for member in client.get_chat_members(chat_id):
            user = member.user
            if not user or user.is_bot or user.is_deleted:
                continue
            members.append(user)
    except Exception as e:
        print(f"[tagall] get_chat_members error: {e}", flush=True)
        try:
            async for member in client.get_chat_members(chat_id, filter=ChatMembersFilter.SEARCH):
                user = member.user
                if not user or user.is_bot or user.is_deleted:
                    continue
                members.append(user)
        except Exception as e2:
            print(f"[tagall] fallback: {e2}", flush=True)
    return members


@bot.on_message(
    filters.command(["tagall", "tag", "mentionall"], ["/", "!", "."])
    & ~filters.private & filters.incoming, group=0,
)
async def tagall_cmd(client, msg: Message):
    chat_id = msg.chat.id
    if not msg.from_user:
        return await msg.reply_text("❌ Anonymous admins cannot use this.")
    if not await is_privileged(client, chat_id, msg.from_user.id):
        return await msg.reply_text("❌ Only admins / owner / sudo can use /tagall.", parse_mode=ParseMode.HTML)
    text = ""
    if msg.reply_to_message:
        text = (msg.reply_to_message.text or msg.reply_to_message.caption or "").strip()
    args = msg.command or []
    if len(args) > 1:
        raw = msg.text or msg.caption or ""
        parts = raw.split(None, 1)
        if len(parts) > 1:
            text = parts[1].strip()
    if not text:
        return await msg.reply_text("<b>Usage:</b> <code>/tagall hi</code> or reply + /tagall", parse_mode=ParseMode.HTML)
    status = await msg.reply_text("🔄 Collecting members...")
    members = await _collect_members(client, chat_id)
    if not members:
        try:
            await status.edit_text("❌ No members found. Bot needs to be admin.")
        except Exception:
            pass
        return
    total = len(members)
    try:
        await status.edit_text(f"📣 Tagging <b>{total}</b> members...", parse_mode=ParseMode.HTML)
    except Exception:
        pass
    sent = failed = 0
    for i in range(0, total, BATCH_SIZE):
        batch = members[i:i+BATCH_SIZE]
        mentions = " ".join(mention_html(u) for u in batch)
        body = f"{text}\n\n{mentions}"
        try:
            await client.send_message(chat_id, body, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            sent += len(batch)
        except Exception as e:
            failed += len(batch)
            print(f"[tagall] send error: {e}", flush=True)
            await asyncio.sleep(5 if "flood" in str(e).lower() else 1)
        if i + BATCH_SIZE < total:
            await asyncio.sleep(BATCH_DELAY)
    try:
        await status.edit_text(
            f"✅ <b>Tagall done!</b>\n👥 {total} | 📣 {sent}"
            + (f"\n⚠️ Failed: {failed}" if failed else ""),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
    await asyncio.sleep(8)
    try:
        await status.delete()
    except Exception:
        pass

print("[tagall] plugin loaded OK", flush=True)
