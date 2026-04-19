import asyncio
import logging
from kwork import KworkBot
from kwork.types import Message

# ТВОИ ДАННЫЕ
LOGIN = "brkotb"
PASSWORD = "doidoius8798DF98FUJDI"

logging.basicConfig(level=logging.INFO)

# Функция, которая запускает бота
async def main():
    # Создаем бота ВНУТРИ асинхронной функции
    bot = KworkBot(login=LOGIN, password=PASSWORD)
    
    @bot.message_handler(on_start=True)
    async def simple_handle(message: Message):
        text = ("Здравствуйте! Мой стек: Python, Flask, PostgreSQL, "
                "Telegram-боты, парсинг, API. Готов обсудить вашу задачу. "
                "Портфолио: ссылка на игру Угадай число")
        await message.answer_simulation(text)
    
    @bot.message_handler(text_contains="бот")
    async def bot_handler(message: Message):
        text = "Вам нужен бот? Могу сделать на Python (aiogram) с БД и платежами"
        await message.answer_simulation(text)
    
    @bot.message_handler(text_contains="парс")
    async def parser_handler(message: Message):
        text = "Парсинг — делаю. requests, BeautifulSoup, Selenium если нужно"
        await message.answer_simulation(text)
    
    await bot.run_bot()

if __name__ == "__main__":
    asyncio.run(main())