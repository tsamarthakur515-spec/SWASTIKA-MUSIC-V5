import asyncio
import os
import sys
import runpy

# ============================================================
# CRITICAL HOTFIX — MUST run BEFORE any PANDAMUSIC / pytgcalls import
# py-tgcalls / basiccalls does: from pyrogram.errors import GroupcallForbidden
# but kurigram/pyrogram sometimes doesn't export it → ImportError
# ============================================================
try:
    import pyrogram.errors as _pe

    if not hasattr(_pe, "GroupcallForbidden"):
        if hasattr(_pe, "GroupCallForbidden"):
            _pe.GroupcallForbidden = _pe.GroupCallForbidden  # type: ignore
        else:

            class GroupcallForbidden(Exception):
                """The group call has already ended / is forbidden."""

                pass

            _pe.GroupcallForbidden = GroupcallForbidden  # type: ignore
except Exception:
    pass
# ============================================================

# Python 3.10+ / 3.14 fix: create event loop BEFORE any pyrogram/kurigram import
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Root directory set karo
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PANDAMUSIC package start
if __name__ == "__main__":
    try:
        runpy.run_module("PANDAMUSIC", run_name="__main__", alter_sys=True)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Failed to start bot: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
