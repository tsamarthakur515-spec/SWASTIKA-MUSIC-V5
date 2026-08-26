"""
PANDAMUSIC — Clone bots manager

Users can /clone with their own BOT_TOKEN.
Clone clients share the same plugins (handlers copied from main bot),
assistants, and PyTgCalls — full feature parity.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

from pyrogram import Client

from .. import bot, console

log = console.logs(__name__)

# bot_id -> {client, token, owner_id, username, name}
_clone_clients: Dict[int, Dict[str, Any]] = {}
_mem_clones: List[Dict[str, Any]] = []  # fallback when DB offline

TOKEN_RE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{20,}$")

# Max clones per non-owner user (override with CLONE_LIMIT env)
def _clone_limit() -> int:
    try:
        from os import getenv

        return max(1, int(getenv("CLONE_LIMIT", "2") or 2))
    except Exception:
        return 2


def _table() -> str:
    p = getattr(console, "TABLE_PREFIX", "pmv2_") or "pmv2_"
    return f"{p}clones"


async def ensure_clone_table() -> bool:
    """Create clones table if DB is available."""
    try:
        from . import database as db

        if not db._ok():
            return False
        t = _table()
        async with db._pool.acquire() as conn:
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {t} (
                    bot_id    BIGINT PRIMARY KEY,
                    owner_id  BIGINT NOT NULL,
                    bot_token TEXT   NOT NULL,
                    username  TEXT,
                    name      TEXT,
                    added_at  TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS {t}_owner_idx ON {t}(owner_id);
                """
            )
        return True
    except Exception as e:
        log.warning(f"clone table: {e}")
        return False


