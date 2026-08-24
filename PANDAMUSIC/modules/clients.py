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


class Call(PyTgCalls):
    def __init__(self):
        self.adityaplayer1 = Client(
            "PANDAMUSIC_Player_1",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING1),
        )
        self.one = PyTgCalls(self.adityaplayer1, cache_duration=100)
        self.adityaplayer2 = Client(
            "PANDAMUSIC_Player_2",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING2),
        )
        self.two = PyTgCalls(self.adityaplayer2, cache_duration=100)
        self.adityaplayer3 = Client(
            "PANDAMUSIC_Player_3",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING3),
        )
        self.three = PyTgCalls(self.adityaplayer3, cache_duration=100)
        self.adityaplayer4 = Client(
            "PANDAMUSIC_Player_4",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING4),
        )
        self.four = PyTgCalls(self.adityaplayer4, cache_duration=100)
        self.adityaplayer5 = Client(
            "PANDAMUSIC_Player_5",
            api_id=console.API_ID,
            api_hash=console.API_HASH,
            session_string=str(console.STRING5),
        )
        self.five = PyTgCalls(self.adityaplayer5, cache_duration=100)

    call_config = GroupCallConfig(auto_start=True)
    paused = {}
    queue = {}
    active_chats = []
    start_times = {}

    async def ensure_assistant_in_chat(self, chat_id):
        from .. import bot

        assistant = await get_assistant(chat_id)
        info = _assistant_info_text(assistant)

        async def try_join():
            chat = await bot.get_chat(chat_id)
            try:
                if chat.username:
                    link_or_username = chat.username
                    chat_link = f"https://t.me/{link_or_username}"
                else:
                    try:
                        link_or_username = await bot.export_chat_invite_link(chat_id)
                        chat_link = link_or_username
                    except errors.ChatAdminRequired:
                        raise AssistantErr(
                            "❌ Bot needs **admin rights** with **Invite Users via Link** permission.\n"
                            "Please make the bot admin and try again."
                        )

                await assistant.join_chat(link_or_username)
                console.chat_links[chat_id] = chat_link
                return True
            except errors.UserAlreadyParticipant:
                return True
            except errors.UserBannedInChannel:
                raise AssistantErr(
                    "❌ **Assistant is banned in this group.**\n\n"
                    f"{info}\n\n"
                    "Please **unban** the assistant and try again."
                )
            except errors.InviteRequestSent:
                raise AssistantErr(
                    "⏳ Assistant join request sent.\n"
                    "Please **approve** the assistant in group requests, then try /play again."
                )
            except Exception as e:
                err = str(e).lower()
                if "banned" in err or "ban" in err:
                    raise AssistantErr(
                        "❌ **Assistant is banned in this group.**\n\n"
                        f"{info}\n\n"
                        "Please **unban** the assistant and try again."
                    )
                raise AssistantErr(f"Assistant join error: {e}")

        try:
            member = await bot.get_chat_member(chat_id, assistant.id)
            status = member.status

            if status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                return True

            if status == ChatMemberStatus.LEFT:
                return await try_join()

            # Banned / restricted / kicked
            if status in (
                ChatMemberStatus.BANNED,
                getattr(ChatMemberStatus, "RESTRICTED", None),
            ):
                raise AssistantErr(
                    "❌ **Assistant is banned / restricted in this group.**\n\n"
                    f"{info}\n\n"
                    "Please **unban** the assistant and try again."
                )

            raise AssistantErr(
                f"❌ Assistant cannot join this group.\n\n"
                f"Status: `{status}`\n"
                f"{info}"
            )

        except errors.UserNotParticipant:
            return await try_join()
        except errors.UserBannedInChannel:
            raise AssistantErr(
                "❌ **Assistant is banned in this group.**\n\n"
                f"{info}\n\n"
                "Please **unban** the assistant and try again."
            )
        except AssistantErr:
            raise
        except Exception as e:
            err = str(e).lower()
            if "banned" in err or "ban" in err:
                raise AssistantErr(
                    "❌ **Assistant is banned in this group.**\n\n"
                    f"{info}\n\n"
                    "Please **unban** the assistant and try again."
                )
            raise AssistantErr(f"Unexpected error while checking assistant: {e}")

    async def _restart_current_stream(self, chat_id: int) -> bool:
        """Restart current track. Video → try audio-only if video keeps dying."""
        queued = self.queue.get(chat_id) or []
        if not queued:
            return False

        item = queued[0]
        restarts = int(item.get("_restarts", 0))
        if restarts >= 2:
            print(f"[stream_end] max restarts reached for chat {chat_id}", flush=True)
            return False

        file_path = item.get("file_path")
        if not file_path:
            ms = item.get("media_stream")
            file_path = getattr(ms, "media_path", None) or getattr(ms, "path", None)

        if not file_path:
            return False

        is_video = bool(item.get("is_video", False))
        # First restart on video: fall back to audio-only (keeps assistant in VC)
        force_audio = is_video and restarts >= 0

        try:
            if force_audio:
                print(
                    f"[stream_end] video died early — falling back to audio chat={chat_id}",
                    flush=True,
                )
                media = self._build_media_stream(file_path, False, 0)
                item["is_video"] = False
            else:
                media = self._build_media_stream(file_path, is_video, 0)

            item["media_stream"] = media
            item["_restarts"] = restarts + 1
            item["played"] = 0

            await self.start_stream(chat_id, media)
            self.start_times[chat_id] = time.time()
            self.paused[chat_id] = False
            print(f"[stream_end] restarted stream chat={chat_id} audio_only={force_audio}", flush=True)
            return True
        except Exception as e:
            print(f"[stream_end] restart failed: {e}", flush=True)
            return False

    async def change_stream(self, chat_id: int):
        from .. import bot
        from PANDAMUSIC.plugins.callbacks import (
            player_markup,
            start_progress_task,
            stop_progress_task,
            _parse_duration,
        )

        stop_progress_task(chat_id)
        await self.pop_queue(chat_id)

        queued = self.queue.get(chat_id)
        if not queued:
            await bot.send_message(chat_id, "**Queue is empty, left VC.**")
            return await self.close_stream(chat_id)

        aux = await bot.send_message(chat_id, "**Processing...**")

        item = queued[0]
        file_path = item.get("file_path")
        is_video = bool(item.get("is_video", False))
        media_stream = item.get("media_stream")

        # Rebuild stream properly for video if we have file path
        if file_path:
            try:
                media_stream = self._build_media_stream(file_path, is_video, 0)
                item["media_stream"] = media_stream
            except Exception as e:
                print(f"[change_stream rebuild] {e}", flush=True)

        await self.start_stream(chat_id, media_stream)
        self.start_times[chat_id] = time.time()
        self.paused[chat_id] = False
        item["_restarts"] = 0

        thumbnail = item.get("thumbnail") or ""
        title = item.get("title") or "Unknown"
        duration = item.get("duration") or "0:00"
        mention = item.get("requested_by") or "User"
        total_sec = _parse_duration(duration)

        caption = panel_caption(
            title,
            duration,
            mention,
            header="sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ ᴏɴ ᴠᴄ"
            + (" (ᴠɪᴅᴇᴏ)" if is_video else ""),
        )
        buttons = player_markup(chat_id, 0, total_sec)

        try:
            await aux.delete()
        except Exception:
            pass

        try:
            if thumbnail and str(thumbnail).startswith("http"):
                panel = await bot.send_photo(
                    chat_id,
                    photo=thumbnail,
                    caption=caption,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                )
            else:
                panel = await bot.send_message(
                    chat_id,
                    caption,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            panel = await bot.send_message(
                chat_id,
                caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )

        item["panel"] = panel
        item["played"] = 0
        start_progress_task(chat_id)

    async def start_stream(self, chat_id: int, media_stream):
        assistant = await group_assistant(self, chat_id)

        # Must succeed before play — do not swallow AssistantErr (banned, no invite, etc.)
        await self.ensure_assistant_in_chat(chat_id)

        try:
            await assistant.play(chat_id, media_stream, config=self.call_config)
            if chat_id not in self.active_chats:
                self.active_chats.append(chat_id)
            return
        except NoActiveGroupCall:
            pass
        except AssistantErr:
            raise
        except Exception as e:
            print(f"[start_stream play error] {e}", flush=True)
            err = str(e).lower()
            if "channel_invalid" in err or "channel is invalid" in err:
                info = _assistant_info_text(await get_assistant(chat_id))
                raise AssistantErr(
                    "❌ **Cannot join Voice Chat** (CHANNEL_INVALID).\n\n"
                    "Possible reasons:\n"
                    "• Assistant is banned / not in group\n"
                    "• This is a Channel (use Supergroup)\n"
                    "• Bot missing admin permissions\n\n"
                    f"{info}\n\n"
                    "Unban assistant, make bot admin, then try again."
                )

        # Retry once after ensuring join again
        await self.ensure_assistant_in_chat(chat_id)

        try:
            await assistant.play(
                chat_id,
                media_stream,
                config=GroupCallConfig(auto_start=True),
            )
            if chat_id not in self.active_chats:
                self.active_chats.append(chat_id)
        except NoActiveGroupCall:
            raise AssistantErr(
                "❌ No active Voice Chat.\n\n"
                "Pehle group mein **Voice Chat / Video Chat** start karo, "
                "phir /play ya /vplay use karo."
            )
        except AssistantErr:
            raise
        except Exception as e:
            print(f"[start_stream retry error] {e}", flush=True)
            err = str(e).lower()
            if "channel_invalid" in err or "channel is invalid" in err:
                info = _assistant_info_text(await get_assistant(chat_id))
                raise AssistantErr(
                    "❌ **Cannot join Voice Chat** (CHANNEL_INVALID).\n\n"
                    "Possible reasons:\n"
                    "• Assistant is banned / not in group\n"
                    "• This is a Channel (use Supergroup)\n"
                    "• Bot missing admin permissions\n\n"
                    f"{info}\n\n"
                    "Unban assistant, make bot admin, then try again."
                )
            raise

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    async def mute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    async def unmute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.leave_call(chat_id)

    def _build_media_stream(self, file_path: str, is_video: bool, start_sec: int = 0):
        from pytgcalls.types import AudioQuality, MediaStream

        start_sec = max(0, int(start_sec or 0))

        # Prefer stable lower quality for VC — high res video often kills the call
        attempts = []

        if is_video:
            video_param = None
            try:
                from pytgcalls.types import VideoQuality

                # Prefer lower quality first for stability in Telegram VC
                for name in ("SD_360p", "SD_480p", "HD_720p", "HD_1080p", "FHD_1080p"):
                    if hasattr(VideoQuality, name):
                        video_param = getattr(VideoQuality, name)
                        break
            except Exception:
                video_param = None

            if video_param is not None:
                attempts.append(
                    dict(
                        media_path=file_path,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=video_param,
                        audio_flags=MediaStream.Flags.REQUIRED,
                        video_flags=MediaStream.Flags.AUTO_DETECT,
                    )
                )
                attempts.append(
                    dict(
                 