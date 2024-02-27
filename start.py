import telebot
from telebot import types
import time

bot = telebot.TeleBot('6612359471:AAGs7LvXMqkan8OjI9H6YG1prp7QUbkH9pw')

stats = {}

@bot.message_handler(commands=['start'])
def buttons(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('/help')
    item2 = types.KeyboardButton('/mute')
    item3 = types.KeyboardButton('/unmute')
    item4 = types.KeyboardButton('/kick')
    item5 = types.KeyboardButton('/stats')
    item6 = types.KeyboardButton('/selfstat')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    markup.add(item4)
    markup.add(item5)
    markup.add(item6)
    bot.send_message(message.chat.id, 'Мяяу!! Я - бот для определения токсиков и душнил в твоих чатах :) Выбери нужную кнопочку и жмякни по ней!', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, '/kick - кикнуть пользователя из чата\n/mute - замьютить пользователя,'
                          'чтобы не токсичил\n/unmute - размьютить пользователя\n/stats - показать'
                          ' статистику токсичных пользователей\n/selfstat - показать свою статистику'
                          ' токсичности')

@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "Я не хочу кикать моего любимого создателя!!")
        else:
            bot.kick_chat_member(chat_id, user_id)
            bot.reply_to(message, f"Токсик {message.reply_to_message.from_user.username} был кикнут")
    else:
        bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение токсика, которого ты хочешь кикнуть")

@bot.message_handler(['mute'])
def mutie(message):
    if message.reply_to_message is not None:
        user_id = message.reply_to_message.from_user.id
        bot.reply_to(message, f'Токсик {user_id} замьючен!')
    else:
        bot.reply_to(message, 'Эта команда должна быть использована в ответ на сообщение токсика!')

@bot.message_handler(commands=['unmute'])
def unmutie(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(chat_id, user_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        bot.reply_to(message, f"Бывший токсик (а может и не бывший) {message.reply_to_message.from_user.username} размьючен")
    else:
        bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение человечка, которого ты хочешь размьютить")

bad_phrases = ['дура', 'клоун', 'как жаль', 'я же говорил', 'иди на', 'иди в ж', 'фу', 'дурак']



@bot.message_handler(func=lambda message: True)
def messages_of_toxic(message):
    for i in bad_phrases:
        if i in message.text:
            user_id = message.from_user.id
            bot.reply_to(message, 'Фу, токсик! +1 в твою копилку токсичных сообщений, отстоооой')
            stats[user_id] = 1

@bot.message_handler(['stats'])
def stats_of_chat(message):
    if len(stats) > 0:
        for key in stats:
            for value in stats:
                bot.reply_to(message, f'Токсик с id {key} натоксичил сегодня {value} раз, отстой!')
    else:
        bot.reply_to(message, 'Пусто блин!')

bot.infinity_polling(none_stop=True)
