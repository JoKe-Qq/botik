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
        """Загружает список чатов из файла, исключая дубликаты."""
        if os.path.exists(self.chats_file):
            with open(self.chats_file, "r") as file:
                chats = [line.strip() for line in file.readlines() if line.strip()]
                return list(set(chats))  # Убираем дубликаты
        return []

    def save_chats(self):
        """Сохраняет список чатов в файл."""
        with open(self.chats_file, "w") as file:
            file.write("\n".join(self.chats))

    def is_valid_chat(self, chat):
        """Проверяет корректность адреса чата."""
        return re.match(r"^@\w+$", chat) or chat.isdigit() or chat.startswith("-100")

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
        if not args or not self.is_valid_chat(args):
            await message.edit("<b>Укажите корректный @username или chat_id чата для добавления.</b>")
            return
        if args not in self.chats:
            self.chats.append(args)
            self.save_chats()
            await message.edit(f"<b>Чат {args} добавлен в список для рассылки.</b>")
        else:
            await message.edit(f"<b>Чат {args} уже находится в списке для рассылки.</b>")

    @loader.command()
    async def chatss(self, message):
        """- показать список чатов для рассылки"""
        if not self.chats:
            await message.edit("<b>Список чатов для рассылки пуст.</b>")
        else:
            chat_list = "\n".join(self.chats)
            await message.edit(f"<b>Список чатов для рассылки:</b>\n{chat_list}")

    @loader.command()
    async def delchat(self, message):
        """- удалить чат из списка для рассылки (использовать только через @username или chat_id)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("<b>Укажите @username или chat_id чата для удаления.</b>")
            return
        if args in self.chats:
            self.chats.remove(args)
            self.save_chats()
            await message.edit(f"<b>Чат {args} удален из списка для рассылки.</b>")
        else:
            await message.edit(f"<b>Чат {args} не найден в списке для рассылки.</b>")

    @loader.command()
    async def minterval(self, message):
        """- установить интервал рассылки (в минутах)"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await message.edit("<b>Укажите интервал в минутах.</b>")
            return
        self.interval = int(args)
        await message.edit(f"<b>Интервал рассылки установлен на {self.interval} минут.</b>")

    @loader.command()
    async def getinterval(self, message):
        """- показать текущий интервал рассылки"""
        await message.edit(f"<b>Текущий интервал рассылки: {self.interval} минут.</b>")

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
            while self.running:
                for chat in self.chats:
                    try:
                        # Преобразуем ID в int, если это числовой ID
                        chat_id = int(chat) if chat.isdigit() else chat

                        # Проверяем интервал
                        current_time = time.time()
                        if chat in self.last_sent_time and current_time - self.last_sent_time[chat] < self.interval * 60:
                            print(f"Пропускаем чат {chat} (интервал ещё не истёк)")
                            continue

                        # Отправляем сообщение
                        if self.message_to_send.media:
                            await self.client.send_file(chat_id, self.message_to_send.media, caption=self.message_to_send.text)
                        else:
                            await self.client.send_message(chat_id, self.message_to_send.text)

                        # Логируем время отправки
                        self.last_sent_time[chat] = current_time
                        print(f"Сообщение успешно отправлено в чат {chat_id}")

                    except Exception as e:
                        if "file reference has expired" in str(e).lower():
                            await self.client.send_message("me", f"Рассылка остановлена: срок действия ссылки сообщения истёк.\nОшибка: {e}")
                            print("Срок действия ссылки истёк. Рассылка остановлена.")
                            self.running = False
                            return

                        print(f"Ошибка при отправке в чат {chat}: {e}")
                        await self.client.send_message("me", f"Ошибка при отправке в чат {chat}: {e}")
                        continue  # Переходим к следующему чату

                # Задержка между циклами рассылки
                await asyncio.sleep(self.interval * 60)

        except Exception as e:
            print(f"Критическая ошибка рассылки: {e}")
            await self.client.send_message("me", f"Рассылка остановлена из-за ошибки: {str(e)}")
        finally:
            self.running = False

    @loader.command()
    async def stopr(self, message):
        """- остановить рассылку сообщений"""
        if self.running:
            self.running = False
            await message.edit("<b>Рассылка сообщений остановлена.</b>")
        else:
            await message.edit("<b>Рассылка сообщений не активна.</b>")
