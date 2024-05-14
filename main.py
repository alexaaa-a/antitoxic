import logging
from aiogram.client.bot import DefaultBotProperties
import aiogram.exceptions
import joblib
from db import get_chat_members
import datetime
from aiogram import Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import config
import math
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, KICKED, LEFT, \
    RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from aiogram.types import ChatMemberUpdated
from aiogram.filters.command import Command
import asyncio
import random
from messages import *
import aiosqlite
from datetime import datetime
from aiogram import types

router = Router()


@router.message(F.text.lower() == 'привет')
async def welcome(message: Message):
    await message.answer('Напиши /start, и мы начнем!')


bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@router.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.first_name
    user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
    if user_status.status == 'creator':
        try:
            kb = [
                [
                    types.KeyboardButton(text="/help"),
                    types.KeyboardButton(text="/words"),
                    types.KeyboardButton(text="/points"),
                    types.KeyboardButton(text="/stats")
                ],
            ]
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=kb,
                resize_keyboard=True,
            )
            await msg.answer(random.choice(hello))
            await msg.answer('Токсюша — это чат-дружок, который фильтрует негатив и оскорбления. '
                             ' Он предоставляет администраторам группы удобные инструменты для поддержания позитивной и безопасной атмосферы в чате. '
                             ' Единственное, что от вас требуется - назначить Токсюшу администратором. Если кто-то пишет что-то токсичное, бот сразу втыкает и админ может удалить или заблокировать негодяя. '
                             'Мы за позитив и уважение! Присоединяйтесь к нам, будь в безопасном чате без токсичности!🚫🧪'
                             '\nЕсли у вас есть какие-либо предложения по поводу улучшения бота или же сотрудничества, контакты создателей указаны в описании бота🌟🌈' 
                             '\n'
                             '\nНажми /help, чтобы увидеть список команд!')
            chat_id = msg.chat.id
            await reset_and_recreate_table(chat_id)
            chat_members = await get_chat_members(chat_id)
            await add_members_to_database(chat_id, chat_members, points=0)
            await msg.answer(f'Я получил все необходимые данные и готов к работе!', reply_markup=keyboard)
        except aiogram.exceptions.TelegramBadRequest as e:
            logging.error(f'Ошибка при выполнении запроса: {e}')
    else:
        await msg.answer('Котик, у тебя недостаточно прав для запуска бота!')

@router.message(Command('help'))
async def commamds(msg: Message):
    user_id = msg.from_user.id
    user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
    await msg.answer('Список команд бота:')
    if user_status.status == 'creator':
        await msg.answer('/ban - можешь забанить участника:(, только имей в виду, что для этой команды бот должен быть админом!'
                         '\n/unban - можешь разбанить участника, только имей в виду, что для этой команды бот должен быть админом!'
                         '\n/mute - можешь замьютить участника, только имей в виду, что для этой команды бот должен быть админом!\n'
                         '/toxic - можешь добавить это слово в токсичный список\n'
                         '/non_toxic - можешь убрать это слово из токсичного списка\n'
                         '/points - можешь посмотреть сколько у тебя баллов\n'
                         '/stats - можешь посмотреть свою статистику плохих слов\n'
                         '/words - список твоих плохих слов\n')
    elif user_status.status == 'administrator':
        await msg.answer('/mute - можешь замьютить участника, только имей в виду, что для этой команды бот должен быть админом!\n'
                         '/toxic - можешь добавить это слово в токсичный список\n'
                         '/non_toxic - можешь убрать это слово из токсичного списка\n'
                         '/points - можешь посмотреть сколько у тебя баллов\n'
                         '/stats - можешь посмотреть свою статистику плохих слов\n'
                         '/words - список твоих плохих слов\n')
    else:
        await msg.answer('/points - можешь посмотреть сколько у тебя баллов\n'
                         '/stats - можешь посмотреть свою статистику плохих слов\n'
                         '/top - статистика всех участников группы\n'
                         '/words - список твоих плохих слов\n')


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await start_scheduler()
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
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'UPDATE {table_name} SET points = 0')
                await conn.commit()
    except Exception as e:
        print(f"Error resetting points: {e}")


