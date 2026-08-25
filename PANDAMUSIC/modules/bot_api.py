"""
Telegram Bot API helpers — bypass broken kurigram KeyboardButtonUrl / Callback write().
Use when pyrogram reply_markup.write fails.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import httpx

from .. import console


def _btn_to_api(btn) -> dict:
    d: dict[str, Any] = {"text": getattr(btn, "text", "") or ""}
    if getattr(btn, "url", None):
        d["url"] = btn.url
    if getattr(btn, "callback_data", None):
        data = btn.callback_data
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="ignore")
        d["callback_data"] = str(data)
    if getattr(btn, "icon_custom_emoji_id", None):
        d["icon_custom_emoji_id"] = str(btn.icon_custom_emoji_id)
    style = getattr(btn, "style", None)
    if style is not None:
        name = getattr(style, "name", None) or str(style)
        name = str(name).lower()
        if name in ("primary", "success", "danger"):
            d["style"] = name
    return d


def markup_to_api(markup) -> Optional[dict]:
    if markup is None:
        return None
    rows = []
    for row in getattr(markup, "inline_keyboard", []) or []:
        rows.append([_btn_to_api(b) for b in row])
    return {"inline_keyboard": rows}


async def bot_api_send_photo(
    chat_id: int,
    photo: str,
    caption: str = "",
    reply_markup=None,
    parse_mode: str = "HTML",
) -> bool:
    token = getattr(console, "BOT_TOKEN", None)
    if not token:
        print("[bot_api] BOT_TOKEN missing", flush=True)
        return False

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "photo": photo,
        "caption": caption or "",
        "parse_mode": parse_mode,
    }
    api_markup = markup_to_api(reply_markup)
    if api_markup:
        payload["reply_markup"] = json.dumps(api_markup)

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, data=payload)
            data = r.json()
            if not data.get("ok"):
                print(f"[bot_api] sendPhoto fail: {data}", flush=True)
                return False
            return True
    except Exception as e:
        print(f"[bot_api] sendPhoto error: {e}", flush=True)
        return False


async def bot_api_send_message(
    chat_id: int,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> bool:
    token = getattr(console, "BOT_TOKEN", None)
    if not token:
        return False

    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }
    api_markup = markup_to_api(reply_markup)
    if api_markup:
        payload["reply_markup"] = json.dumps(api_markup)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, data=payload)
            data = r.json()
            if not data.get("ok"):
                print(f"[bot_api] sendMessage fail: {data}", flush=True)
                return False
            return True
    except Exception as e:
        print(f"[bot_api] sendMessage error: {e}", flush=True)
        return False
