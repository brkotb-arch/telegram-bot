import telebot
import sqlite3
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# База данных для статистики
DB_FILE = "stats.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id TEXT PRIMARY KEY, platform TEXT, title TEXT, budget INTEGER, link TEXT, found_at TEXT)''')
    conn.commit()
    conn.close()

def add_order(order_id, platform, title, budget, link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, datetime('now'))",
              (order_id, platform, title, budget, link))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    total = c.fetchone()[0]
    c.execute("SELECT platform, COUNT(*) FROM orders GROUP BY platform")
    platforms = c.fetchall()
    conn.close()
    return total, platforms

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Парсер заказов активен!\n\nКоманды:\n/stats — статистика")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    total, platforms = get_stats()
    text = f"📊 Статистика парсера:\n\nВсего найдено заказов: {total}\n\nПо платформам:\n"
    for platform, count in platforms:
        text += f"• {platform}: {count}\n"
    bot.reply_to(message, text)

if __name__ == "__main__":
    init_db()
    print("🤖 Telegram-бот запущен!")
    bot.infinity_polling()