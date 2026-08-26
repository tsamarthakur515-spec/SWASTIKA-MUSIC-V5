# ---------------------------------------------------------------
# PANDAMUSIC — clone.py
# regex group=-5 + Bot API fallback (kurigram send often broken)
# ---------------------------------------------------------------

print("[clone] loading plugin...", flush=True)

import json
import re
import traceback

import httpx
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message

from .. import bot, console

_pending_token = {}
TOKEN_FIND = re.compile(r"(\d{5,15}:[A-Za-z0-9_-]{20,100})")
CLONE_CMD_RE = re.compile(r"(?i)^/(clone|clonebot)(@\w+)?(?:\s|$)")


def _is_owner(uid):
    return bool(uid and uid == getattr(console, "OWNER_ID", 0))


def _normalize_token(raw: str) -> str:
    return re.sub(r"\s+", "", (raw or "").strip())


def _looks_like_token(t: str) -> bool:
    t = _normalize_token(t)
    if not t or ":" not in t:
        return False
    left, right = t.split(":", 1)
    return left.isdigit() and 5 <= len(left) <= 15 and len(right) >= 20


def _extract_token(message: Message) -> str:
    text = (message.text or message.caption or "") or ""
    if not text.strip():
        return ""

    parts = text.strip().split(None, 1)
    if len(parts) >= 2:
        joined = _normalize_token(parts[1])
        if _looks_like_token(joined):
            return joined
        m = TOKEN_FIND.search(joined)
        if m:
            return m.group(1)

    compact = _normalize_token(text)
    m = TOKEN_FIND.search(compact)
    if m:
        return m.group(1)

    try:
        cmd = list(getattr(message, "command", None) or [])
        if len(cmd) >= 2:
            joined = _normalize_token("".join(cmd[1:]))
            if _looks_like_token(joined):
                return joined
            m = TOKEN_FIND.search(joined)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


async def _api_post(method: str, payload: dict):
    token = getattr(console, "BOT_TOKEN", None)
    if not token:
        print("[clone] BOT_TOKEN missing", flush=True)
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, data=payload)
            data = r.json()
            if not data.get("ok"):
                print(f"[clone] bot_api {method} fail: {data}", flush=True)
                return None
            return data.get("result")
    except Exception as e:
        print(f"[clone] bot_api {method} error: {e}", flush=True)
        return None


async def _api_send(chat_id, text: str):
    """Send via Bot API HTTP — returns message_id or None."""
    result = await _api_post(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
    )
    if result:
        return result.get("message_id")
    result = await _api_post(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": _strip_html(text)[:4096],
            "disable_web_page_preview": "true",
        },
    )
    return result.get("message_id") if result else None


async def _api_edit(chat_id, message_id, text: str) -> bool:
    if not message_id:
        return False
    r = await _api_post(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
    )
    if r is not None:
        return True
    r = await _api_post(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": _strip_html(text)[:4096],
            "disable_web_page_preview": "true",
        },
    )
    return r is not None


class _Status:
    """Minimal status holder for pyrogram msg OR bot-api message_id."""

    def __init__(self, chat_id, msg=None, message_id=None):
        self.chat_id = chat_id
        self.msg = msg
        self.message_id = message_id or (getattr(msg, "id", None) if msg else None)


async def _reply(message, text) -> _Status | None:
    chat_id = message.chat.id
    # 1) pyrogram
    try:
        msg = await message.reply_text(text, parse_mode=ParseMode.HTML)
        return _Status(chat_id, msg=msg)
    except Exception as e:
        print(f"[clone] pyrogram reply fail: {e}", flush=True)
    try:
        msg = await message.reply_text(_strip_html(text))
        return _Status(chat_id, msg=msg)
    except Exception as e:
        print(f"[clone] pyrogram plain reply fail: {e}", flush=True)
    # 2) Bot API HTTP
    mid = await _api_send(chat_id, text)
    if mid:
        print(f"[clone] bot_api send ok mid={mid}", flush=True)
        return _Status(chat_id, message_id=mid)
    print("[clone] ALL send paths failed", flush=True)
    return None


