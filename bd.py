from bs4 import BeautifulSoup
import requests
import sqlite3


url='https://mat2.slovaronline.com'

conn = sqlite3.connect('words.db')
cursor = conn.cursor()

bs = BeautifulSoup

cursor.execute('CREATE TABLE IF NOT EXISTS words (word TEXT)')

page = requests.get(url)

print(page.status_code)

filteredWords = []
allWords = []
soup = BeautifulSoup(page.content, 'html.parser')


soup = BeautifulSoup(page.text, "html.parser")

allWords = soup.find('div', class_='row articles-link-list')

if allWords:
    for news_item in allWords.find_all('div'):
        # Проходим по каждому элементу div внутри блока all_news
        filteredWords.append(news_item.get_text())  # Получаем только текст и добавляем его в список

for word in filteredWords:
        cursor.execute('INSERT INTO words VALUES (?)', (word,))

# Сохраняем изменения и закрываем соединение с базой данных
conn.commit()
conn.close()


print('Слова успешно спарсены и сохранены в базу данных.')
