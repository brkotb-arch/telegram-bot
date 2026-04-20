import telebot
import sqlite3
import os
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TOKEN)

DB_FILE = "stats.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id TEXT PRIMARY KEY, platform TEXT, title TEXT, budget INTEGER, link TEXT, found_at TEXT)''')
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

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    import threading
    import os
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")

    def run_health_server():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()

    threading.Thread(target=run_health_server, daemon=True).start()
    init_db()
    print("🤖 Telegram-бот запущен!")
    
    # Запускаем парсер в отдельном потоке
    from parser import main as parser_main
    threading.Thread(target=parser_main, daemon=True).start()

    # Запускаем Telegram-бота
    bot.infinity_polling()
    