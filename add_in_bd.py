import sqlite3

def add_bad_word_to_db(bad_word):
    # Устанавливаем соединение с базой данных
    conn = sqlite3.connect('bad_words.db')
    cursor = conn.cursor()
    # Добавляем плохое слово в базу данных
    cursor.execute('INSERT INTO bad_words (word) VALUES (?)', (bad_word,))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
