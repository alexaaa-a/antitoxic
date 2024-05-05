import logging

import aiogram.exceptions
import joblib
from db import get_chat_members
import datetime
from aiogram import Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import config
from aiogram import types, F, Router, Bot
from aiogram.types import Message
from aiogram.methods import get_chat_member
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, KICKED, LEFT, \
    RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from aiogram.types import ChatMemberUpdated
from aiogram.filters.command import Command
import asyncio
import aiosqlite

router = Router()

@router.message(F.text.lower() == 'привет')
async def welcome(message: Message):
    await message.answer('Напиши /start, и мы начнем!')

@router.message(Command("start"))
async def start_handler(msg: Message):
    kb = [
        [
            types.KeyboardButton(text="/ban"),
            types.KeyboardButton(text="/unban"),
            types.KeyboardButton(text="/mute"),
            types.KeyboardButton(text="/toxic"),
            types.KeyboardButton(text="/points")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    await msg.answer('Мяяу!! Я - бот для определения токсиков и душнил в твоих чатах :) Выбери нужную кнопочку и жмякни по ней!')
    await msg.answer('Кнопочки для вас, мои котики!', reply_markup=keyboard)

    chat_id = msg.chat.id
    chat_members = await get_chat_members(chat_id)
    await add_members_to_database(chat_id, chat_members, points=0)
    await msg.answer(f'Участники чата успешно добавлены!')
    await reset_and_recreate_table(chat_id)


async def main():
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

@router.chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=
        (KICKED | LEFT | RESTRICTED | MEMBER)
        >>
        (ADMINISTRATOR | CREATOR)
    )
)
async def admin_promoted(event: ChatMemberUpdated, admins: set[int]):
    admins.add(event.new_chat_member.user.id)

async def reset_points(chat_id):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('UPDATE members_{id} SET points = 0'.format(id=chat_id))
                await conn.commit()
    except Exception as e:
        print(f"Error resetting points: {e}")

async def drop_table(chat_id):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('DROP TABLE IF EXISTS members_{id}'.format(id=chat_id))
                await conn.commit()
    except Exception as e:
        print(f"Error dropping table: {e}")

async def create_table_words():
    try:
        async with aiosqlite.connect('words.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        word TEXT
                    )
                ''')
                await conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")

async def reset_and_recreate_table(chat_id):
    try:
        await reset_points(chat_id)
        await drop_table(chat_id)
        await create_table(chat_id)
    except Exception as e:
        print(f"Error resetting and recreating table: {e}")
async def add_word_to_database(word: str):
    await create_table_words()

    try:
        async with aiosqlite.connect('words.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO words (word)
                    VALUES (?)
                ''', (word,))
                await conn.commit()
    except Exception as e:
        print(f"Error adding word to database: {e}")

@router.message(Command('new'))
async def add_new_word(msg: Message, command: Command):
    word = command.args
    if word:
        await add_word_to_database(word)
        await msg.answer(f'Слово "{word}" добавленно в базу.')
    else:
        await msg.answer('Пожалуйста, напиши слово, которое ты хочешь добавить в базу, после команды')

