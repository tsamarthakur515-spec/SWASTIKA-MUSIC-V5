import sys
import time

from .. import console
from .database import get_assistant, group_assistant
from .helpers import AssistantErr
from .formatters import panel_caption

from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pytgcalls import PyTgCalls, filters as fl
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import Call, GroupCallConfig, ChatUpdate, Update, StreamEnded


assistants = []
assistantids = []

# Ignore stream_end if stream just started (prevents instant leave on bad video)
STREAM_GRACE_SECONDS = 12


def _assistant_info_text(assistant) -> str:
    """Build readable assistant identity for user-facing errors."""
    name = getattr(assistant, "name", None) or "Unknown"
    username = getattr(assistant, "username", None)
    aid = getattr(assistant, "id", None) or "?"
    lines = [f"• Name: `{name}`"]
    if username:
        lines.append(f"• Username: `@{username}`")
    else:
        lines.append("• Username: `None`")
    lines.append(f"• ID: `{aid}`")
    return "\n".join(lines)


class Bot(Client):
    def __init__(self):
        super().__init__(
            "PANDAMUSIC_Bot",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            bot_token=console.BOT_TOKEN,
        )

    async def start(self):
        console.logs(__name__).info("Starting Bot ...")
        await super().start()
        get_me = await self.get_me()
        if get_me.last_name:
            self.name = get_me.first_name + " " + get_me.last_name
        else:
            self.name = get_me.first_name
        self.username = get_me.username
        self.mention = get_me.mention
        self.id = get_me.id
        try:
            await self.send_message(console.LOG_GROUP_ID, "**Bot Started.**")
        except Exception:
            console.logs(__name__).error(
                "Bot has failed to access the log Group."
            )
            sys.exit()
        try:
            a = await self.get_chat_member(console.LOG_GROUP_ID, self.id)
        except Exception:
            console.logs(__name__).error(
                "Bot has failed to access the log Group."
            )
            sys.exit()
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            console.logs(__name__).error(
                "Please promote bot as admin in your logger group!"
            )
            sys.exit()
        console.logs(__name__).info(f"Bot Started as {self.name}")


class App(Client):
    def __init__(self):
        self.one = Client(
            "PANDAMUSIC_1",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING1),
            no_updates=True,
        )
        self.two = Client(
            "PANDAMUSIC_2",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING2),
            no_updates=True,
        )
        self.three = Client(
            "PANDAMUSIC_3",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING3),
            no_updates=True,
        )
        self.four = Client(
            "PANDAMUSIC_4",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING4),
            no_updates=True,
        )
        self.five = Client(
            "PANDAMUSIC_5",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING5),
            no_updates=True,
        )

    async def start(self):
        console.logs(__name__).info("Starting Assistant Clients")
        clients = [
            (console.STRING1, self.one, 1),
            (console.STRING2, self.two, 2),
            (console.STRING3, self.three, 3),
            (console.STRING4, self.four, 4),
            (console.STRING5, self.five, 5),
        ]
        for string, client, num in clients:
            if not string:
                continue
            await client.start()
            try:
                await client.join_chat("AdityaServer")
                await client.join_chat("AdityaDiscus")
            except Exception:
                pass
            assistants.append(num)
            try:
                await client.send_message(
                    console.LOG_GROUP_ID, f"**Assistant ({num}) Started.**"
                )
            except Exception:
                console.logs(__name__).error(
                    f"Assistant account {num} has failed to access the log group."
                )
                sys.exit()
            get_me = await client.get_me()
            client.name = (
                (get_me.first_name + " " + get_me.last_name)
                if get_me.last_name
                else get_me.first_name
            )
            client.username = get_me.username
            client.mention = get_me.mention
            client.id = get_me.id
            assistantids.append(get_me.id)
            console.logs(__name__).info(
                f"Assistant ({num}) started as - {client.name}"
            )
