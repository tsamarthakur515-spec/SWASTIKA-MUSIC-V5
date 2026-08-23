# PANDAMUSIC — sudo.py
print("[sudo] loading plugin...", flush=True)

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from .. import bot, console
from ..modules.database import add_sudo, remove_sudo, get_sudoers_list


def is_owner(user_id: int) -> bool:
    return bool(user_id and user_id == getattr(console, "OWNER_ID", 0))


async def resolve_target(client, msg: Message):
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user
    args = msg.command or []
    if len(args) < 2:
        return None
    raw = args[1].strip()
    if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
        try:
            return await client.get_users(int(raw))
        except Exception:
            return None
    try:
        return await client.get_users(raw.lstrip("@"))
    except Exception:
        return None


@bot.on_message(filters.command(["addsudo", "addsudoer"], ["/", "!", "."]) & filters.incoming, group=0)
async def addsudo_cmd(client, msg: Message):
    if not msg.from_user or not is_owner(msg.from_user.id):
        return await msg.reply_text("❌ Only the <b>bot owner</b> can add sudo users.", parse_mode=ParseMode.HTML)
    target = await resolve_target(client, msg)
    if not target:
        return await msg.reply_text("<b>Usage:</b> reply / ID / @username", parse_mode=ParseMode.HTML)
    if target.is_bot:
        return await msg.reply_text("❌ Bots cannot be sudo.")
    if target.id == console.OWNER_ID:
        return await msg.reply_text("✅ Owner is already the highest authority.")
    sudos = await get_sudoers_list()
    if target.id in sudos:
        return await msg.reply_text(f"⚠️ {target.mention} is already a sudo user.", parse_mode=ParseMode.HTML)
    await add_sudo(target.id)
    try:
        if target.id not in console.sudoers:
            console.sudoers.add(target.id)
    except Exception:
        pass
    await msg.reply_text(f"✅ <b>Sudo added!</b>\n👤 {target.mention}\n🆔 <code>{target.id}</code>", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command(["delsudo", "rmsudo", "remsudo"], ["/", "!", "."]) & filters.incoming, group=0)
async def delsudo_cmd(client, msg: Message):
    if not msg.from_user or not is_owner(msg.from_user.id):
        return await msg.reply_text("❌ Only the <b>bot owner</b> can remove sudo users.", parse_mode=ParseMode.HTML)
    target = await resolve_target(client, msg)
    if not target:
        return await msg.reply_text("<b>Usage:</b> reply / ID / @username", parse_mode=ParseMode.HTML)
    if target.id == console.OWNER_ID:
        return await msg.reply_text("❌ Owner ko sudo list se hata nahi sakte.")
    ok = await remove_sudo(target.id)
    if not ok:
        return await msg.reply_text(f"⚠️ {target.mention} sudo list mein nahi hai.", parse_mode=ParseMode.HTML)
    await msg.reply_text(f"✅ <b>Sudo removed!</b>\n👤 {target.mention}", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command(["sudolist", "sudos", "listsudo"], ["/", "!", "."]) & filters.incoming, group=0)
async def sudolist_cmd(client, msg: Message):
    uid = msg.from_user.id if msg.from_user else 0
    sudos = await get_sudoers_list()
    if uid != console.OWNER_ID and uid not in sudos:
        return await msg.reply_text("❌ Only owner / sudo can view the sudo list.")
    if not sudos:
        return await msg.reply_text("📭 Sudo list empty.")
    lines = ["👑 <b>Sudo Users</b>\n"]
    for i, sid in enumerate(sudos, 1):
        tag = " (Owner)" if sid == console.OWNER_ID else ""
        try:
            u = await client.get_users(sid)
            name = u.mention if u else f"<code>{sid}</code>"
        except Exception:
            name = f"<code>{sid}</code>"
        lines.append(f"{i}. {name}{tag}\n   🆔 <code>{sid}</code>")
    await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

print("[sudo] plugin loaded OK", flush=True)
