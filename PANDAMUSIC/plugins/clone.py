# ---------------------------------------------------------------
# PANDAMUSIC — clone.py
# /clone  /myclones  /delclone  /clones
# Users clone this bot with their BOT_TOKEN (all features shared)
# ---------------------------------------------------------------

print("[clone] loading plugin...", flush=True)

import re

from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import bot, console
from ..modules.clones import (
    TOKEN_RE,
    db_list_clones,
    get_running_clones,
    start_clone_client,
    stop_clone_client,
    user_can_clone,
    validate_bot_token,
)
from ..modules.custom_emojis import E, tg_emoji
from ..modules.formatters import smallcaps

# Waiting for token in PM: user_id -> True
_pending_token: dict[int, bool] = {}


def _is_owner(uid: int) -> bool:
    return bool(uid and uid == getattr(console, "OWNER_ID", 0))


def _clone_help_text() -> str:
    return (
        f"{tg_emoji(E.SPARKLES, '✨')} <b>𝗦𝘄𝗮𝘀𝘁𝗶𝗸𝗮 𝗖𝗹𝗼𝗻𝗲</b>\n\n"
        f"{smallcaps('apna music bot banao — saari features ke sath')}\n\n"
        f"<b>{smallcaps('kya milta hai')}:</b>\n"
        f"• music / vplay / pause / skip / end\n"
        f"• moderation, locks, welcome, tagall\n"
        f"• chatbot, games, stats, broadcast\n"
        f"• same assistants + voice chat quality\n\n"
        f"<b>{smallcaps('kaise clone kare')}:</b>\n"
        f"1. @BotFather se naya bot banao → /newbot\n"
        f"2. BotFather se <b>BOT_TOKEN</b> copy karo\n"
        f"3. Yahan PM me bhejo:\n"
        f"   <code>/clone 123456:ABC-DEF...</code>\n"
        f"   ya /clone dabake token alag message me bhejo\n\n"
        f"<b>{smallcaps('commands')}:</b>\n"
        f"• <code>/clone</code> — help / start\n"
        f"• <code>/clone TOKEN</code> — clone create\n"
        f"• <code>/myclones</code> — mere clones\n"
        f"• <code>/delclone BOT_ID</code> — clone delete\n\n"
        f"⚠️ Token <b>sirf private chat</b> me bhejo. Group me mat bhejo."
    )


@bot.on_message(
    filters.command(["clone", "clonebot"], ["/", "!", "."]) & filters.incoming,
    group=0,
)
async def clone_cmd(client, message: Message):
    if not message.from_user:
        return

    uid = message.from_user.id
    is_private = message.chat and message.chat.type == ChatType.PRIVATE

    # Token in command args
    args = message.command or []
    token = ""
    if len(args) >= 2:
        token = args[1].strip()

    if not token:
        if not is_private:
            return await message.reply_text(
                "🔒 Clone setup sirf <b>private chat</b> me hota hai.\n"
                "Bot ko PM karo aur <code>/clone</code> bhejo.",
                parse_mode=ParseMode.HTML,
            )
        _pending_token[uid] = True
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "BotFather ↗", url="https://t.me/BotFather"
                    )
                ]
            ]
        )
        return await message.reply_text(
            _clone_help_text()
            + "\n\n➡️ Ab apna <b>BOT_TOKEN</b> is chat me bhej do.",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
            disable_web_page_preview=True,
        )

    if not is_private:
        try:
            await message.delete()
        except Exception:
            pass
        return await message.reply_text(
            "🔒 Security: token group me mat bhejo. Bot ko PM karo.",
            parse_mode=ParseMode.HTML,
        )

    await _do_clone(client, message, token)


