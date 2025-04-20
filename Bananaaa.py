@loader.command()
async def rassil(self, message):
    """- разослать сохраненное сообщение по указанным чатам через интервал времени"""
    if not self.message_to_send:
        await message.edit("<b>Нет сообщения для рассылки.</b>")
        return
    if not self.chats:
        await message.edit("<b>Список чатов для рассылки пуст.</b>")
        return
    if self.running:
        await message.edit("<b>Рассылка уже запущена.</b>")
        return

    await message.edit(f"<b>Начинаю рассылку каждые {self.interval} минут...</b>")
    self.running = True

    try:
        # Если сообщение содержит медиа, скачиваем его локально
        media_path = None
        if self.message_to_send.media:
            media_path = await self.message_to_send.download_media()

        while self.running:
            for chat in self.chats:
                try:
                    await asyncio.sleep(0.005)  # Минимальная задержка между отправками

                    # Отправляем сообщение
                    if media_path:  # Если есть вложение
                        await self.client.send_file(chat, media_path, caption=self.message_to_send.text)
                    else:  # Если только текст
                        await self.client.send_message(chat, self.message_to_send.text)

                except Exception as e:
                    print(f"Ошибка при отправке в чат {chat}: {e}")
                    # Логирование ошибки, но продолжаем рассылку в остальные чаты
                    await self.client.send_message("me", f"Ошибка при отправке в чат {chat}: {e}")
                    continue  # Переходим к следующему чату

            # Задержка между циклами рассылки
            await asyncio.sleep(self.interval * 60)

    except Exception as e:
        print(f"Критическая ошибка рассылки: {e}")
        await self.client.send_message("me", f"Рассылка остановлена из-за ошибки: {str(e)}")
    finally:
        self.running = False
        # Удаляем локально сохраненное медиа, если оно есть
        if media_path and os.path.exists(media_path):
            os.remove(media_path)
