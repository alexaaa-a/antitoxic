import sqlite3

try:
    conn = sqlite3.connect("person.db")
    cursor = conn.cursor()

    # Создание пользователя с user_id = 1000
    cursor.execute("INSERT OR IGNORE INTO 'users' ('user_id') VALUES(?)", (1000,))

    # Считывание всех пользователей
    users = cursor.execute("SELECT * FROM 'users'")
    print(users.fetchall())

    # Подтверждение изменений
    conn.commit()

except sqlite3.Error as error:
    print('Error', error)

finally:
    if(conn):
        conn.close()