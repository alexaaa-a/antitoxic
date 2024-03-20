import joblib

dp = Dispatcher
model = joblib.load('model.pkl')

@dp.message_handler()
async def predict(msg: Message):
    text = msg.text
    prediction = model.predict([text])
    if prediction == -1:
        await add_toxic_word(msg)

async def add_toxic_word(msg: Message):
    chat_id = msg.chat.id
    member_id = msg.user.id
    username = msg.user.first_name
    toxic_word = msg.text
    await add_toxic_words(chat_id, member_id, toxic_word)
    async with aiosqlite.connect('chat_members.db') as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                UPDATE members
                SET points = points + 1
                WHERE member_id = ? AND chat_id = ?
            ''', (member_id, chat_id))
            await conn.commit()
    await msg.answer(f"Слово '{toxic_word}' добавлено к пользователю {username} в базу данных и +1 балл участнику.")



@router.message(Command('toxic'))
async def add_word_to_database(msg: Message):
    await create_table_words()

    text = msg.text
    try:
        async with aiosqlite.connect('words.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('''
                    INSERT INTO toxic_message (message)
                    VALUES (?)
                ''', (text,))
                await conn.commit()

                await cursor.execute('SELECT COUNT(message) FROM toxic_message')
                count_message = await cursor.fetchone()
                if count_message == 100:
                    await additional_training(conn)


    except Exception as e:
        print(f"Error adding word to database: {e}")

async def additional_training(conn):
    new_toxic_data = []
    toxic = ["-1"] * 100
    async with conn.execute('SELECT message FROM toxic_message') as cursor:
        async for string in cursor:
            new_toxic_data.append(string[0])
    model.fit(new_toxic_data, toxic)

    await conn.execute('UPDATE toxic_message SET message = NULL')
    await conn.commit()

    joblib.dump(model, 'model.pkl')

    new_toxic_data.append("Доброе утро")









