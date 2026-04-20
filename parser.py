import requests
import time
import json
import os
import re
import sqlite3
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# --- Твои настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MIN_BUDGET = 2000
SENT_FILE = "sent_orders.json"

KEYWORDS = [
    "python", "flask", "fastapi", "postgresql", "sql", "sqlalchemy",
    "бот", "telegram", "tg", "api", "парс", "скрипт", "парсер",
    "регистрация", "авторизация", "база данных", "бд",
    "деплой", "автоматизация", "excel", "csv", "json",
    "парсинг", "сбор данных"
]

# --- БАЗА ДАННЫХ ---
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
    c.execute(
        "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (order_id, platform, title, budget, link)
    )
    conn.commit()
    conn.close()

# --- ФУНКЦИЯ АВТООТКЛИКА ---
def auto_respond(order_url):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()
    chrome_options.binary_location = r"C:\Users\Yagami Light\AppData\Local\Vivaldi\Application\vivaldi.exe"

    chromedriver_path = r"C:\kwork_bot\chromedriver.exe"
    service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(order_url)
    time.sleep(3)

    try:
        message_box = driver.find_element(By.NAME, "response")

        template = (
            "Здравствуйте! Сделаю под ключ. Мой стек: Python, Flask, парсинг, "
            "Telegram-боты. Пример работы: веб-игра с регистрацией и БД "
            "(ссылка в портфолио). Цена от 3000 ₽, срок 2–4 дня. Готов обсудить."
        )

        message_box.send_keys(template)

        submit_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Откликнуться')]"
        )
        submit_button.click()

        print(f"✅ Автоотклик отправлен на {order_url}")

    except Exception as e:
        print(f"❌ Ошибка при автоотклике: {e}")

    time.sleep(2)
    driver.quit()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def load_sent_orders():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent_orders(sent_orders):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent_orders), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def extract_budget(text):
    match = re.search(r'(\d+)', text.replace(" ", ""))
    return int(match.group(1)) if match else None

# --- ПАРСИНГ KWORK ---
def check_kwork():
    url = "https://kwork.ru/projects"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    project = soup.find("div", class_="project-card")
    if not project:
        return None

    title = project.find("a").text.strip()
    link = "https://kwork.ru" + project.find("a")["href"]

    budget_text = project.text
    budget = extract_budget(budget_text)

    if budget and budget < MIN_BUDGET:
        return None

    if not any(k.lower() in title.lower() for k in KEYWORDS):
        return None

    order_id = link.split("/")[-1]

    return {
        "order_id": order_id,
        "platform": "Kwork",
        "title": title,
        "budget": budget,
        "link": link
    }

# --- ПАРСИНГ FL.RU ---
def check_fl():
    url = "https://www.fl.ru/projects/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    project = soup.find("div", class_="b-post")
    if not project:
        return None

    title = project.find("a").text.strip()
    link = project.find("a")["href"]

    budget_text = project.text
    budget = extract_budget(budget_text)

    if budget and budget < MIN_BUDGET:
        return None

    if not any(k.lower() in title.lower() for k in KEYWORDS):
        return None

    order_id = link.split("/")[-1]

    return {
        "order_id": order_id,
        "platform": "FL",
        "title": title,
        "budget": budget,
        "link": link
    }

# --- ГЛАВНЫЙ ЦИКЛ ---
def main():
    print("🚀 Парсер с автооткликом запущен!")

    init_db()
    sent_orders = load_sent_orders()

    while True:
        for checker in [check_kwork, check_fl]:
            order = checker()

            if order and order["order_id"] not in sent_orders:
                budget_str = f"{order['budget']} ₽" if order['budget'] else "Цена не указана"

                message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ!</b>

📌 <b>{order['platform']}</b> - {order['title']}

💰 {budget_str}

🔗 <a href="{order['link']}">Перейти к заказу</a>
"""

                send_telegram(message)
                print(f"✅ Найден заказ: {order['title'][:50]}")

                auto_respond(order["link"])

                add_order(
                    order["order_id"],
                    order["platform"],
                    order["title"],
                    order["budget"],
                    order["link"]
                )

                sent_orders.add(order["order_id"])
                save_sent_orders(sent_orders)

        time.sleep(60)

if __name__ == "__main__":
    main()