async def create_table(msg: Message):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                # Создаем таблицу для хранения информации о чатах
                await cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chat_info (
                            id INTEGER PRIMARY KEY,
                            chat_id INTEGER UNIQUE
                        )
                    ''')
                await conn.commit()

                # Проверяем, есть ли запись о текущем чате
                chat_id = msg.chat.id
                await cursor.execute('SELECT id FROM chat_info WHERE chat_id = ?', (chat_id,))
                existing_chat = await cursor.fetchone()

                if not existing_chat:
                    # Если записи о чате нет, добавляем ее
                    await cursor.execute('INSERT INTO chat_info (chat_id) VALUES (?)', (chat_id,))
                    await conn.commit()

                # Создаем таблицу участников для данного чата
                if existing_chat or not existing_chat:
                    await cursor.execute('''
                            CREATE TABLE IF NOT EXISTS members_{id} (
                                user_id INTEGER PRIMARY KEY,
                                username TEXT,
                                points INTEGER
                            )
                        '''.format(id=existing_chat[0] if existing_chat else cursor.lastrowid))
                    await conn.commit()

    except Exception as e:
        print(f"Error creating table: {e}")

async def add_members_to_database(chat_id: int, member_ids: list, points: int):
    try:
        await create_table(chat_id)  # Проверка на существование таблицы

        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                for member_id in member_ids:
                    await cursor.execute('''
                            INSERT OR IGNORE INTO members (chat_id, member_id, points)
                            VALUES (?, ?, ?)
                        ''', (chat_id, member_id, points))

                await conn.commit()

    except Exception as e:
        print(f"Error adding members to database: {e}")


async def add_toxic_words(chat_id, member_id, toxic_word):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await create_table()

                # Проверяем, существует ли уже запись с указанным chat_id и member_id
                await cursor.execute('''
                        SELECT *
                        FROM members
                        WHERE chat_id = ? AND member_id = ?
                    ''', (chat_id, member_id))
                existing_record = await cursor.fetchone()

                if existing_record:
                    existing_toxic_words = existing_record[2]  # Получаем текущие токсичные слова
                    if existing_toxic_words:
                        new_toxic_words = f'{existing_toxic_words}, {toxic_word}'
                    else:
                        new_toxic_words = toxic_word
                    await cursor.execute('''
                            UPDATE members
                            SET toxic_words = ?
                            WHERE chat_id = ? AND member_id = ?
                        ''', (new_toxic_words, chat_id, member_id))
                else:
                    # Если записи нет, просто добавляем новую запись
                    await cursor.execute('''
                            INSERT INTO members(chat_id, member_id, toxic_words)
                            VALUES (?, ?, ?)
                        ''', (chat_id, member_id, toxic_word))

                await conn.commit()
    except Exception as e:
        print(f"Error adding toxic word: {e}")

async def add_toxic_word(msg: Message):
    chat_id = msg.chat.id
    member_id = msg.user.id
    username = msg.user.first_name
    toxic_word = msg.text
    await add_toxic_words(chat_id, member_id, toxic_word)
    # Добавление +1 балла в столбец points для участника чата
    try:
            table_name = f"chat_{abs(chat_id)}"

            async with aiosqlite.connect('chat_members.db') as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute('''
                        UPDATE {table_name}
                        SET points = points + 1
                        WHERE member_id = ?
                    ''', member_id)

                    await conn.commit()
    except Exception as e:
        print(f"Error updating points: {e}")

        await msg.answer(f"Слово '{toxic_word}' добавлено к пользователю {username} в базу данных и +1 балл участнику.")

@router.message(Command('points'))
async def show_member_points(msg: Message):
    try:
        # Получаем ID пользователя, на чье сообщение отвечаем
        replied_user_id = msg.reply_to_message.from_user.id

        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                # Извлекаем баллы только для указанного пользователя
                await cursor.execute('SELECT points FROM members WHERE member_id = ?', (replied_user_id,))
                row = await cursor.fetchone()

                # Проверяем, найдены ли баллы для пользователя
                if row:
                    points = row[0]
                    response = f'Участник с ID {replied_user_id} имеет {points} балл(ов)'
                else:
                    response = f'Участник с ID {replied_user_id} не имеет баллов'

                await msg.answer(response, parse_mode=ParseMode.HTML)

    except aiosqlite.Error as e:
        logging.error(f'Ошибка при выполнении запроса: {e}')
        await msg.answer('Произошла ошибка при выполнении запроса.')

async def get_all_member_points():
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT member_id, points FROM members')
                rows = await cursor.fetchall()
                return rows
    except aiosqlite.Error as e:
        logging.error(f'Ошибка при выполнении запроса: {e}')
        return None


async def calculate_toxicity(user_id, user_points, all_member_points):
    total_points = sum(points for _, points in all_member_points)
    user_toxicity = (user_points / total_points) * 100
    return user_toxicity


@router.message(Command('toxicity_stats'))
async def toxicity_stats_command(msg: Message):
    replied_user_id = msg.reply_to_message.from_user.id
    all_member_points = await get_all_member_points()

    if all_member_points:
        user_points = dict(all_member_points).get(replied_user_id)

        if user_points:
            toxicity_percent = await calculate_toxicity(replied_user_id, user_points, all_member_points)
            response = f'Участник с ID {replied_user_id} имеет токсичность на уровне {toxicity_percent:.2f}% по сравнению с другими участниками группы.'
        else:
            response = f'Участник с ID {replied_user_id} не найден в базе данных.'
    else:
        response = 'Произошла ошибка при выполнении запроса для получения данных участников.'

    await msg.answer(response, parse_mode=ParseMode.HTML)

@router.message(Command('chat_stats'))
async def chat_stats(msg: Message):
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                # Выбираем список участников и количество сообщений для каждого из них
                await cursor.execute('SELECT user_id, COUNT(*) FROM messages GROUP BY user_id')
                rows = await cursor.fetchall()

                # Формируем сообщение со статистикой
                stats_message = "Статистика участников:\n"
                for row in rows:
                    user_id, message_count = row
                    user_info = await bot.get_chat_member(msg.chat.id, user_id)
                    username = user_info.user.username if user_info.user.username else user_info.user.first_name
                    stats_message += f"@{username}: {message_count} сообщений\n"

                await msg.answer(stats_message)
    except aiosqlite.Error as e:
        logging.error(f'Ошибка при получении статистики чата: {e}')
        await msg.answer('Произошла ошибка при получении статистики чата.')

@router.message(Command('ban'))
async def ban_toxic(msg: Message):
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    if msg.reply_to_message:
        user_id = msg.reply_to_message.from_user.id
        username = msg.reply_to_message.from_user.first_name
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        if user_status.status.CREATOR:
            try:
                await msg.chat.ban(user_id=user_id)
                await msg.answer(f'Токсик {username} забанен! Давайте вместе бороться с токсичностью!')
            except aiogram.exceptions.TelegramBadRequest as e:
                logging.error(f'Ошибка при выполнении запроса: {e}')
                await msg.answer('Я не хочу банить моего любимого админа!!')
        else:
            await msg.answer('Котик, у тебя недостаточно прав для совершения данного действия')
    else:
        await msg.answer('Если ты хочешь забанить токсика, ответь на его сообщение')

@router.message(Command('unban'))
async def unban_toxic(msg: Message):
    bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    if msg.reply_to_message:
        user_id = msg.reply_to_message.from_user.id
        username = msg.reply_to_message.from_user.first_name
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        if user_status.status.CREATOR:
            await msg.chat.unban(user_id=user_id)
            await msg.answer(f'Токсик {username} разбанен!!')
        else:
            await msg.answer('Котик, у тебя недостаточно прав для совершения данного действия')
    else:
        await msg.answer('Если ты хочешь разбанить токсика, ответь на его сообщение')

@router.message(Command('mute'))
async def mutie(msg: Message):
    if msg.reply_to_message:
        bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
        user_id = msg.reply_to_message.from_user.id
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        username = msg.reply_to_message.from_user.first_name
        chat_id = msg.chat.id
        permissions = types.ChatPermissions(can_send_messages=False, can_send_media_messages=False, can_send_polls=False,
                                      can_send_other_messages=False)

        if user_status.status.ADMINISTRATOR or user_status.status.CREATOR:
            try:
                await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=permissions,
                                               use_independent_chat_permissions=False,
                                               until_date=datetime.timedelta(minutes=3))
                await msg.answer(f'Токсик {username} замьючен!')

            except aiogram.exceptions.TelegramBadRequest as e:
                logging.error(f'Ошибка при выполнении запроса: {e}')
                await msg.answer('Я не хочу мьютить моего любимого админа!!')
        else:
            await msg.answer('Котик, у тебя недостаточно прав для совершения данного действия')
    else:
        await msg.answer('Если ты хочешь замьютить токсика, ответь на его сообщение')

model = joblib.load('model.pkl')
@router.message()
async def predict(msg: Message):
    text = msg.text
    prediction = model.predict([text])
    if prediction == -1:
        await msg.answer(f"Сообщение токсичное")
        await add_toxic_word(msg)

async def toxic_admin(msg: Message):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    table_name = f"chat_{abs(chat_id)}"
    points = 0

    async with aiosqlite.connect('chat_members.db') as conn:
        async with conn.cursor() as cursor:
            # Извлекаем баллы только для указанного пользователя в текущем чате
            await cursor.execute(f'SELECT points FROM {table_name} WHERE member_id = ?', user_id,)
            row = await cursor.fetchone()

            # Проверяем, найдены ли баллы для пользователя
            if row:
                points = row[0]
    if points > 10:
        await mutie(msg)
        await msg.answer('Ты превысил количество токсичных слов, придется тебя замьютить')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