async def drop_table(chat_id):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
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
                        word TEXT,
                        label TEXT
                    )
                ''')
                await conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")


async def reset_and_recreate_table(chat_id):
    await reset_points(chat_id)
    await drop_table(chat_id)
    await create_table(chat_id)


async def additional_training(conn):
    new_toxic_data = []
    labels = []
    async with conn.execute('SELECT word, labels FROM words') as cursor:
        async for string in cursor:
            word, label = string
            new_toxic_data.append(word)
            labels.append(label)
    new_toxic_data.append("Привет, как дела?")
    label += ["+1"]
    new_toxic_data.append("Ты тупой, раз не можешь решить такую простую задачу")
    label += ["-1"]

    model.fit(new_toxic_data, labels)

    await conn.execute('UPDATE words SET word = NULL, label = NULL')
    await conn.commit()

    joblib.dump(model, 'model.pkl')


async def add_word_to_database(word: str, label: str):
    await create_table_words()

    try:
        async with aiosqlite.connect('words.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO words (word, label)
                    VALUES (?, ?)
                ''', (word, label))
                await conn.commit()
                await cursor.execute('SELECT COUNT(word) FROM words')
                count_message = await cursor.fetchone()
                if count_message == 100:
                    await additional_training(conn)

    except Exception as e:
        print(f"Error adding word to database: {e}")


@router.message(Command('toxic'))
async def add_new_tword(msg: Message):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    user_status = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if user_status.status == 'administrator' or user_status.status == 'creator':
        await add_toxic_word(msg.reply_to_message)
        word = msg.reply_to_message.text
        await add_word_to_database(word, "-1")
    else:
        await msg.answer('Солнышко, тебе не хватает прав для совершения этого действия')


@router.message(Command('non_toxic'))
async def add_new_nword(msg: Message):
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    user_status = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
    if user_status.status == 'administrator' or user_status.status == 'creator':
        await delete_toxic_word(msg.reply_to_message)
        word = msg.reply_to_message.text
        await add_word_to_database(word, "+1")
    else:
        await msg.answer('Солнышко, тебе не хватает прав для совершения этого действия')


