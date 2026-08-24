        for method_name in ("seek_stream", "seek"):
            method = getattr(assistant, method_name, None)
            if not callable(method):
                continue
            try:
                await method(chat_id, position)
                return
            except TypeError:
                try:
                    await method(chat_id, position=position)
                    return
                except Exception:
                    pass
            except Exception:
                pass

        media = self._build_media_stream(file_path, is_video, position)
        await assistant.play(chat_id, media, config=self.call_config)
        item["media_stream"] = media

        if chat_id not in self.active_chats:
            self.active_chats.append(chat_id)

        self.paused[chat_id] = False

    async def add_to_queue(
        self,
        chat_id,
        media_stream,
        title,
        duration,
        thumbnail,
        requested_by,
        file_path=None,
        is_video=False,
    ):
        if chat_id not in self.queue:
            self.queue[chat_id] = []

        if not file_path and media_stream is not None:
            file_path = getattr(media_stream, "media_path", None) or getattr(
                media_stream, "path", None
            )

        item = {
            "media_stream": media_stream,
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "requested_by": requested_by,
            "played": 0,
            "file_path": file_path,
            "is_video": bool(is_video),
            "_restarts": 0,
        }
        self.queue[chat_id].append(item)
        return len(self.queue[chat_id]) - 1

    async def pop_queue(self, chat_id: int):
        if chat_id in self.queue and self.queue[chat_id]:
            return self.queue[chat_id].pop(0)
        return None

    async def clear_queue(self, chat_id: int):
        if chat_id in self.active_chats:
            self.active_chats.remove(chat_id)
        try:
            from PANDAMUSIC.plugins.callbacks import stop_progress_task

            stop_progress_task(chat_id)
        except Exception:
            pass
        try:
            self.queue.pop(chat_id)
        except Exception:
            pass
        self.start_times.pop(chat_id, None)
        self.paused.pop(chat_id, None)

    async def is_stream_off(self, chat_id: int) -> bool:
        mode = self.paused.get(chat_id)
        if not mode:
            return False
        return mode

    async def stream_on(self, chat_id: int):
        self.paused[chat_id] = False

    async def stream_off(self, chat_id: int):
        self.paused[chat_id] = True

    async def close_stream(self, chat_id: int):
        try:
            await self.stop_stream(chat_id)
        except Exception:
            pass
        await self.clear_queue(chat_id)

    async def ping(self):
        pings = []
        if console.STRING1:
            pings.append(await self.one.ping)
        if console.STRING2:
            pings.append(await self.two.ping)
        if console.STRING3:
            pings.append(await self.three.ping)
        if console.STRING4:
            pings.append(await self.four.ping)
        if console.STRING5:
            pings.append(await self.five.ping)
        if not pings:
            return "0"
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        console.logs(__name__).info("Starting PyTgCalls Client\n")
        if console.STRING1:
            await self.one.start()
        if console.STRING2:
            await self.two.start()
        if console.STRING3:
            await self.three.start()
        if console.STRING4:
            await self.four.start()
        if console.STRING5:
            await self.five.start()

    async def decorators(self):
        @self.one.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.two.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.three.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.four.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.five.on_update(fl.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
        @self.one.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
        @self.two.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
        @self.three.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
        @self.four.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
        @self.five.on_update(fl.chat_update(ChatUpdate.Status.KICKED))
        @self.one.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.two.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.three.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.four.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
        @self.five.on_update(fl.chat_update(ChatUpdate.Status.LEFT_GROUP))
        async def stream_services_handler(_, update: Update):
            return await self.close_stream(update.chat_id)

        @self.one.on_update(fl.stream_end())
        @self.two.on_update(fl.stream_end())
        @self.three.on_update(fl.stream_end())
        @self.four.on_update(fl.stream_end())
        @self.five.on_update(fl.stream_end())
        async def stream_end_handler(_, update: Update):
            chat_id = update.chat_id
            start = self.start_times.get(chat_id)
            elapsed = (time.time() - start) if start else 999

            # Premature end (common on bad / incompatible video) → restart instead of leave
            if elapsed < STREAM_GRACE_SECONDS:
                print(
                    f"[stream_end] premature end after {elapsed:.1f}s chat={chat_id} — trying restart",
                    flush=True,
                )
                ok = await self._restart_current_stream(chat_id)
                if ok:
                    return

            return await self.change_stream(chat_id)