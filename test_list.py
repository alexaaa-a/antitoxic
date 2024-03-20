
# Команда для вывода слов для конкретного пользователя
@router.message(Command("list"))
async def list_toxic_words(msg: Message):
    if msg.get_args():  # Проверяем, есть ли аргументы у команды
        user_id = msg.get_args().split()[0]  # Получаем аргументы команды (пользователя)
        toxic_words = await get_toxic_words_for_member(user_id)  # Получаем токсичные слова для данного пользователя из базы данных
        if toxic_words:
            await msg.answer(f"Токсичные слова для пользователя {user_id}:\n" + "\n".join(toxic_words))
        else:
            await msg.answer(f"Для пользователя {user_id} нет токсичных слов в базе данных.")
    else:
        await msg.answer("Используйте команду в формате: /list @(пользователь)")

# Команда для вывода всех токсичных слов для всех пользователей
@router.message(Command("list_all"))
async def list_all_toxic_words(msg: Message):
    toxic_words = await get_toxic_words_for_all_members()  # Получаем все токсичные слова для всех пользователей из базы данных
    if toxic_words:
        response = "Токсичные слова для всех пользователей:\n"
        for user_id, words in toxic_words.items():
            response += f"Пользователь {user_id}:\n" + "\n".join(words) + "\n\n"
        await msg.answer(response)
    else:
        await msg.answer("В базе данных нет токсичных слов для пользователей.")

async def get_toxic_words_for_member(chat_id: int, user_id: int):
    try:
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f'''
                    SELECT toxic_words
                    FROM members_{chat_id}
                    WHERE member_id = ?
                ''', (user_id,))
                toxic_words = await cursor.fetchone()
                return toxic_words[0].split(',') if toxic_words else []
    except Exception as e:
        print(f"Error getting toxic words for member {user_id} in chat {chat_id}: {e}")
        return []

async def get_toxic_words_for_all_members():
    try:
        toxic_words_dict = {}
        async with aiosqlite.connect('chat_members.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    SELECT chat_id, member_id, toxic_words
                    FROM members
                ''')
                rows = await cursor.fetchall()
                for row in rows:
                    chat_id, member_id, toxic_words = row
                    if chat_id not in toxic_words_dict:
                        toxic_words_dict[chat_id] = {}
                    toxic_words_dict[chat_id][member_id] = toxic_words.split(',')
        return toxic_words_dict
    except Exception as e:
        print(f"Error getting toxic words for all members: {e}")
        return {}
