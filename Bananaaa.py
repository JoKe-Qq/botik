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
        """Загружает список чатов из файла, исключая дубликаты, и конвертирует теги в ID."""
        if os.path.exists(self.chats_file):
            with open(self.chats_file, "r") as file:
                chats = [line.strip() for line in file.readlines() if line.strip()]
            
            updated_chats = []
            for chat in set(chats):
                parts = chat.split(" | ")
                chat_id = parts[0]
                chat_link = parts[1] if len(parts) > 1 else "Unknown"
                chat_name = parts[2] if len(parts) > 2 else "Unknown"

                if chat_id.startswith("@"):  # Если это тег
                    try:
                        # Конвертируем тег в ID
                        entity = self.client.get_entity(chat_id)
                        chat_id = str(entity.id)
                        chat_link = f"@{entity.username}" if entity.username else "Unknown"
                        chat_name = entity.title
                    except Exception as e:
                        print(f"Ошибка при конвертации тега {chat}: {e}")
                updated_chats.append(f"{chat_id} | {chat_link} | {chat_name}")

            # Сохраняем обновлённый список чатов
            self.chats = updated_chats
            self.save_chats()
            return updated_chats
        return []

    def save_chats(self):
        """Сохраняет список чатов в файл."""
        with open(self.chats_file, "w") as file:
            file.write("\n".join(self.chats))

    async def resolve_chat_info(self, chat):
        """
        Преобразовывает тег (@examplegroup) или ID в полную информацию о чате.
        Возвращает строку в формате: "ID | @username | Название".
        """
        entity = await self.client.get_entity(chat)
        chat_id = str(entity.id)
        chat_link = f"@{entity.username}" if entity.username else "Unknown"
        chat_name = entity.title
        return f"{chat_id} | {chat_link} | {chat_name}"

    @loader.command()
    async def sxr(self, message):
        """- сохранить сообщение для рассылки (использовать в ответ на сообщение)"""
        reply = await message.get_reply_message()
        if not reply:
            await message.edit("<b>Нет сообщения для сохранения. Используйте эту команду в ответ на сообщение.</b>")
            return
        self.message_to_send = reply
        await message.edit("<b>Сообщение сохранено для рассылки.</b>")

    @loader.command()
    async def psxr(self, message):
        """- показать сохраненное сообщение для рассылки"""
        if not self.message_to_send:
            await message.edit("<b>Сообщение для рассылки не сохранено.</b>")
        else:
            await self.client.send_message(message.chat_id, self.message_to_send)

    @loader.command()
    async def dchat(self, message):
        """- добавить чат в список для рассылки (использовать только с @username или chat_id)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("<b>Укажите корректный @username или chat_id чата для добавления.</b>")
            return

        try:
            # Преобразуем тег или ID в полную информацию
            chat_info = await self.resolve_chat_info(args)

            chat_id = chat_info.split(" | ")[0]  # Извлекаем ID
            if chat_id not in [c.split(" | ")[0] for c in self.chats]:
                # Сохраняем информацию о чате
                self.chats.append(chat_info)
                self.save_chats()
                await message.edit(f"<b>Чат добавлен в список для рассылки:</b>\n<code>{chat_info}</code>")
            else:
                await message.edit(f"<b>Чат уже находится в списке для рассылки:</b>\n<code>{chat_info}</code>")

        except Exception as e:
            await message.edit(f"<b>Ошибка: {e}</b>")

    @loader.command()
    async def chatss(self, message):
        """- показать список чатов для рассылки"""
        if not self.chats:
            await message.edit("<b>Список чатов для рассылки пуст.</b>")
        else:
            chat_list = "\n".join(self.chats)
            await message.edit(f"<b>Список чатов для рассылки:</b>\n<code>{chat_list}</code>")

    @loader.command()
    async def delchat(self, message):
        """- удалить чат из списка для рассылки (использовать только через @username или chat_id)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("<b>Укажите @username или chat_id чата для удаления.</b>")
            return

        try:
            # Преобразуем тег или ID в полную информацию
            chat_info = await self.resolve_chat_info(args)

            chat_id = chat_info.split(" | ")[0]  # Извлекаем ID
            if chat_id in [c.split(" | ")[0] for c in self.chats]:
                self.chats = [c for c in self.chats if not c.startswith(chat_id)]
                self.save_chats()
                await message.edit(f"<b>Чат удалён из списка для рассылки:</b>\n<code>{chat_info}</code>")
            else:
                await message.edit(f"<b>Чат не найден в списке для рассылки:</b>\n<code>{chat_info}</code>")

        except Exception as e:
            await message.edit(f"<b>Ошибка: {e}</b>")

    @loader.command()
    async def updatechats(self, message):
        """- обновить названия и ссылки для чатов в списке"""
        if not self.chats:
            await message.edit("<b>Список чатов для обновления пуст.</b>")
            return

        updated_chats = []
        for chat in self.chats:
            try:
                # Разделяем строку на ID, ссылку, имя
                parts = chat.split(" | ")
                chat_id = parts[0]  # ID чата

                # Получаем обновлённую информацию о чате
                entity = await self.client.get_entity(int(chat_id))
                updated_chats.append(f"{chat_id} | @{entity.username or 'Unknown'} | {entity.title}")
            except Exception as e:
                print(f"Ошибка при обновлении информации о чате {chat}: {e}")
                updated_chats.append(chat)  # Сохраняем оригинал, если не удалось

        # Сохраняем обновлённые данные
        self.chats = updated_chats
        self.save_chats()
        await message.edit("<b>Информация о чатах успешно обновлена.</b>")
