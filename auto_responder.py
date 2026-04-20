import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

def auto_respond(order_url, message_template):
    print(f"🚀 Запускаю браузер для отклика на: {order_url}")
    
    # Путь к твоему ChromeDriver (который ты скачала и положила в папку)
    chromedriver_path = r"C:\kwork_bot\chromedriver.exe"
    service = Service(chromedriver_path)

    # Настройки для Vivaldi
    chrome_options = Options()
    chrome_options.binary_location = r"C:\Users\Yagami Light\AppData\Local\Vivaldi\Application\vivaldi.exe"

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(order_url)
    time.sleep(5)  # Ждём полной загрузки страницы

    try:
        # Пробуем найти поле для отклика (селектор для Kwork)
        # Если не работает, нужно будет уточнить
        response_field = driver.find_element(By.NAME, "response")
        response_field.send_keys(message_template)

        # Находим кнопку отправки
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Откликнуться')]")
        submit_button.click()
        print(f"✅ Отклик отправлен на {order_url}")
    except Exception as e:
        print(f"❌ Ошибка при отправке отклика: {e}")

    time.sleep(3)
    driver.quit()

# --- Твои настройки ---
# Ссылку на заказ ты будешь копировать из Telegram и вставлять сюда
order_link = "ВСТАВЬ_ССЫЛКУ_НА_ЗАКАЗ_СЮДА"
my_message = "Здравствуйте! Сделаю под ключ. Мой стек: Python, Flask, парсинг, Telegram-боты. Пример работы: веб-игра с регистрацией и БД (ссылка в портфолио). Цена от 3000 ₽, срок 2–4 дня. Готов(а) обсудить."

# Запускаем функцию
auto_respond(order_link, my_message)