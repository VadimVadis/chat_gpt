from datetime import datetime

from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import io

# Токен
TOKEN = ''

users = [893685583, 6011446939]
print("Работаю!")


async def bot_start(msg: types.Message):
    await bot.send_message(msg.from_user.id, f'Здравствуйте, {msg.from_user.full_name}!')


@dp.message_handler(content_types=['document'])
async def doc_handler(message: types.Message):
    file_in_io = io.BytesIO()
    await message.reply(text='файл получен, начинаю поиск ошибок...')
    if message.content_type == 'document':
        destination = f"excel/{message.document.file_id}.xlsx"
        await message.document.download(destination_file=file_in_io, destination=destination)
    await message.reply(text='Обработка началась')


@dp.message_handler()
async def bot_hello(msg: types.Message):
    for user in users:
        await bot.send_message(user, f'Здравствуйте, {msg.from_user.full_name}!')


async def start():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())
    executor.start_polling(dp)
    scheduler = AsyncIOScheduler(timexone="Europe/Moscow")
    scheduler.add_job(bot_hello, trigger="cron", hour=datetime.now().hour,
                      minute=datetime.now().minute + 1, start_date=datetime.now())

    @dp.updates_handler(bot_hello, commands=['start'])

if __name__ == '__main__':
    start()