async def create_table(chat_id: int):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        chat_id INTEGER,
                        member_id INTEGER,
                        toxic_words TEXT,
                        points INTEGER,
                        PRIMARY KEY (chat_id, member_id)
                    )
                ''')
                await conn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")


async def add_members_to_database(chat_id: int, member_ids: list, points: int):
    try:
        await create_table(chat_id)  # Проверка на существование таблицы
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                for member_id in member_ids:
                    if member_id != 6612359471:  # Проверка, что member_id не равен ID вашего бота
                        await cursor.execute(f'''
                                INSERT INTO {table_name} (chat_id, member_id, points)
                                VALUES (?, ?, ?)
                            ''', (chat_id, member_id, points))

                await conn.commit()

    except Exception as e:
        print(f"Error adding members to database: {e}")


async def add_toxic_words(chat_id, member_id, toxic_word):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await create_table(chat_id)

                await cursor.execute(f'''
                        SELECT *
                        FROM {table_name}
                        WHERE chat_id = ? AND member_id = ?
                    ''', (chat_id, member_id))
                existing_record = await cursor.fetchone()

                if existing_record:
                    existing_toxic_words = existing_record[2]
                    if existing_toxic_words:
                        new_toxic_words = f'{existing_toxic_words}, {toxic_word}'
                    else:
                        new_toxic_words = toxic_word
                    await cursor.execute(f'''
                            UPDATE {table_name}
                            SET toxic_words = ?
                            WHERE chat_id = ? AND member_id = ?
                        ''', (new_toxic_words, chat_id, member_id))
                else:
                    await cursor.execute(f'''
                            INSERT INTO {table_name}(chat_id, member_id, toxic_words)
                            VALUES (?, ?, ?)
                        ''', (chat_id, member_id, toxic_word))

                await conn.commit()
    except Exception as e:
        print(f"Error adding toxic word: {e}")


async def add_toxic_word(msg: Message):
    chat_id = msg.chat.id
    table_name = f'chat_{abs(chat_id)}'
    member_id = msg.from_user.id
    username = msg.from_user.first_name
    toxic_word = msg.text
    await add_toxic_words(chat_id, member_id, toxic_word)
    async with aiosqlite.connect('chat_members.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f'''
                        SELECT points 
                        FROM {table_name} 
                        WHERE member_id = ?
                    ''', (member_id,))
            row = await cursor.fetchone()
            if row:
                points = row[0]
                if points > 0:
                    await cursor.execute(f'''
                                UPDATE {table_name}
                                SET points = points + 1
                                WHERE member_id = ? AND chat_id = ?
                            ''', (member_id, chat_id))
                    await conn.commit()
                    success_message = random.choice(success_messages).format(
                        toxic_word=toxic_word,
                        username=username,
                        points=points + 1
                    )
                    await msg.answer(success_message)
                else:
                    await cursor.execute(f'''
                                UPDATE {table_name}
                                SET points = points + 1
                                WHERE member_id = ? AND chat_id = ?
                            ''', (member_id, chat_id))
                    await conn.commit()
                    no_points_message = random.choice(no_points_messages).format(
                        toxic_word=toxic_word,
                        username=username
                    )
                    await msg.answer(no_points_message)
            else:
                print("Ошибка при выполнении запроса.")


async def delete_toxic_words(chat_id, member_id, toxic_word):
    try:

        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await create_table(chat_id)

                await cursor.execute(f'''
                            SELECT *
                            FROM {table_name}
                            WHERE chat_id = ? AND member_id = ?
                        ''', (chat_id, member_id))
                existing_record = await cursor.fetchone()

                if existing_record:
                    existing_toxic_words = existing_record[2]
                    if existing_toxic_words and toxic_word in existing_toxic_words:
                        new_toxic_words = [word for word in existing_toxic_words.split(', ') if word != toxic_word]
                        new_toxic_words_str = ', '.join(new_toxic_words)
                        await cursor.execute(f'''
                                    UPDATE {table_name}
                                    SET toxic_words = ?
                                    WHERE chat_id = ? AND member_id = ?
                                ''', (new_toxic_words_str, chat_id, member_id))
                        await conn.commit()
                    else:
                        print(f"Токсичное слово '{toxic_word}' не найдено у пользователя ")
                else:
                    print(f"Пользователь не найден.")

    except Exception as e:
        print(f"Error deleting toxic word: {e}")

async def delete_toxic_word(msg: Message):
    chat_id = msg.chat.id
    table_name = f'chat_{abs(chat_id)}'
    member_id = msg.from_user.id
    username = msg.from_user.first_name
    toxic_word = msg.text

    await delete_toxic_words(chat_id, member_id, toxic_word)
    async with aiosqlite.connect('chat_members.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f'''
                SELECT points 
                FROM {table_name} 
                WHERE member_id = ?
            ''', (member_id,))
            row = await cursor.fetchone()
            points = row[0] if row else 0

            if points > 0:
                await cursor.execute(f'''
                    UPDATE {table_name}
                    SET points = points - 1
                    WHERE member_id = ? AND chat_id = ?
                ''', (member_id, chat_id))
                await conn.commit()
                await msg.answer(
                    f"Слово '{toxic_word}' удалено у пользователя {username}. Теперь у него {points - 1} баллов.")
            else:
                await msg.answer(f"У пользователя {username} и так нет токсичных сообщений.")


@router.message(Command('points'))
async def show_member_points(msg: Message):
    try:
        member_id = msg.from_user.id
        chat_id = msg.chat.id
        username = msg.from_user.first_name
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    SELECT points 
                    FROM {table_name} 
                    WHERE member_id = ?
                ''', (member_id,))
                row = await cursor.fetchone()
                if row:
                    points = row[0]
                    if points > 0:
                        response = random.choice(more_points).format(username=username, points=points)
                    else:
                        response = random.choice(zero_points).format(username=username)
                else:
                    response = random.choice(zero_points).format(username=username)

                await msg.answer(response, parse_mode=ParseMode.HTML)

    except aiosqlite.Error as e:
        logging.error(f'Ошибка при выполнении запроса: {e}')
        await msg.answer('Произошла ошибка при выполнении запроса.')


async def get_all_member_points(chat_id):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'SELECT member_id, points FROM {table_name}')
                rows = await cursor.fetchall()
                return rows
    except aiosqlite.Error as e:
        logging.error(f'Ошибка при выполнении запроса: {e}')
        return None

async def calculate_toxicity(points, all_member_points):
    total_points = sum(points for _, points in all_member_points)
    user_toxicity = (points / total_points) * 100
    return user_toxicity


@router.message(Command('stats'))
async def toxicity_stats_command(msg: Message):
    replied_user_id = msg.reply_to_message.from_user.id
    chat_id = msg.chat.id
    all_member_points = await get_all_member_points(chat_id)
    username = msg.reply_to_message.from_user.first_name

    if all_member_points:
        user_points = dict(all_member_points).get(replied_user_id)

        if user_points:
            toxicity_percent = await calculate_toxicity(user_points, all_member_points)
            await msg.answer(f"Участник {username} имеет токсичность на уровне {toxicity_percent:.2f}% по сравнению с другими участниками группы.")
        else:
            await msg.answer(f"Участник с ID {username} не найден в базе данных.")
    else:
        await msg.answer('Произошла ошибка при выполнении запроса для получения данных участников.')


