import string
from add_in_bd import add_bad_word_to_db

from aiogram.types import Message

from botlogic import views
from botlogic.settings import BAN_WORDS, logger


async def check_message(message: Message):
    contains_ban_word = False

    if message.text:
        message_words = set(message.text.translate(str.maketrans('', '', string.punctuation)).split())
        filtered_message = message.text
        for word in message_words:
            if word.lower() in BAN_WORDS:
                filtered_message = filtered_message.replace(word, "*" * len(word))
                contains_ban_word = True

    if contains_ban_word:
        bad_word = 'плохое_слово'
        add_bad_word_to_db(bad_word)