async def db_list_clones(owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
    try:
        from . import database as db

        if not db._ok():
            if owner_id is None:
                return list(_mem_clones)
            return [c for c in _mem_clones if int(c.get("owner_id", 0)) == int(owner_id)]
        t = _table()
        async with db._pool.acquire() as conn:
            if owner_id is None:
                rows = await conn.fetch(
                    f"SELECT bot_id, owner_id, bot_token, username, name FROM {t}"
                )
            else:
                rows = await conn.fetch(
                    f"SELECT bot_id, owner_id, bot_token, username, name FROM {t} WHERE owner_id=$1",
                    int(owner_id),
                )
        return [dict(r) for r in rows]
    except Exception as e:
        log.warning(f"db_list_clones: {e}")
        if owner_id is None:
            return list(_mem_clones)
        return [c for c in _mem_clones if int(c.get("owner_id", 0)) == int(owner_id)]


async def db_save_clone(
    bot_id: int, owner_id: int, bot_token: str, username: str = "", name: str = ""
) -> None:
    entry = {
        "bot_id": int(bot_id),
        "owner_id": int(owner_id),
        "bot_token": bot_token,
        "username": username or "",
        "name": name or "",
    }
    # memory upsert
    _mem_clones[:] = [c for c in _mem_clones if int(c.get("bot_id", 0)) != int(bot_id)]
    _mem_clones.append(entry)
    try:
        from . import database as db

        if not db._ok():
            return
        t = _table()
        async with db._pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {t}(bot_id, owner_id, bot_token, username, name)
                VALUES($1, $2, $3, $4, $5)
                ON CONFLICT(bot_id) DO UPDATE SET
                    owner_id=EXCLUDED.owner_id,
                    bot_token=EXCLUDED.bot_token,
                    username=EXCLUDED.username,
                    name=EXCLUDED.name
                """,
                int(bot_id),
                int(owner_id),
                bot_token,
                username or "",
                name or "",
            )
    except Exception as e:
        log.warning(f"db_save_clone: {e}")


async def db_delete_clone(bot_id: int) -> bool:
    global _mem_clones
    before = len(_mem_clones)
    _mem_clones = [c for c in _mem_clones if int(c.get("bot_id", 0)) != int(bot_id)]
    ok = len(_mem_clones) < before
    try:
        from . import database as db

        if db._ok():
            t = _table()
            async with db._pool.acquire() as conn:
                r = await conn.execute(
                    f"DELETE FROM {t} WHERE bot_id=$1", int(bot_id)
                )
                ok = True
    except Exception as e:
        log.warning(f"db_delete_clone: {e}")
    return ok


def _copy_handlers(source: Client, target: Client) -> int:
    """Copy all dispatcher handlers from main bot onto clone client."""
    count = 0
    try:
        groups = getattr(source, "dispatcher", None)
        if groups is None:
            return 0
        for group_id, handlers in list(source.dispatcher.groups.items()):
            for handler in list(handlers):
                try:
                    target.add_handler(handler, group_id)
                    count += 1
                except Exception as e:
                    log.warning(f"clone handler copy skip: {e}")
    except Exception as e:
        log.error(f"_copy_handlers failed: {e}")
    return count


async def validate_bot_token(token: str) -> Optional[Dict[str, Any]]:
    """Start temp client, get_me, stop — returns me dict or None."""
    token = (token or "").strip()
    if not TOKEN_RE.match(token):
        return None
    name = f"clone_check_{token.split(':', 1)[0]}"
    client = Client(
        name,
        api_id=console.API_ID,
        api_hash=console.API_HASH,
        bot_token=token,
        in_memory=True,
    )
    try:
        await client.start()
        me = await client.get_me()
        info = {
            "id": me.id,
            "username": me.username or "",
            "name": ((me.first_name or "") + (" " + me.last_name if me.last_name else "")).strip()
            or "CloneBot",
            "token": token,
        }
        await client.stop()
        return info
    except Exception as e:
        log.warning(f"validate_bot_token failed: {e}")
        try:
            await client.stop()
        except Exception:
            pass
        return None


async def start_clone_client(
    token: str, owner_id: int, bot_id: int = 0, username: str = "", name: str = ""
) -> Dict[str, Any]:
    """Start a clone Client, copy handlers from main bot, register in memory."""
    if bot_id and bot_id in _clone_clients:
        return _clone_clients[bot_id]

    # Avoid cloning the main bot token
    if console.BOT_TOKEN and token.strip() == str(console.BOT_TOKEN).strip():
        raise RuntimeError("Ye main bot ka token hai — clone nahi banega.")

    session = f"PANDAMUSIC_Clone_{token.split(':', 1)[0]}"
    client = Client(
        session,
        api_id=console.API_ID,
        api_hash=console.API_HASH,
        bot_token=token,
        in_memory=True,
    )
    await client.start()
    me = await client.get_me()
    bot_id = int(me.id)
    username = me.username or username or ""
    name = (
        ((me.first_name or "") + (" " + me.last_name if me.last_name else "")).strip()
        or name
        or "CloneBot"
    )

    if bot_id in _clone_clients:
        try:
            await client.stop()
        except Exception:
            pass
        return _clone_clients[bot_id]

    n = _copy_handlers(bot, client)
    log.info(f"Clone @{username} ({bot_id}) started — {n} handlers copied")

    entry = {
        "client": client,
        "token": token,
        "owner_id": int(owner_id),
        "bot_id": bot_id,
        "username": username,
        "name": name,
    }
    _clone_clients[bot_id] = entry
    await db_save_clone(bot_id, owner_id, token, username, name)
    return entry


async def stop_clone_client(bot_id: int) -> bool:
    entry = _clone_clients.pop(int(bot_id), None)
    if not entry:
        await db_delete_clone(int(bot_id))
        return False
    client = entry.get("client")
    try:
        if client:
            await client.stop()
    except Exception as e:
        log.warning(f"stop clone {bot_id}: {e}")
    await db_delete_clone(int(bot_id))
    return True


def get_running_clones() -> List[Dict[str, Any]]:
    return [
        {
            "bot_id": v["bot_id"],
            "owner_id": v["owner_id"],
            "username": v.get("username") or "",
            "name": v.get("name") or "",
        }
        for v in _clone_clients.values()
    ]


async def start_all_saved_clones() -> int:
    """Called on boot after main bot + plugins loaded."""
    await ensure_clone_table()
    rows = await db_list_clones()
    started = 0
    for row in rows:
        token = row.get("bot_token") or ""
        owner_id = int(row.get("owner_id") or 0)
        if not token or not owner_id:
            continue
        try:
            await start_clone_client(
                token,
                owner_id,
                bot_id=int(row.get("bot_id") or 0),
                username=row.get("username") or "",
                name=row.get("name") or "",
            )
            started += 1
            await asyncio.sleep(0.4)
        except Exception as e:
            log.error(f"Failed to start saved clone {row.get('bot_id')}: {e}")
    log.info(f"Clones online: {started}")
    return started


async def user_can_clone(owner_id: int) -> tuple[bool, str]:
    owner_id = int(owner_id)
    if owner_id == getattr(console, "OWNER_ID", 0):
        return True, ""
    rows = await db_list_clones(owner_id)
    # also count running
    running = sum(1 for c in _clone_clients.values() if int(c["owner_id"]) == owner_id)
    n = max(len(rows), running)
    limit = _clone_limit()
    if n >= limit:
        return False, f"Limit full — max {limit} clone(s) per user. /delclone se purana hatao."
    return True, ""
