import asyncio
import aiosqlite

async def add_toxic_words(chat_id, member_id, toxic_words):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                # Создание таблицы, если ее еще нет
                await create_table(chat_id)

                # Выполнение запроса на добавление токсичного слова
                await cursor.execute(f'''
                    INSERT INTO members_{chat_id} (chat_id, member_id, toxic_words)
                    VALUES (?, ?, ?)
                    ON CONFLICT(chat_id, member_id) DO UPDATE SET toxic_words = COALESCE(toxic_words || ?, toxic_words)
                ''', (chat_id, member_id, toxic_words, ',' + toxic_words))
                await conn.commit()
    except Exception as e:
        print(f"Error adding toxic words: {e}")

# Функция создания таблицы
async def create_table(chat_id):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS members_{chat_id} (
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

asyncio.run(add_toxic_words(chat_id=123, member_id=456, toxic_words="bad_word"))
asyncio.run(add_toxic_words(chat_id=123, member_id=456, toxic_words="lox"))
asyncio.run(add_toxic_words(chat_id=124, member_id=236, toxic_words="haha"))