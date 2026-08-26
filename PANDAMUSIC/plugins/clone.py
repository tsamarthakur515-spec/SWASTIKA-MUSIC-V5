# ---------------------------------------------------------------
# PANDAMUSIC — clone.py (fixed)
# /clone  /myclones  /delclone  /clones  /cloneping
# ---------------------------------------------------------------

print("[clone] loading plugin...", flush=True)

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console
from ..modules.clones import (
    db_list_clones,
    get_running_clones,
    is_bot_token,
    start_clone_client,
    stop_clone_client,
    user_can_clone,
)
from ..modules.formatters import smallcaps

_pending_token = {}


def _is_owner(uid):
    return bool(uid and uid == getattr(console, "OWNER_ID", 0))


def _help_text():
    return (
        "✨ <b>Swastika Clone</b>\n\n"
        f"{smallcaps('apna music bot — full features')}\n\n"
        "<b>Steps:</b>\n"
        "1. @BotFather → /newbot → token copy\n"
        "2. Yahan PM me bhejo:\n"
        "   <code>/clone YOUR_BOT_TOKEN</code>\n\n"
        "<b>Commands:</b>\n"
        "• <code>/clone TOKEN</code> — create\n"
        "• <code>/myclones</code> — list\n"
        "• <code>/delclone BOT_ID</code> — delete\n"
        "• Clone bot pe <code>/cloneping</code> — test\n\n"
        "⚠️ Token sirf <b>private chat</b> me bhejo."
    )


@bot.on_message(
    filters.command(["clone", "clonebot"], ["/", "!", "."]) & filters.incoming,
    group=0,
)
async def clone_cmd(client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    is_private = bool(message.chat and message.chat.type == ChatType.PRIVATE)

    args = message.command or []
    token = args[1].strip() if len(args) >= 2 else ""

    # Full message after /clone  (token might have been split wrong — rare)
    if not token and message.text and len(message.text.split(None, 1)) > 1:
        rest = message.text.split(None, 1)[1].strip()
        if is_bot_token(rest):
            token = rest

    if not token:
        if not is_private:
            return await message.reply_text(
                "🔒 Clone sirf <b>PM</b> me.\nBot ko private message karo → <code>/clone</code>",
                parse_mode=ParseMode.HTML,
            )
        _pending_token[uid] = True
        return await message.reply_text(
            _help_text() + "\n\n➡️ Ab <b>BOT_TOKEN</b> bhej do.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("BotFather", url="https://t.me/BotFather")]]
            ),
            disable_web_page_preview=True,
        )

    if not is_private:
        try:
            await message.delete()
        except Exception:
            pass
        return await message.reply_text(
            "🔒 Token group me mat bhejo — bot ko PM karo.",
            parse_mode=ParseMode.HTML,
        )

    await _do_clone(client, message, token)


@bot.on_message(
    filters.private & filters.text & filters.incoming & ~filters.via_bot,
    group=8,
)
async def clone_token_listener(client, message: Message):
    """Accept raw token message after /clone."""
    if not message.from_user:
        return
    uid = message.from_user.id
    if not _pending_token.get(uid):
        return

    # Ignore commands
    text = (message.text or "").strip()
    if text.startswith(("/", "!", ".")):
        return

    if not is_bot_token(text):
        if ":" in text and len(text) > 25:
            return await message.reply_text(
                "❌ Token format galat.\nExample: <code>123456789:AAHxxxx...</code>",
                parse_mode=ParseMode.HTML,
            )
        return  # normal chat — ignore

    _pending_token.pop(uid, None)
    await _do_clone(client, message, text)