async def _edit(status: _Status | None, text: str):
    if not status:
        return None
    if status.msg:
        try:
            return await status.msg.edit_text(text, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"[clone] pyrogram edit fail: {e}", flush=True)
            try:
                return await status.msg.edit_text(_strip_html(text))
            except Exception:
                pass
    if status.message_id:
        ok = await _api_edit(status.chat_id, status.message_id, text)
        if ok:
            return status
    # last resort: new message
    mid = await _api_send(status.chat_id, text)
    if mid:
        status.message_id = mid
        status.msg = None
    return status


async def _delete(message):
    try:
        await message.delete()
    except Exception:
        pass


@bot.on_message(
    filters.regex(r"(?i)^/(clone|clonebot)(@\w+)?(?:\s|$)") & filters.incoming,
    group=-5,
)
async def clone_cmd(client, message: Message):
    uid = getattr(message.from_user, "id", None)
    chat_id = message.chat.id if message.chat else None
    print(
        f"[clone] CMD HIT uid={uid} chat={chat_id} text={((message.text or '')[:120])!r}",
        flush=True,
    )

    try:
        if not message.from_user:
            return await _reply(message, "❌ User not found.")

        chat_type = getattr(message.chat, "type", None)
        is_private = chat_type == ChatType.PRIVATE or str(chat_type).lower() in (
            "private",
            "chattype.private",
        )
        if not is_private:
            return await _reply(
                message,
                "🔒 Clone sirf <b>private chat</b> me chalta hai.\nBot ko DM karke /clone bhejo.",
            )

        token = _extract_token(message)
        print(f"[clone] token_len={len(token)} valid={_looks_like_token(token)}", flush=True)

        if not token:
            _pending_token[uid] = True
            return await _reply(
                message,
                "✨ <b>Swastika Clone</b>\n\n"
                "Usage (token <b>ek line</b> me):\n"
                "<code>/clone 123456:AAHxxxx</code>\n\n"
                "Ya /clone ke baad agli message me sirf token bhejo.\n\n"
                "• /myclones — list\n"
                "• /delclone ID — delete",
            )

        await _do_clone(client, message, token)
    except Exception as e:
        print(f"[clone] clone_cmd ERROR: {e}", flush=True)
        traceback.print_exc()
        await _reply(message, f"❌ Clone error:\n<code>{str(e)[:400]}</code>")


