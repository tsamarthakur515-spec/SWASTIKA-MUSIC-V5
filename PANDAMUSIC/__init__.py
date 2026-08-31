from .console import sudoers
from .modules.helpers import cdx, cdz, rgx

# Clients are created lazily to avoid "Future attached to a different loop"
bot = None
app = None
call = None


def init_clients():
    """Must be called once the event loop is running."""
    global bot, app, call
    if bot is not None:
        return
    from .modules.clients import Bot, App, Call

    bot = Bot()
    app = App()
    call = Call()
