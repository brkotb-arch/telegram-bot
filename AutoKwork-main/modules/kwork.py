from loguru import logger
from config import LOGIN, PASSWORD
import requests
import re
import json, json5
import html

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,pl;q=0.7,de;q=0.6,no;q=0.5",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/119.0.0.0 (Edition Yx 05)",
}


class KworkAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # Загружаем старые cookies, если есть
        try:
            with open("modules/cookies.json", 'r', encoding='utf-8') as f:
                old_cookies = json.load(f)
                self.session.cookies.update(old_cookies)
                logger.info("Подгружены старые cookies")
        except Exception:
            logger.info("Старые cookies не найдены, обновляем...")
            self.update_cookies()


    def update_cookies(self):
        try:
            res = self.session.post(
                "https://kwork.ru/api/user/login",
                data={
                    "g-recaptcha-response": "",
                    "jlog": 1,
                    "l_password": PASSWORD,
                    "l_remember_me": "1",
                    "l_username": LOGIN,
                    "recaptcha_pass_token": "",
                    "track_client_id": False,
                },
            )
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка авторизации: {e}")
            return

        # Сохраняем актуальные cookies в файл
        with open("modules/cookies.json", 'w', encoding='utf-8') as f:
            json.dump(self.session.cookies.get_dict(), f, indent=2)
        logger.info(f"Cookies обновлены: {list(self.session.cookies.get_dict().keys())[:5]}")


    def _get_data(self, page):
        try:
            res = self.session.get(f'https://kwork.ru/projects?a=1&price-from=500&price-to=10000&page={page}')
            res.raise_for_status()
            html = res.text

            with open("fetches/kworks.html", 'w', encoding='utf-8') as f:
                f.write(html)

            data = re.findall(r'window.stateData=(.*?)window.firebaseConfig', html)[0]
            if not data:
                logger.error("window.stateData не найден")
                return None

            data = json5.loads(data[:-1])

            with open("fetches/data.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return data
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Не удалось получить страницу биржи: {e}")
            logger.info("Попытка получить новые cookies")
            self.update_cookies()
            return None

        except Exception as e:
            logger.error(f"Не удалось получить страницу биржи: {e}")
            return None


    def _get_pages(self, data):
        links = data['pagination']['links']
        pages = []
        for link in links:
            try:
                pages.append(int(link['label']))
            except: pass
        return pages


    def get_orders(self):
        first_data = self._get_data(page=1)
        if not first_data:
            return None
        
        pages = self._get_pages(data=first_data)
        if not pages:
            logger.error("Не удалось получить ни одной страницы")
            return None
        
        use_first_data = True
        found_orders = []
        
        # Твои ключевые слова (то, что ты ищешь)
        keywords = ['python', 'flask', 'парсинг', 'бот', 'telegram', 'автоматизация', 'api', 'backend', 'скрипт', 'парсер']
        
        # Минимальная цена (игнорируем дешёвые заказы)
        min_price = 2000

        for page in pages:
            if use_first_data:
                data = first_data
                use_first_data = False
            else:
                data = self._get_data(page)

            orders = data['wantsListData']['pagination']['data']

            for order in orders:
                try:
                    title = order['name'].lower()
                    description = html.unescape(order['description']).lower()
                    price = int(float(order['priceLimit']))
                    
                    # Пропускаем заказы дешевле min_price
                    if price < min_price:
                        continue
                    
                    # Проверяем, есть ли хоть одно ключевое слово в заголовке или описании
                    if not any(keyword in title or keyword in description for keyword in keywords):
                        continue
                    
                    # Если дошли сюда — заказ подходит
                    found_orders.append({
                        "id": order['id'],
                        "title": order['name'],
                        "description": html.unescape(order['description']),
                        "price": price,
                        "max_price": int(float(order['possiblePriceLimit'])),
                        "offers_count": order['kwork_count'],
                        "last_date": order['wantDates']['dateExpire'],
                        "link": f"https://kwork.ru/projects/{order['id']}/view"
                    })
                    logger.info(f"✅ Найден подходящий кворк {order['id']}: {order['name'][:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Не удалось спарсить кворк: {e}")
            
            logger.success(f"Обработана страница {page}, найдено {len(found_orders)} подходящих заказов")
        
        return found_orders