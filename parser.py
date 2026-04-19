import requests
import time
import json
import os
import re
import sqlite3
from bs4 import BeautifulSoup

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================================


# Минимальный бюджет (в рублях)
MIN_BUDGET = 2000

# Файл для хранения уже отправленных заказов
SENT_FILE = "sent_orders.json"
# ==========================================

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

# Ключевые слова для поиска
KEYWORDS = [
    "python", "flask", "fastapi", "postgresql", "sql", "sqlalchemy",
    "бот", "telegram", "tg", "api", "парс", "скрипт", "парсер",
    "регистрация", "авторизация", "база данных", "бд", "деплой"
]

def load_sent_orders():
    """Загружает список уже отправленных заказов"""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent_orders(sent_orders):
    """Сохраняет список отправленных заказов"""
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_orders), f, ensure_ascii=False)

def send_telegram(text):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def extract_budget(text):
    """Извлекает бюджет из текста"""
    patterns = [
        r"(\d+[\s]?[\d]*)\s*[₽руб]",
        r"бюджет[:]?\s*(\d+[\s]?[\d]*)",
        r"до\s*(\d+[\s]?[\d]*)",
        r"от\s*(\d+[\s]?[\d]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num = int(match.group(1).replace(" ", ""))
            return num
    return None

def check_kwork():
    """Проверяет заказы на Kwork"""
    url = "https://kwork.ru/projects"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        projects = soup.find_all("div", class_=re.compile("project-card"))
        
        for project in projects[:15]:
            title_elem = project.find("a", class_=re.compile("title"))
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            link = "https://kwork.ru" + title_elem.get("href", "")
            order_id = f"kwork_{link.split('/')[-1]}"
            
            full_text = project.get_text()
            budget = extract_budget(full_text)
            
            if budget and budget < MIN_BUDGET:
                continue
            
            title_lower = title.lower()
            for keyword in KEYWORDS:
                if keyword in title_lower:
                    return {
                        "platform": "Kwork",
                        "title": title[:100],
                        "budget": budget,
                        "link": link,
                        "order_id": order_id
                    }
    except Exception as e:
        print(f"Ошибка парсинга Kwork: {e}")
    return None

def check_fl():
    """Проверяет заказы на FL.ru"""
    url = "https://www.fl.ru/projects/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        projects = soup.find_all("div", class_=re.compile("b-post"))
        
        for project in projects[:15]:
            title_elem = project.find("a", class_=re.compile("post__title"))
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = "https://www.fl.ru" + title_elem.get("href", "")
            order_id = f"fl_{link.split('/')[-1]}"
            
            full_text = project.get_text()
            budget = extract_budget(full_text)
            
            if budget and budget < MIN_BUDGET:
                continue
            
            title_lower = title.lower()
            for keyword in KEYWORDS:
                if keyword in title_lower:
                    return {
                        "platform": "FL.ru",
                        "title": title[:100],
                        "budget": budget,
                        "link": link,
                        "order_id": order_id
                    }
    except Exception as e:
        print(f"Ошибка парсинга FL.ru: {e}")
    return None

def main():
    print("🚀 Парсер заказов запущен!")
    print(f"💰 Минимальный бюджет: {MIN_BUDGET} ₽")
    print(f"🔍 Ключевые слова: {', '.join(KEYWORDS)}")
    print(f"⏱️  Проверка каждые 60 секунд (Kwork + FL.ru)")
    print("-" * 50)
    
    init_db()

    sent_orders = load_sent_orders()
    
    while True:
        # Проверяем Kwork
        order = check_kwork()
        if order and order["order_id"] not in sent_orders:
            budget_str = f"{order['budget']} ₽" if order['budget'] else "Цена не указана"
            message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ!</b>

📌 <b>{order['platform']}</b> - {order['title']}

💰 {budget_str}

🔗 <a href="{order['link']}">Перейти к заказу</a>

⏰ Откликайся быстро!
"""
            send_telegram(message)
            print(f"✅ Найден заказ на {order['platform']}: {order['title'][:50]}")
            add_order(order["order_id"], order["platform"], order["title"], order["budget"], order["link"]) 
            sent_orders.add(order["order_id"])
            save_sent_orders(sent_orders)
        
        # Проверяем FL.ru
        order = check_fl()
        if order and order["order_id"] not in sent_orders:
            budget_str = f"{order['budget']} ₽" if order['budget'] else "Цена не указана"
            message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ!</b>

📌 <b>{order['platform']}</b> - {order['title']}

💰 {budget_str}

🔗 <a href="{order['link']}">Перейти к заказу</a>

⏰ Откликайся быстро!
"""
            send_telegram(message)
            print(f"✅ Найден заказ на {order['platform']}: {order['title'][:50]}")
            add_order(order["order_id"], order["platform"], order["title"], order["budget"], order["link"]) 
            sent_orders.add(order["order_id"])
            save_sent_orders(sent_orders)
        
        time.sleep(60)

if __name__ == "__main__":
    main()