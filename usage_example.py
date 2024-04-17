import joblib

dp = Dispatcher
@dp.message_handler()
async def predict(msg: Message):
    model = joblib.load('model.pkl')
    text = msg.text
    prediction = model.predict([text])
    if prediction == -1:
        await add_toxic_word(msg)

def check_text_in_table(text_to_find, cursor):
    cursor.execute("SELECT * FROM words WHERE word = ?", (text_to_find,))
    rows = cursor.fetchone()

    if rows:
        return False
    return True



@router.message(Command('toxic'))
async def add_word_to_database(msg: Message):
    add_toxic_word(msg)
    await create_table_words()

    text = msg.text
    try:
        async with aiosqlite.connect('words.db') as conn:
            async with conn.cursor() as cursor:
                if check_text_in_table(text, cursor):
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
    new_toxic_data.append("Привет, как дела?", "Доброе утро, как настроение?", "Пока, до встречи!", "Молодец, ты справишься!", "Здравствуй, как твои дела?", "До свидания, будь здоров!", "Отлично, продолжай в том же духе!", "Приветствую, как прошел день?", "Спокойной ночи, приятных снов!", "Удачи, ты сможешь все!", "Вечер добрый, как прошел день?", "До скорой встречи!", "Поздравляю!", "Добрый день, какие у тебя планы?", "Спасибо, что ты есть рядом!", "Доброй ночи!", "Ты молодец, не сомневайся!", "Здравствуй, как прошла неделя?")
    toxic += ["+1"] * len(new_toxic_data)
    model.fit(new_toxic_data, toxic)

    await conn.execute('UPDATE toxic_message SET message = NULL')
    await conn.commit()

    joblib.dump(model, 'model.pkl')











