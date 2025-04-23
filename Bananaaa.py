from telethon import events
from .. import loader, utils
import asyncio
import re
import os
import time


class banan(loader.Module):
    """
    Модуль для получения бана 🥵 из-за рассылки от @j_0_k_e.
    """
    strings = {"name": "rassil"}

    def __init__(self):
        self.chats_file = "chats_list.txt"
        self.chats = self.load_chats()
        self.message_to_send = None
        self.interval = 10  # Интервал по умолчанию в минутах
        self.running = False  # Статус рассылки
        self.last_sent_time = {}  # Время последней отправки по каждому чату

    async def client_ready(self, client, db):
        self.client = client

    def load_chats(self):
        """Загружает список чатов из файла."""
        if os.path.exists(self.chats_file):
            with open(self.chats_file, "r") as file:
                return [line.strip() for line in file.readlines() if line.strip()]
        return []

    def save_chats(self):
        """Сохраняет список чатов в файл."""
        with open(self.chats_file, "w") as file:
            file.write("\n".join(self.chats))

    async def resolve_chat_info(self, chat):
        """
        Преобразует @username или chat_id в полную информацию о чате.
        Возвращает строку в формате: "ID | @username | Название".
        """
        try:
            entity = await self.client.get_entity(chat)
            chat_id = str(entity.id)
            chat_username = f"@{entity.username}" if entity.username else "Unknown"
            chat_title = entity.title if hasattr(entity, "title") and entity.title else "Unknown"
            return f"{chat_id} | {chat_username} | {chat_title}"
        except Exception as e:
            raise ValueError(f"Не удалось получить информацию о чате: {e}")

    async def refresh_message(self):
        async def refresh_message(self):
        """
        Пересохраняет текущее сообщение для рассылки.
        Это продлевает срок действия ссылки на медиа (если есть вложение).
        Уведомления отправляются отдельно в "Избранное", чтобы не перезаписывать исходное сообщение.
        Предыдущее сохранённое сообщение удаляется.
        """
        if self.message_to_send:
            try:
                # Удаляем предыдущее сообщение, если оно существует
                if hasattr(self, "previous_message") and self.previous_message:
                    await self.previous_message.delete()

                # Отправляем новое сообщение для обновления медиа
                if self.message_to_send.media:
                    updated_message = await self.client.send_file(
                        "me", self.message_to_send.media, caption=self.message_to_send.text
                    )
                else:
                    updated_message = await self.client.send_message(
                        "me", self.message_to_send.text
                    )

                # Сохраняем обновлённое сообщение для рассылки
                self.message_to_send = updated_message

                # Сохраняем новое сообщение как предыдущую версию
                self.previous_message = updated_message

                # Уведомляем об успешном обновлении
                await self.client.send_message(
                    "me", "<b>Сообщение успешно обновлено для продления срока действия.</b>"
                )
                print("Сообщение для рассылки обновлено.")
            except Exception as e:
                # Логируем ошибку в личные сообщения
                await self.client.send_message(
                    "me", f"<b>Ошибка при обновлении сообщения:</b> {e}"
                )
                print(f"Ошибка при обновлении сообщения: {e}")

    @loader.command()
    async def sxr(self, message):
        """- сохраняет сообщение для рассылки (использовать в ответ на сообщение)"""
        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<b>Нет сообщения для сохранения. Используйте эту команду в ответ на сообщение.</b>")
            return
        self.message_to_send = reply
        await message.edit("<b>Сообщение сохранено для рассылки.</b>")

    @loader.command()
    async def psxr(self, message):
        """- показывает сохр. соо для рассылки"""
        if not self.message_to_send:
            await message.edit("<b>Сообщение для рассылки не сохранено.</b>")
        else:
            await self.client.send_message(message.chat_id, self.message_to_send)

    @loader.command()
    async def chatss(self, message):
        """- показывает список чатов для рассылки"""
        if not self.chats:
            await message.edit("<b>Список чатов для рассылки пуст.</b>")
            return

        chat_list = "\n".join(self.chats)
        max_length = 4000  # Устанавливаем лимит длины сообщения (немного меньше 4096 для безопасности)
        
        if len(chat_list) > max_length:
            parts = [chat_list[i:i+max_length] for i in range(0, len(chat_list), max_length)]
            for part in parts:
                await self.client.send_message(message.chat_id, f"<b>Список чатов для рассылки:</b>\n<code>{part}</code>")
            await message.delete()
        else:
            await message.edit(f"<b>Список чатов для рассылки:</b>\n<code>{chat_list}</code>")

    @loader.command()
    async def adchat(self, message):
        """- добавляет тот чат в котором написали эту команду в список чатов для рассылки"""
        try:
            chat = await message.get_chat()
            chat_id = str(chat.id)
            chat_username = f"@{chat.username}" if chat.username else "Unknown"
            chat_title = chat.title if chat.title else "Unknown"

            chat_info = f"{chat_id} | {chat_username} | {chat_title}"
            log_message = ""

            if chat_id not in [c.split(" | ")[0] for c in self.chats]:
                self.chats.append(chat_info)
                self.save_chats()
                log_message = f"<b>Успешно добавлено:</b>\n<code>{chat_info}</code>"
            else:
                log_message = f"<b>Чат уже находится в списке:</b>\n<code>{chat_info}</code>"

            # Отправляем лог в личные сообщения
            await self.client.send_message("me", log_message)
        except Exception as e:
            # Логируем ошибку в личные сообщения
            error_message = f"<b>Ошибка при добавлении текущего чата:</b> {e}"
            await self.client.send_message("me", error_message)
        finally:
            # Удаляем сообщение команды
            await message.delete()

    @loader.command()
    async def dchat(self, message):
        """- добавить чат в список для рассылки (использовать @username или chat_id)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("<b>Укажите @username или chat_id чата для добавления.</b>")
            return

        try:
            chat_info = await self.resolve_chat_info(args)
            chat_id = chat_info.split(" | ")[0]
            if chat_id not in [c.split(" | ")[0] for c in self.chats]:
                self.chats.append(chat_info)
                self.save_chats()
                await message.edit(f"<b>Чат добавлен в список для рассылки:</b>\n<code>{chat_info}</code>")
            else:
                await message.edit(f"<b>Чат уже находится в списке для рассылки:</b>\n<code>{chat_info}</code>")
        except Exception as e:
            await message.edit(f"<b>Ошибка: {e}</b>")

    @loader.command()
    async def delchat(self, message):
        """- удалить чат из списка для рассылки (через @username или chat_id)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("<b>Укажите @username или chat_id чата для удаления.</b>")
            return

        try:
            chat_info = await self.resolve_chat_info(args)
            chat_id = chat_info.split(" | ")[0]
            if chat_id in [c.split(" | ")[0] for c in self.chats]:
                self.chats = [c for c in self.chats if not c.startswith(chat_id)]
                self.save_chats()
                await message.edit(f"<b>Чат удалён из списка для рассылки:</b>\n<code>{chat_info}</code>")
            else:
                await message.edit(f"<b>Чат не найден в списке для рассылки:</b>\n<code>{chat_info}</code>")
        except Exception as e:
            await message.edit(f"<b>Ошибка: {e}</b>")

    @loader.command()
    async def dint(self, message):
        """- установить интервал рассылки (минуты)"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await message.edit("<b>Укажите интервал в минутах.</b>")
            return
        self.interval = max(5, int(args))
        await message.edit(f"<b>Интервал рассылки установлен на {self.interval} минут.</b>")

    @loader.command()
    async def pint(self, message):
        """- показать интервал рассылки"""
        await message.edit(f"<b>Текущий интервал рассылки: {self.interval} минут.</b>")

    @loader.command()
    async def rassil(self, message):
        """- Начать рассылку по чатам"""
        if not self.message_to_send:
            await message.edit("<b>Нет сообщения для рассылки.</b>")
            return
        if not self.chats:
            await message.edit("<b>Список чатов пуст.</b>")
            return
        if self.running:
            await message.edit("<b>Рассылка уже запущена.</b>")
            return

        await message.edit(f"<b>Рассылка каждые {self.interval} минут...</b>")
        self.running = True

        try:
            while self.running:
                for chat in self.chats:
                    try:
                        chat_id = int(chat.split(" | ")[0])
                        if self.message_to_send.media:
                            await self.client.send_file(chat_id, self.message_to_send.media, caption=self.message_to_send.text)
                        else:
                            await self.client.send_message(chat_id, self.message_to_send.text)

                        print(f"Сообщение успешно отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка при отправке в чат {chat}: {e}")
                        await self.client.send_message("me", f"Ошибка при отправке в чат {chat}: {e}")
                        continue
                await self.refresh_message()
                await asyncio.sleep(self.interval * 60)
        except Exception as e:
            print(f"Критическая ошибка рассылки: {e}")
            await self.client.send_message("me", f"Рассылка остановлена из-за ошибки: {str(e)}")
        finally:
            self.running = False

    @loader.command()
    async def stopr(self, message):
        """- остановить рассылку"""
        if self.running:
            self.running = False
            await message.edit("<b>Рассылка остановлена.</b>")
        else:
            await message.edit("<b>Рассылка не активна.</b>")

    @loader.command()
    async def uchats(self, message):
        """- обновить названия и теги для чатов в списке"""
        if not self.chats:
            await message.edit("<b>Список чатов для обновления пуст.</b>")
            return

        updated_chats = []
        unresolved_chats = []  # Для логирования чатов, которые не удалось обновить

        # Отправляем сообщение о начале обновления
        await message.edit("<b>Обновление информации о чатах началось...</b>")

        for chat in self.chats:
            try:
                parts = chat.split(" | ")
                chat_id = parts[0]

                # Получаем информацию о чате (по ID или тегу)
                entity = await self.client.get_entity(int(chat_id) if chat_id.isdigit() else chat_id)

                # Извлекаем обновлённую информацию
                updated_chat_id = str(entity.id)
                updated_username = f"@{entity.username}" if entity.username else "Unknown"
                updated_title = entity.title if entity.title else "Unknown"

                updated_chats.append(f"{updated_chat_id} | {updated_username} | {updated_title}")
            except Exception as e:
                print(f"Ошибка при обновлении информации о чате {chat}: {e}")
                unresolved_chats.append(chat)  # Добавляем в список проблемных чатов

        # Обновляем список чатов
        self.chats = updated_chats
        self.save_chats()

        # Сообщение о завершении
        result_message = "<b>Информация о чатах успешно обновлена.</b>"
        if unresolved_chats:
            unresolved_list = "\n".join(unresolved_chats)
            result_message += f"\n<b>Не удалось обновить следующие чаты:</b>\n<code>{unresolved_list}</code>"

        await message.edit(result_message)
