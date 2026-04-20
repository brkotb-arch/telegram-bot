from modules.logging import setlogger, logger
from modules.kwork import KworkAPI
from modules.bot import send_order_notification
import json, os
from time import sleep

setlogger("main.log")
kwork = KworkAPI()

# Файл для хранения полученных id кворков
ORDERS_FILE = "orders.json"

def load_orders():
    if os.path.exists(ORDERS_FILE) and os.path.getsize(ORDERS_FILE) > 0:
        try:
            with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения {ORDERS_FILE}: {e}")
    return []

def save_orders(orders):
    try:
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка записи {ORDERS_FILE}: {e}")

def fetch_updates():
    orders = kwork.get_orders()
    if not orders:
        logger.error("Не удалось получить кворки")
        return

    old_orders = load_orders()
    old_ids = {o['id'] for o in old_orders}

    new_orders = [o for o in orders if o['id'] not in old_ids]

    logger.info(f"Найдено {len(new_orders)} новых кворков")

    if not new_orders:
        return
    
    for order in new_orders:
        # Отправляем уведомление с кнопкой
        send_order_notification(order)
        sleep(2)

    all_orders = old_orders + new_orders
    save_orders(all_orders)

# ... (весь остальной код: импорты, функции, load_orders, save_orders, fetch_updates)

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Запускаем health-сервер в отдельном потоке
threading.Thread(target=run_health_server, daemon=True).start()

# ========== ЗАПУСК (твой бесконечный цикл) ==========
if __name__ == "__main__":
    loop = 0
    while True:
        logger.info(f"=== Запущен {loop} цикл ===")
        fetch_updates()
        logger.info(f"=== Цикл {loop} завершён ===")
        loop += 1
        sleep(60 * 5)

if __name__ == "__main__":
    loop = 0
    while True:
        logger.info(f"=== Запущен {loop} цикл ===")
        fetch_updates()
        logger.info(f"=== Цикл {loop} завершён ===")
        loop += 1
        sleep(60 * 5)