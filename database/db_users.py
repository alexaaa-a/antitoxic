import asyncio
import aiosqlite
from start import chat_members

# Асинхронная функция для добавления ID участников в базу данных
async def add_members_to_database(chat_id: int, member_ids: chat_members):
    try:
        # Подключаемся к базе данных SQLite
        async with aiosqlite.connect('chat_members.db') as conn:
            # Создаем курсор для выполнения SQL-запросов
            async with conn.cursor() as cursor:
                # Добавляем ID участников в базу данных
                for member_id in member_ids:
                    await cursor.execute('''
                        INSERT INTO members (chat_id, member_id)
                        VALUES (?, ?)
                    ''', (chat_id, member_id))

                await conn.commit()

    except Exception as e:
        print(f"Error adding members to database: {e}")

# Вызов асинхронной функции для добавления участников в базу данных
asyncio.run(add_members_to_database(123456, chat_members))
