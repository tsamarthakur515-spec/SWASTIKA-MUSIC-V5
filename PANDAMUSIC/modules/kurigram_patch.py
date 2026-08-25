"""
Fix broken kurigram installs missing raw.types.KeyboardButtonCallback / KeyboardButtonUrl.
Must be imported BEFORE bot handlers process updates.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def apply() -> None:
    try:
        from pyrogram import raw
        from pyrogram.types.bots_and_keyboards import inline_keyboard_button as ikb
        from pyrogram.types import InlineKeyboardButton
        from pyrogram import enums, types
    except Exception as e:
        log.warning("kurigram_patch: import failed: %s", e)
        return

    # --- Inject missing TL type classes if absent ---
    try:
        from pyrogram.raw.core import TLObject
    except Exception:
        TLObject = object  # type: ignore

    def _ensure_type(name: str, qual: str, fields: tuple):
        if hasattr(raw.types, name):
            return
        attrs = {"QUALNAME": qual}

        def __init__(self, **kwargs):
            for k in fields:
                setattr(self, k, kwargs.get(k))

        attrs["__init__"] = __init__
        cls = type(name, (TLObject,), attrs)
        setattr(raw.types, name, cls)
        log.info("kurigram_patch: injected raw.types.%s", name)

    _ensure_type(
        "KeyboardButtonCallback",
        "types.KeyboardButtonCallback",
        ("text", "data", "requires_password", "style"),
    )
    _ensure_type(
        "KeyboardButtonUrl",
        "types.KeyboardButtonUrl",
        ("text", "url", "style"),
    )
    _ensure_type(
        "KeyboardButton",
        "types.KeyboardButton",
        ("text", "style"),
    )

    # --- Patch InlineKeyboardButton.read (duck-typed, never AttributeError) ---
    _orig_read = ikb.InlineKeyboardButton.read

    @staticmethod
    def _safe_read(b):  # type: ignore
        try:
            return _orig_read(b)
        except AttributeError:
            pass
        except Exception:
            pass

        # Duck-type parse
        text = getattr(b, "text", "") or ""
        style = None
        icon = None
        raw_style = getattr(b, "style", None)
        if raw_style is not None:
            try:
                if getattr(raw_style, "bg_primary", False):
                    style = enums.ButtonStyle.PRIMARY
                elif getattr(raw_style, "bg_success", False):
                    style = enums.ButtonStyle.SUCCESS
                elif getattr(raw_style, "bg_danger", False):
                    style = enums.ButtonStyle.DANGER
                if getattr(raw_style, "icon", None):
                    icon = str(raw_style.icon)
            except Exception:
                pass

        kw = {}
        if style is not None:
            kw["style"] = style
        if icon:
            kw["icon_custom_emoji_id"] = icon

        data = getattr(b, "data", None)
        url = getattr(b, "url", None)
        if data is not None:
            if isinstance(data, bytes):
                try:
                    data = data.decode()
                except Exception:
                    data = data.decode("utf-8", errors="ignore")
            try:
                return InlineKeyboardButton(
                    text,
                    callback_data=data,
                    requires_password=getattr(b, "requires_password", None),
                    **kw,
                )
            except TypeError:
                return InlineKeyboardButton(text, callback_data=data)
        if url is not None:
            try:
                return InlineKeyboardButton(text, url=url, **kw)
            except TypeError:
                return InlineKeyboardButton(text, url=url)

        try:
            return InlineKeyboardButton(text, **kw)
        except TypeError:
            return InlineKeyboardButton(text)

    ikb.InlineKeyboardButton.read = _safe_read
    types.InlineKeyboardButton.read = _safe_read  # type: ignore
    log.info("kurigram_patch: InlineKeyboardButton.read patched")

    # --- Patch write to avoid KeyboardButtonUrl/Callback AttributeError on send ---
    _orig_write = ikb.InlineKeyboardButton.write

    async def _safe_write(self, client):  # type: ignore
        try:
            return await _orig_write(self, client)
        except AttributeError as e:
            log.warning("kurigram_patch write fallback: %s", e)
            # Build minimal objects if types exist after inject
            style = None
            try:
                if getattr(self, "style", None) or getattr(self, "icon_custom_emoji_id", None):
                    style = raw.types.KeyboardButtonStyle(
                        bg_primary=str(getattr(self.style, "name", self.style)).lower()
                        == "primary"
                        if self.style
                        else False,
                        bg_success=str(getattr(self.style, "name", self.style)).lower()
                        == "success"
                        if self.style
                        else False,
                        bg_danger=str(getattr(self.style, "name", self.style)).lower()
                        == "danger"
                        if self.style
                        else False,
                        icon=int(self.icon_custom_emoji_id)
                        if self.icon_custom_emoji_id
                        else None,
                    )
            except Exception:
                style = None

            if self.callback_data is not None:
                data = self.callback_data
                if isinstance(data, str):
                    data = data.encode()
                try:
                    return raw.types.KeyboardButtonCallback(
                        text=self.text,
                        data=data,
                        requires_password=self.requires_password or None,
                        style=style,
                    )
                except TypeError:
                    return raw.types.KeyboardButtonCallback(
                        text=self.text, data=data
                    )
            if self.url is not None:
                try:
                    return raw.types.KeyboardButtonUrl(
                        text=self.text, url=self.url, style=style
                    )
                except TypeError:
                    return raw.types.KeyboardButtonUrl(text=self.text, url=self.url)
            raise

    ikb.InlineKeyboardButton.write = _safe_write
    types.InlineKeyboardButton.write = _safe_write  # type: ignore
    log.info("kurigram_patch: InlineKeyboardButton.write patched")


# Auto-apply on import
try:
    apply()
except Exception as _e:
    logging.getLogger(__name__).error("kurigram_patch apply failed: %s", _e)
