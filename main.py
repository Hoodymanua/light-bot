import os
import io
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from google import genai
from PIL import Image

# Читання ключів із середовища хостингу
TELEGRAM_BOT_TOKEN = "8734121752:AAEZsFdAHEM-UhhediXeb_ZN0lmmpiB6zwc"
GEMINI_API_KEY = "AQ.Ab8RN6LkbaA_3MxBpnfhCzhnCgKHbkJlkmzmoR098BBjm6_bLw"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Ти — асистент-координатор для компанії друзів у Львові. Твоє завдання — аналізувати офіційні графіки погодинних відключень «Львівобленерго» із зображення, зіставляти їх із підгрупами учасників і вираховувати спільні слоти зі світлом для спільних ігор чи зідзвонів.

Список учасників та їхні групи Львівобленерго:
- Захар: група 6.1
- Маркіян: група 1.1
- Василь: група 4.1
- Нікіта: група 6.1

Формат відповіді (суворо без вступних слів і привітань):
1. Спільні вікна (Світло є у всіх):
   - Точні проміжки часу, коли у ВСІХ зазначених людей гарантоване світло.
   - Окремо вкажи «умовно стабільні» вікна (де є можливе відключення).
   - Якщо 100% перетину немає: напиши «Ідеального перетину немає» і вкажи слоти, де світло є у більшості (і кого конкретно виб'є).

2. Персональний розклад відключень:
   - Чіткий список без світла по кожній людині на вказану дату:
     - [Ім'я] (група X.X): немає з ЧЧ:ММ до ЧЧ:ММ (зони ризику: ЧЧ:ММ–ЧЧ:ММ).

3. Вердикт для гри:
   - Чітка суха рекомендація: найкращий безперервний слот (наприклад: «Сідаємо грати з 20:00 до 23:00 — гарантовані 3 години без вильотів»).

Суворі обмеження: Жодної зайвої води. Якщо зображення нечітке або обрізане — прямо напиши про це.
"""

@dp.message(F.photo)
async def process_schedule(message: Message):
    status = await message.reply("⏳ Аналізую графік Львівобленерго...")
    try:
        photo = message.photo[-1]
        photo_file = await bot.get_file(photo.file_id)
        
        photo_bytes = io.BytesIO()
        await bot.download_file(photo_file.file_path, destination=photo_bytes)
        photo_bytes.seek(0)
        
        img = Image.open(photo_bytes)

        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[SYSTEM_PROMPT, img]
        )
        
        await status.edit_text(response.text)
    except Exception as e:
        await status.edit_text(f"⚠️ Помилка: {e}")

# Фоновий веб-сервер для хмарного сервісу
async def health_check(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
