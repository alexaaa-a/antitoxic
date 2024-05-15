from pyrogram import Client
import config
api_id = 20255404
api_hash = "ec32a80268164eb3040459daa22477a9"
bot_token = config.BOT_TOKEN


async def get_chat_members(chat_id):
    app = Client("Имя | Бот", api_id=api_id, api_hash=api_hash, bot_token=bot_token, in_memory=True)
    chat_members = []
    await app.start()
    async for member in app.get_chat_members(chat_id):
        chat_members = chat_members + [member.user.id]
    await app.stop()
    return chat_members