import aiosqlite

async def reset_points(chat_id):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'UPDATE {table_name} SET points = 0')
                await conn.commit()
    except Exception as e:
        print(f"Error resetting points: {e}")

async def drop_table(chat_id):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
                await conn.commit()
    except Exception as e:
        print(f"Error dropping table: {e}")

async def create_table(chat_id: int):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        chat_id INTEGER,
                        member_id TEXT,
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
        await create_table(chat_id)  # Check if table exists
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                for member_id in member_ids:
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
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                await create_table(chat_id)

                # Check if a record with the given chat_id and member_id already exists
                await cursor.execute(f'''
                        SELECT *
                        FROM {table_name}
                        WHERE chat_id = ? AND member_id = ?
                    ''', (chat_id, member_id))
                existing_record = await cursor.fetchone()

                if existing_record:
                    existing_toxic_words = existing_record[2]  # Get current toxic words
                    if existing_toxic_words:
                        new_toxic_words = f'{existing_toxic_words}, {toxic_word}'
                    else:
                        new_toxic_words = toxic_word
                    await cursor.execute(f'''
                            UPDATE {table_name}
                            SET toxic_words = ?,
                                points = points + 1
                            WHERE chat_id = ? AND member_id = ?
                        ''', (new_toxic_words, chat_id, member_id))
                else:
                    # If no record exists, simply add a new record
                    await cursor.execute(f'''
                            INSERT INTO {table_name}(chat_id, member_id, toxic_words, points)
                            VALUES (?, ?, ?, 1)
                        ''', (chat_id, member_id, toxic_word))

                await conn.commit()
                print("Toxic word added successfully.")
    except Exception as e:
        print(f"Error adding toxic word: {e}")

async def get_all_member_points(chat_id: int):
    try:
        table_name = f'chat_{abs(chat_id)}'
        async with aiosqlite.connect('test.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    SELECT member_id, points FROM {table_name}
                ''')
                rows = await cursor.fetchall()
                return rows
    except Exception as e:
        print(f"Error getting member points: {e}")
        return None

async def main():
    chat1_id = -123456789  # Пример отрицательного айди чата
    chat1_members = [111, 222, 333]  # Примеры айди участников
    chat2_id = -987654321  # Пример второго отрицательного айди чата
    chat2_members = [444, 555, 666]  # Примеры айди участников для второго чата
    toxic_word = "пример_токсичного_слова"

    await reset_points(chat1_id)
    await drop_table(chat1_id)
    await create_table(chat1_id)
    await add_members_to_database(chat1_id, chat1_members, points=0)
    await add_toxic_words(chat1_id, chat1_members[0], toxic_word)
    await add_toxic_words(chat1_id, chat1_members[0], toxic_word)
    points_statistics = await get_all_member_points(chat1_id)
    print("Statistics for chat", chat1_id)
    print(points_statistics)

    await reset_points(chat2_id)
    await drop_table(chat2_id)
    await create_table(chat2_id)
    await add_members_to_database(chat2_id, chat2_members, points=0)
    await add_toxic_words(chat2_id, chat2_members[0], toxic_word)
    points_statistics = await get_all_member_points(chat2_id)
    print("Statistics for chat", chat2_id)
    print(points_statistics)

# Пример вызова функции main
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
