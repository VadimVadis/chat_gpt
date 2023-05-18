import logging
import io
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from aiogram.utils import executor
from aiogram import Bot, Dispatcher

import sqlite3
import openai
from pydub import AudioSegment

# Токены
openai.api_key = "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"
TOKEN = '5941193514:AAHaI47TlkBSYAjoDsontrkEmgM493vJyTA'
PAYMENTS_TOKEN = '1744374395:TEST:0f42211fdbd4c4c990de'

# Работа с базой данных
conn = sqlite3.connect('user.db')
cur = conn.cursor()

print("Работаю!")

# Подключение бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# prices
PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=10 * 100)  # в копейках (руб)

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=['start'])
async def bot_start(msg: types.Message):
    if not cur.execute(f"SELECT * FROM users WHERE id_tg ='{msg.from_user.id}';").fetchall():
        cur.execute(
            f"INSERT INTO users(id_tg, name_tg, kolvo_query, count_days) VALUES({msg.from_user.id}, '{msg.from_user.full_name}', 10, 10);")
        conn.commit()
    await bot.send_message(msg.chat.id, f'Привет, {msg.from_user.full_name}! Я Chat gpt! Введите команду /help')


@dp.message_handler(commands=['help'])
async def help(msg: types.Message):
    await bot.send_message(msg.chat.id, f'~~Здравствуй! Я Chat GPT bot~~\n\n'
                                             f'° - "/quest" - Задать вопрос,\n'
                                             f'° - "/image"- Сгенерировать картинку по вашему запросу\n'
                                             f'° - "/buy"- Оформить подписку\n'
                                             f'~~~~~~~~~~~~~~~~')


@dp.message_handler(commands=['quest'])
async def quest(msg: types.Message):
    print(msg.from_user.full_name, msg.text)
    if len(msg.text) > 6:
        await bot.send_message(msg.chat.id, "Запрос обрабатывается...")
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": msg.text[7:]}
                ]
            )
            await bot.send_message(msg.chat.id, completion.choices[0].message.content)
        except Exception:
            await bot.send_message(msg.chat.id, "Что-то пошло не так... Попробуйте иначе задать вопрос или позже")
    else:
        await bot.send_message(msg.chat.id, "Вы забыли написать запрос")


async def audio_to_text(file_path: str) -> str:
    """Принимает путь к аудио файлу, возвращает текст файла."""
    with open(file_path, "rb") as audio_file:
        transcript = await openai.Audio.atranscribe(
            "whisper-1", audio_file
        )
    return transcript["text"]


async def save_voice_as_mp3(voice):
    """Скачивает голосовое сообщение и сохраняет в формате mp3."""
    voice_file_info = await bot.get_file(voice.file_id)
    voice_ogg = io.BytesIO()
    await bot.download_file(voice_file_info.file_path, voice_ogg)
    voice_mp3_path = f"voice_files/voice-{voice.file_unique_id}.mp3"
    AudioSegment.from_file(voice_ogg, format="ogg").export(
        voice_mp3_path, format="mp3"
    )
    return voice_mp3_path


@dp.message_handler(content_types=[ContentType.VOICE])
async def voice_message_handler(msg: types.Message):
    voice_path = await save_voice_as_mp3(msg.voice)
    transcripted_voice_text = await audio_to_text(voice_path)
    await bot.send_message(msg.from_user.id, msg.text)
    if transcripted_voice_text:
        await bot.send_message(msg.chat.id, f'Ваш запрос:"{transcripted_voice_text}"')
        await bot.send_message(msg.chat.id, "Запрос обрабатывается...")
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": msg.text}
                ]
            )
            await bot.send_message(msg.chat.id, completion.choices[0].message.content)
        except Exception:
            await bot.send_message(msg.chat.id, "Что-то пошло не так... Попробуйте иначе задать вопрос или позже")


# Оплата
@dp.message_handler(commands=['image'])
async def image(msg: types.Message):
    print(msg.from_user.full_name, msg.text)
    if len(msg.text) > 6:
        try:
            response = openai.Image.create(
                prompt=msg.text[7:],
                n=1,
                size="1024x1024",
            )
            await bot.send_photo(msg.from_user.id, response["data"][0]["url"])
        except Exception:
            await bot.send_message(msg.chat.id, "Что-то пошло не так... Попробуйте иначе задать вопрос или позже")

    else:
        await bot.send_message(msg.chat.id, "Вы забыли написать запрос")


@dp.message_handler(commands=['buy'])
async def buy(msg: types.Message):
    await bot.send_invoice(msg.from_user.id,
                           title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
                           provider_token=PAYMENTS_TOKEN,
                           currency="rub",
                           photo_url="https://est-nsk.ru/upload/medialibrary/8b5/sistema.jpg",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")


# pre checkout  (must be answered in 10 seconds)
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# successful payment
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(msg: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = msg.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    await bot.send_message(msg.from_user.id,
                           f"Платёж на сумму {msg.successful_payment.total_amount // 100} {msg.successful_payment.currency} прошел успешно!!!")


if __name__ == '__main__':
    executor.start_polling(dp)