async def _do_clone(client, message: Message, token: str):
    uid = message.from_user.id
    token = token.strip()
    chat_id = message.chat.id

    try:
        await message.delete()
    except Exception:
        pass

    ok, reason = await user_can_clone(uid)
    if not ok:
        return await client.send_message(chat_id, f"❌ {reason}")

    if not is_bot_token(token):
        return await client.send_message(
            chat_id,
            "❌ Invalid token.\nFormat: <code>123456789:AAHxxxx...</code>",
            parse_mode=ParseMode.HTML,
        )

    status = await client.send_message(
        chat_id, "⏳ Token check + clone start ho raha hai..."
    )

    try:
        entry = await start_clone_client(token, uid)
    except Exception as e:
        err = str(e)
        print(f"[clone] start error: {e}", flush=True)
        return await status.edit_text(
            f"❌ Clone fail:\n<code>{err[:500]}</code>\n\n"
            "• Token @BotFather se naya lo\n"
            "• Main bot token mat use karo\n"
            "• API_ID/API_HASH config me sahi hone chahiye",
            parse_mode=ParseMode.HTML,
        )

    uname = entry.get("username") or ""
    mention = f"@{uname}" if uname else f"<code>{entry['bot_id']}</code>"
    await status.edit_text(
        f"✅ <b>Clone ready!</b>\n\n"
        f"🤖 {mention}\n"
        f"📛 {entry.get('name') or 'Clone'}\n"
        f"🆔 <code>{entry['bot_id']}</code>\n\n"
        f"1. Is bot ko group me add karo\n"
        f"2. Admin banao (manage video chats)\n"
        f"3. Clone bot pe <code>/cloneping</code> try karo\n"
        f"4. Phir <code>/play song</code>\n\n"
        f"• /myclones\n"
        f"• /delclone {entry['bot_id']}",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@bot.on_message(
    filters.command(["myclones", "myclone"], ["/", "!", "."]) & filters.incoming,
    group=0,
)
async def myclones_cmd(client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    rows = await db_list_clones(uid)
    running_ids = {
        c["bot_id"] for c in get_running_clones() if c["owner_id"] == uid
    }

    seen = {}
    for r in rows:
        seen[int(r["bot_id"])] = r
    for c in get_running_clones():
        if c["owner_id"] == uid:
            seen[int(c["bot_id"])] = {**seen.get(int(c["bot_id"]), {}), **c}

    if not seen:
        return await message.reply_text(
            "📭 Koi clone nahi.\n<code>/clone</code> se banao.",
            parse_mode=ParseMode.HTML,
        )

    lines = ["🌟 <b>Your Clones</b>\n"]
    for i, (bid, r) in enumerate(seen.items(), 1):
        un = r.get("username") or ""
        tag = f"@{un}" if un else f"<code>{bid}</code>"
        online = "🟢" if bid in running_ids else "🔴"
        lines.append(f"{i}. {online} {tag}\n   🆔 <code>{bid}</code> · /delclone {bid}")
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


@bot.on_message(
    filters.command(["delclone", "removeclone", "rmclone"], ["/", "!", "."])
    & filters.incoming,
    group=0,
)
async def delclone_cmd(client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    args = message.command or []
    if len(args) < 2:
        return await message.reply_text(
            "Usage: <code>/delclone BOT_ID</code>\n<code>/myclones</code> se id lo.",
            parse_mode=ParseMode.HTML,
        )

    raw = args[1].strip().lstrip("@")
    target_id = None
    if raw.isdigit():
        target_id = int(raw)
    else:
        for r in await db_list_clones(None if _is_owner(uid) else uid):
            if (r.get("username") or "").lower() == raw.lower():
                target_id = int(r["bot_id"])
                break
        if target_id is None:
            for c in get_running_clones():
                if (c.get("username") or "").lower() == raw.lower():
                    if _is_owner(uid) or c["owner_id"] == uid:
                        target_id = int(c["bot_id"])
                    break

    if not target_id:
        return await message.reply_text("❌ Clone not found.")

    owner_of = None
    for r in await db_list_clones():
        if int(r["bot_id"]) == target_id:
            owner_of = int(r["owner_id"])
            break
    if owner_of is None:
        for c in get_running_clones():
            if int(c["bot_id"]) == target_id:
                owner_of = int(c["owner_id"])
                break

    if owner_of is None:
        return await message.reply_text("❌ Clone not found.")
    if owner_of != uid and not _is_owner(uid):
        return await message.reply_text("❌ Ye clone tumhara nahi.")

    await stop_clone_client(target_id)
    await message.reply_text(
        f"✅ Clone removed.\n🆔 <code>{target_id}</code>",
        parse_mode=ParseMode.HTML,
    )


@bot.on_message(
    filters.command(["clones", "allclones"], ["/", "!", "."]) & filters.incoming,
    group=0,
)
async def all_clones_cmd(client, message: Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text("❌ Owner only.")

    rows = await db_list_clones()
    running = {c["bot_id"]: c for c in get_running_clones()}
    if not rows and not running:
        return await message.reply_text("📭 No clones.")

    lines = ["👑 <b>All Clones</b>\n"]
    seen = set()
    for r in rows:
        bid = int(r["bot_id"])
        seen.add(bid)
        un = r.get("username") or ""
        tag = f"@{un}" if un else str(bid)
        online = "🟢" if bid in running else "🔴"
        lines.append(
            f"{online} {tag} · owner <code>{r['owner_id']}</code> · <code>{bid}</code>"
        )
    for bid, c in running.items():
        if bid not in seen:
            un = c.get("username") or ""
            tag = f"@{un}" if un else str(bid)
            lines.append(
                f"🟢 {tag} · owner <code>{c['owner_id']}</code> · <code>{bid}</code>"
            )
    await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


print("[clone] plugin loaded OK", flush=True)
