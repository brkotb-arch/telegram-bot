from loguru import logger
from config import TOKEN, USERID
import telebot
# telebot.apihelper.API_URL = "https://tg-proxy.brkotb.workers.dev"
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(TOKEN)

def send_order_notification(order):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("🔗 Откликнуться", url=order['link'])
    keyboard.add(button)
    
    text = f"""🔔 НОВЫЙ ЗАКАЗ!
    
📌 {order['title']}

💰 {order['price']} ₽

👉 Нажми на кнопку, чтобы открыть заказ
"""
    bot.send_message(chat_id=USERID, text=text, reply_markup=keyboard)