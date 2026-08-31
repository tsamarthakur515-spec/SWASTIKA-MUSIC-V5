import asyncio
import os
import sys
import runpy
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# CRITICAL HOTFIXES — MUST run BEFORE any PANDAMUSIC / pytgcalls import
# ============================================================

# 1. Event loop for Python 3.10+
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# 2. GroupcallForbidden + crypto_executor for kurigram / py-tgcalls
try:
    import pyrogram
    import pyrogram.errors as _pe

    # GroupcallForbidden
    if not hasattr(_pe, "GroupcallForbidden"):
        if hasattr(_pe, "GroupCallForbidden"):
            _pe.GroupcallForbidden = _pe.GroupCallForbidden  # type: ignore
        else:

            class GroupcallForbidden(Exception):
                pass

            _pe.GroupcallForbidden = GroupcallForbidden  # type: ignore

    # crypto_executor (removed in some kurigram versions)
    if not hasattr(pyrogram, "crypto_executor"):
        pyrogram.crypto_executor = ThreadPoolExecutor(
            1, thread_name_prefix="CryptoWorker"
        )
except Exception:
    pass
# ============================================================

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
