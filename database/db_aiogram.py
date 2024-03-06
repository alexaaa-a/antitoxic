import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatType

# Установка уровня логгирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# Функция для создания базы данных и таблицы
def create_database():
    try:
        # Подключаемся к базе данных или создаем новую, если она не существует
        conn = sqlite3.connect('chat_members.db')

        # Создаем курсор для выполнения SQL-запросов
        cursor = conn.cursor()

        # Создаем таблицу для хранения участников чатов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER
            )
        ''')

        # Сохраняем изменения в базе данных
        conn.commit()

        # Закрываем соединение с базой данных
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")


# Функция для добавления участников в базу данных
async def add_users_to_database(group_id: int, users: list):
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('chat_members.db')

        # Создаем курсор для выполнения SQL-запросов
        cursor = conn.cursor()

        # Добавляем участников в базу данных
        for user_id in users:
            cursor.execute('''
                INSERT INTO chat_members (chat_id, user_id)
                VALUES (?, ?)
            ''', (group_id, user_id))

        # Сохраняем изменения в базе данных
        conn.commit()

        # Закрываем соединение с базой данных
        conn.close()

        return True  # Успешно добавлено
    except Exception as e:
        print(f"Error adding users to database: {e}")
        return False  # Ошибка при добавлении


# Фильтр для проверки, что бот добавлен в группу
class AddedToGroup(types.ChatMemberUpdated):
    async def check(self, message: types.Message) -> bool:
        return message.new_chat_members and bot.id in [user.id for user in message.new_chat_members]


# Обработчик добавления бота в группу
@dp.message(is_added_to_group=True)
async def on_added_to_group(message: types.Message):
    chat_id = message.chat.id
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        members = await bot.get_chat_members_count(chat_id)
        if members:
            # Получаем список участников чата
            chat_members = await bot.get_chat_members(chat_id)
            user_ids = [member.user.id for member in chat_members if member.user.id != bot.id]

            # Добавляем участников в базу данных
            await add_users_to_database(chat_id, user_ids)
            await message.reply(f"Участники группы с ID {chat_id} были успешно добавлены в базу данных.")
        else:
            await message.reply(f"Группа с ID {chat_id} не найдена.")


# Запуск бота
if __name__ == '__main__':
    import asyncio

    create_database()  # Создаем базу данных

    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()