@bot.on_message(
    filters.private & filters.text & filters.incoming & ~filters.command(
        ["clone", "clonebot", "myclones", "delclone", "clones", "start", "help"],
        ["/", "!", "."],
    ),
    group=5,
)
async def clone_token_listener(client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    if not _pending_token.get(uid):
        return
    text = (message.text or "").strip()
    if not TOKEN_RE.match(text):
        # might be normal chat — ignore if doesn't look like token
        if ":" not in text or len(text) < 30:
            return
        return await message.reply_text(
            "❌ Invalid token format.\n"
            "Example: <code>123456789:AAHxxxx...</code>",
            parse_mode=ParseMode.HTML,
        )
    _pending_token.pop(uid, None)
    await _do_clone(client, message, text)


async def _do_clone(client, message: Message, token: str):
    uid = message.from_user.id
    token = token.strip()

    # Delete message that contains the token
    try:
        await message.delete()
    except Exception:
        pass

    ok, reason = await user_can_clone(uid)
    if not ok:
        return await client.send_message(
            message.chat.id, f"❌ {reason}", parse_mode=ParseMode.HTML
        )

    status = await client.send_message(
        message.chat.id,
        f"{tg_emoji(E.LOADER, '⏳')} {smallcaps('token check ho raha hai...')}",
        parse_mode=ParseMode.HTML,
    )

    info = await validate_bot_token(token)
    if not info:
        return await status.edit_text(
            "❌ Invalid / expired bot token.\n"
            "@BotFather se naya token lo aur dubara try karo.",
            parse_mode=ParseMode.HTML,
        )

    # Already running?
    running = {c["bot_id"]: c for c in get_running_clones()}
    if info["id"] in running:
        return await status.edit_text(
            f"⚠️ Ye bot pehle se online hai.\n"
            f"🤖 @{info['username'] or info['id']}\n"
            f"🆔 <code>{info['id']}</code>",
            parse_mode=ParseMode.HTML,
        )

    await status.edit_text(
        f"{tg_emoji(E.LOADER, '⏳')} {smallcaps('clone start ho raha hai...')}",
        parse_mode=ParseMode.HTML,
    )

    try:
        entry = await start_clone_client(
            token,
            uid,
            bot_id=info["id"],
            username=info.get("username") or "",
            name=info.get("name") or "",
        )
    except Exception as e:
        return await status.edit_text(
            f"❌ Clone start fail:\n<code>{e}</code>",
            parse_mode=ParseMode.HTML,
        )

    uname = entry.get("username") or ""
    mention = f"@{uname}" if uname else f"<code>{entry['bot_id']}</code>"
    await status.edit_text(
        f"{tg_emoji(E.CHECK, '✅')} <b>Clone ready!</b>\n\n"
        f"🤖 Bot: {mention}\n"
        f"📛 Name: <b>{entry.get('name') or 'Clone'}</b>\n"
        f"🆔 <code>{entry['bot_id']}</code>\n\n"
        f"{smallcaps('ab is bot ko group me add karo (admin + invite + manage video chats)')}\n"
        f"{smallcaps('saari features main bot jaisi chalengi.')}\n\n"
        f"• /myclones — list\n"
        f"• /delclone {entry['bot_id']} — delete",
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
    running = {c["bot_id"] for c in get_running_clones() if c["owner_id"] == uid}

    if not rows and not running:
        return await message.reply_text(
            f"📭 {smallcaps('abhi koi clone nahi.')}\n"
            f"<code>/clone</code> se naya banao.",
            parse_mode=ParseMode.HTML,
        )

    # merge by bot_id
    seen = {}
    for r in rows:
        seen[int(r["bot_id"])] = r
    for c in get_running_clones():
        if c["owner_id"] == uid:
            seen[int(c["bot_id"])] = {**seen.get(int(c["bot_id"]), {}), **c}

    lines = [f"{tg_emoji(E.STAR, '🌟')} <b>Your Clones</b>\n"]
    for i, (bid, r) in enumerate(seen.items(), 1):
        un = r.get("username") or ""
        tag = f"@{un}" if un else f"<code>{bid}</code>"
        online = "🟢" if bid in running or bid in {x['bot_id'] for x in get_running_clones()} else "🔴"
        lines.append(
            f"{i}. {online} {tag}\n"
            f"   🆔 <code>{bid}</code> · /delclone {bid}"
        )
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
            "<b>Usage:</b> <code>/delclone BOT_ID</code>\n"
            "Apna bot id <code>/myclones</code> se dekho.",
            parse_mode=ParseMode.HTML,
        )

    raw = args[1].strip().lstrip("@")
    target_id = None
    if raw.isdigit():
        target_id = int(raw)
    else:
        # match username from list
        rows = await db_list_clones(None if _is_owner(uid) else uid)
        for r in rows:
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

    # ownership check
    rows = await db_list_clones()
    owner_of = None
    for r in rows:
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
        return await message.reply_text("❌ Ye clone tumhara nahi hai.")

    await stop_clone_client(target_id)
    await message.reply_text(
        f"✅ Clone stopped & removed.\n🆔 <code>{target_id}</code>",
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