async def top():
    async with aiosqlite.connect('chat_members.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f'''
                SELECT name 
                FROM sqlite_master
                WHERE type='table';''')
            tables = await cursor.fetchall()
            tables = tables[1:]

    message_data = []

    for i in range(len(tables)):
        chat_id = int('-' + tables[i][0][5:])
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    SELECT member_id, points 
                    FROM {table_name}''')
                rows = await cursor.fetchall()
                tops = {row[0]: row[1] for row in rows}

        sorted_top = sorted(tops.items(), key=lambda x: x[1], reverse=True)
        if sorted_top[0][1] == 0:
            message_data.append((chat_id, 'Топ пуст... Сначала станьте токсиками!'))
        else:
            message_data.append((chat_id, 'Внимание, друзьяшки! Топ токсичности за сегодня:'))

            for member_id, points in sorted_top:
                chat_member = await bot.get_chat_member(chat_id, member_id)
                username = chat_member.user.first_name
                message_data.append((chat_id, f'{username}: {points} баллов'))

            async with aiosqlite.connect('chat_members.db') as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(f'''
                            SELECT toxic_words 
                            FROM {table_name}
                            WHERE member_id = ?
                        ''', (sorted_top[0][0],))
                    toxic_words = await cursor.fetchone()
            top_member_id = sorted_top[0][0]
            top_chat_member = await bot.get_chat_member(chat_id, top_member_id)
            top_username = top_chat_member.user.first_name
            message_data.append(
                (chat_id, f'{top_username} стал(а) королем токсичности, позор! Токсичные сообщения: {toxic_words[0]}'))

    for chat_id, message in message_data:
        await bot.send_message(chat_id, message)

async def reset_toxic_words():
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = await cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    await cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = await cursor.fetchall()
                    column_names = [column[1] for column in columns]
                    if 'toxic_words' in column_names:
                        await cursor.execute(f'UPDATE {table_name} SET toxic_words = NULL, points = 0')
                await conn.commit()
    except Exception as e:
        print(f"Error resetting toxic words: {e}")

async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_toxic_words, 'cron', hour=0, minute=0)
    scheduler.add_job(top, 'cron', hour=0, minute=0)  # Вызов команды /top в 00:00 каждый день
    scheduler.start()

@router.message(Command('chat_stats'))
async def chat_stats(msg: Message):
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
    if msg.reply_to_message:
        user_id = msg.from_user.id
        username = msg.reply_to_message.from_user.first_name
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        if user_status.status == 'creator':
            try:
                await msg.chat.ban(user_id=msg.reply_to_message.from_user.id)
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
    if msg.reply_to_message:
        user_id = msg.from_user.id
        username = msg.reply_to_message.from_user.first_name
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        if user_status.status == 'creator':
            await msg.chat.unban(user_id=msg.reply_to_message.from_user.id)
            await msg.answer(f'Токсик {username} разбанен!!')
        else:
            await msg.answer('Котик, у тебя недостаточно прав для совершения данного действия')
    else:
        await msg.answer('Если ты хочешь разбанить токсика, ответь на его сообщение')


@router.message(Command('toxic_words'))
async def get_toxic_words(msg: Message):
    try:
        chat_id = msg.chat.id
        table_name = f'chat_{abs(chat_id)}'
        member_id = msg.reply_to_message.from_user.id
        username = msg.reply_to_message.from_user.first_name
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                        SELECT toxic_words 
                        FROM {table_name}
                        WHERE member_id = ?
                    ''', (member_id,))
                toxic_words = await cursor.fetchone()

                if toxic_words[0] is not None:  # Проверяем наличие токсичных слов
                    await msg.answer(f"Токсичные сообщения {username}: {toxic_words[0]}")
                else:
                    await msg.answer(f"Пока что у {username} нет токсичных сообщений! Молодец!")
    except aiosqlite.Error as e:
        logging.error(f'Ошибка при получении токсичных сообщений: {e}')
        await msg.answer('Произошла ошибка при получении токсичных сообщений.')


@router.message(Command('mute'))
async def mutie(msg: Message):
    if msg.reply_to_message:
        user_id = msg.from_user.id
        user_status = await bot.get_chat_member(chat_id=msg.chat.id, user_id=user_id)
        username = msg.reply_to_message.from_user.first_name
        chat_id = msg.chat.id
        permissions = types.ChatPermissions(can_send_messages=False, can_send_media_messages=False,
                                            can_send_polls=False,
                                            can_send_other_messages=False)

        if user_status.status == 'administrator' or user_status.status == 'creator':
            try:
                await bot.restrict_chat_member(chat_id=chat_id, user_id=msg.reply_to_message.from_user.id,
                                               permissions=permissions,
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
        await add_toxic_word(msg)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
