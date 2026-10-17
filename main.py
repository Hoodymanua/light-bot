import os
import io
import base64
import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

TELEGRAM_BOT_TOKEN = "8734121752:AAEZsFdAHEM-UhhediXeb_ZN0lmmpiB6zwc"
GROQ_API_KEY = "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"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

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
        b64_img = base64.b64encode(photo_bytes.getvalue()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
                data = await resp.json()
                if "error" in data:
                    await status.edit_text(f"⚠️ Помилка AI: {data['error'].get('message', data['error'])}")
                    return
                text = data["choices"][0]["message"]["content"]
                await status.edit_text(text)
    except Exception as e:
        await status.edit_text(f"⚠️ Помилка: {e}")

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