@bot.on_message(
    filters.private & filters.text & filters.incoming,
    group=-4,
)
async def clone_token_paste(client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    if not _pending_token.get(uid):
        return

    text_raw = message.text or ""
    if CLONE_CMD_RE.match(text_raw.strip()):
        return

    text = _normalize_token(text_raw)
    m = TOKEN_FIND.search(text)
    token = m.group(1) if m else text
    if not _looks_like_token(token):
        if ":" in text:
            return await _reply(
                message,
                "❌ Token incomplete / galat.\nPoora token <b>ek line</b> me bhejo.",
            )
        return

    _pending_token.pop(uid, None)
    print(f"[clone] paste from {uid}", flush=True)
    await _do_clone(client, message, token)


async def _do_clone(client, message: Message, token: str):
    uid = message.from_user.id
    token = _normalize_token(token)

    status = await _reply(message, "⏳ <b>cloning....</b>")
    await _delete(message)

    if not _looks_like_token(token):
        return await _edit(
            status,
            "❌ Invalid token.\nExample: <code>123456789:AAHxxxx</code>",
        )

    try:
        from ..modules.clones import is_bot_token, start_clone_client, user_can_clone
    except Exception as e:
        print(f"[clone] import clones fail: {e}", flush=True)
        traceback.print_exc()
        return await _edit(
            status,
            "❌ Clone module load nahi hua.\nPanel se <b>Rebuild</b> karo.",
        )

    if not is_bot_token(token):
        return await _edit(
            status,
            "❌ Invalid token format.\n<code>123456789:AAHxxxx</code>",
        )

    ok, reason = await user_can_clone(uid)
    if not ok:
        return await _edit(status, f"❌ {reason}")

    try:
        entry = await start_clone_client(token, uid)
    except Exception as e:
        print(f"[clone] start fail: {e}", flush=True)
        traceback.print_exc()
        return await _edit(
            status,
            f"❌ Clone fail:\n<code>{str(e)[:450]}</code>\n\n"
            "• @BotFather se naya token\n"
            "• Main bot token mat use karo\n"
            "• Token ek line me bhejo",
        )

    uname = (entry.get("username") or "").strip()
    bot_id = entry.get("bot_id")
    name = entry.get("name") or "Clone"
    who = f"@{uname}" if uname else f"<code>{bot_id}</code>"

    text = (
        f"✅ <b>Bot Cloned!</b>\n\n"
        f"🤖 Username: <b>{who}</b>\n"
        f"📛 Name: {name}\n"
        f"🆔 <code>{bot_id}</code>\n\n"
        f"Next:\n"
        f"1. {who} ko group me add karo\n"
        f"2. Admin + manage video chats\n"
        f"3. Clone pe /cloneping\n"
        f"4. /play song\n\n"
        f"/myclones · /delclone {bot_id}"
    )
    await _edit(status, text)


@bot.on_message(
    filters.regex(r"(?i)^/(myclones|myclone)(@\w+)?(?:\s|$)") & filters.incoming,
    group=-5,
)
async def myclones_cmd(client, message: Message):
    try:
        from ..modules.clones import db_list_clones, get_running_clones

        if not message.from_user:
            return
        uid = message.from_user.id
        rows = await db_list_clones(uid)
        running_ids = {c["bot_id"] for c in get_running_clones() if c["owner_id"] == uid}
        seen = {}
        for r in rows:
            seen[int(r["bot_id"])] = r
        for c in get_running_clones():
            if c["owner_id"] == uid:
                seen[int(c["bot_id"])] = {**seen.get(int(c["bot_id"]), {}), **c}
        if not seen:
            return await _reply(message, "📭 Koi clone nahi.\n<code>/clone TOKEN</code>")
        lines = ["🌟 <b>Your Clones</b>\n"]
        for i, (bid, r) in enumerate(seen.items(), 1):
            un = r.get("username") or ""
            tag = f"@{un}" if un else f"<code>{bid}</code>"
            online = "🟢" if bid in running_ids else "🔴"
            lines.append(f"{i}. {online} {tag}\n   /delclone {bid}")
        await _reply(message, "\n".join(lines))
    except Exception as e:
        await _reply(message, f"❌ {e}")


@bot.on_message(
    filters.regex(r"(?i)^/(delclone|removeclone|rmclone)(@\w+)?(?:\s|$)") & filters.incoming,
    group=-5,
)
async def delclone_cmd(client, message: Message):
    try:
        from ..modules.clones import db_list_clones, get_running_clones, stop_clone_client

        if not message.from_user:
            return
        uid = message.from_user.id
        parts = (message.text or "").strip().split()
        if len(parts) < 2:
            return await _reply(message, "Usage: <code>/delclone BOT_ID</code>")
        raw = parts[1].strip().lstrip("@")
        if not raw.isdigit():
            return await _reply(message, "❌ Numeric BOT_ID do.")
        target_id = int(raw)
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
            return await _reply(message, "❌ Clone not found.")
        if owner_of != uid and not _is_owner(uid):
            return await _reply(message, "❌ Ye clone tumhara nahi.")
        await stop_clone_client(target_id)
        await _reply(message, f"✅ Clone removed.\n🆔 <code>{target_id}</code>")
    except Exception as e:
        await _reply(message, f"❌ {e}")


@bot.on_message(
    filters.regex(r"(?i)^/(clones|allclones)(@\w+)?(?:\s|$)") & filters.incoming,
    group=-5,
)
async def all_clones_cmd(client, message: Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return await _reply(message, "❌ Owner only.")
    try:
        from ..modules.clones import db_list_clones, get_running_clones

        rows = await db_list_clones()
        running = {c["bot_id"]: c for c in get_running_clones()}
        if not rows and not running:
            return await _reply(message, "📭 No clones.")
        lines = ["👑 <b>All Clones</b>\n"]
        seen = set()
        for r in rows:
            bid = int(r["bot_id"])
            seen.add(bid)
            un = r.get("username") or ""
            tag = f"@{un}" if un else str(bid)
            online = "🟢" if bid in running else "🔴"
            lines.append(f"{online} {tag} · owner <code>{r['owner_id']}</code>")
        for bid, c in running.items():
            if bid not in seen:
                un = c.get("username") or ""
                tag = f"@{un}" if un else str(bid)
                lines.append(f"🟢 {tag} · owner <code>{c['owner_id']}</code>")
        await _reply(message, "\n".join(lines))
    except Exception as e:
        await _reply(message, f"❌ {e}")


print("[clone] plugin loaded OK — handlers registered (group=-5 + bot_api)", flush=True)
