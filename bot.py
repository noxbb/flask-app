import telebot
import requests
import time
from bs4 import BeautifulSoup
from flask import Flask, request

# 🔹 Ваши API-ключи
TOKEN = "7985818132:AAFwAdzb_v-mnbi79GBF7W61vdc73T2vl28"
NEWS_API_KEY = "41429bb3e88b44bea3b434ad8ec305ef"
WEATHER_API_KEY = "485c304f7f4a4d2fa49141208250203"
ADMIN_ID = 6706183152
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# 🔹 Запуск Flask (для Webhook)
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

banned_users = {}

# 🔹 Функция получения погоды
def get_weather():
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q=Dnipro&days=1&lang=ru"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        return "Ошибка получения данных о погоде 😢"

    temp = data["current"]["temp_c"]
    description = data["current"]["condition"]["text"]
    return f"🌤 Погода в Днепре:\nТемпература: {temp}°C\n{description}\n"

# 🔹 Функция получения курса валют
def get_exchange_rates():
    response = requests.get(EXCHANGE_API_URL)
    data = response.json()
    usd = data["rates"]["UAH"]
    eur = data["rates"]["UAH"] / data["rates"]["EUR"]

    return f"💰 Курс валют:\n1 USD = {round(usd, 2)} UAH\n1 EUR = {round(eur, 2)} UAH"

# 🔹 Функция получения новостей
def get_news():
    url = f"https://newsapi.org/v2/top-headlines?country=ua&category=general&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "ok":
        return "Ошибка получения новостей 😢"

    articles = data["articles"][:5]
    news_list = []

    for article in articles:
        title = article.get("title", "Без заголовка")
        url = article.get("url", "#")
        news_list.append(f"📰 {title}\n🔗 [Читать]({url})")

    return "\n\n".join(news_list)

# 🔹 Функция поиска музыки через Zaycev.net
def search_music(query):
    url = f"https://zaycev.net/search.html?query_search={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", class_="musicset-track")

    music_list = []
    for track in results[:5]:
        title = track.find("a", class_="musicset-track__title").text.strip()
        link = track.find("a", class_="musicset-track__download")["href"]
        full_link = f"https://zaycev.net{link}"
        music_list.append(f"🎵 {title}\n🔗 [Скачать]({full_link})")

    if not music_list:
        return "Музыка не найдена 😢"

    return "\n\n".join(music_list)

# 🔹 Проверка бана пользователя
def is_banned(user_id):
    if user_id in banned_users:
        if time.time() < banned_users[user_id]:
            return True
        else:
            del banned_users[user_id]
    return False

# 🔹 Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    if is_banned(message.chat.id):
        bot.send_message(message.chat.id, "🚫 Вы временно заблокированы.")
        return

    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет, {user_name}!\n"
                                      "Выберите действие:", reply_markup=main_menu())

    bot.send_message(ADMIN_ID, f"🔔 Новый пользователь: {user_name} (ID: {message.chat.id})")

# 🔹 Кнопки управления
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🌤 Погода"), KeyboardButton("💰 Курс валют"))
    markup.add(KeyboardButton("📰 Новости"), KeyboardButton("🎵 Музыка"))
    if ADMIN_ID:
        markup.add(KeyboardButton("🚫 Блокировка пользователя"))
    return markup

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    if is_banned(message.chat.id):
        bot.send_message(message.chat.id, "🚫 Вы временно заблокированы.")
        return

    if message.text == "🌤 Погода":
        bot.send_message(message.chat.id, get_weather())
    elif message.text == "💰 Курс валют":
        bot.send_message(message.chat.id, get_exchange_rates())
    elif message.text == "📰 Новости":
        bot.send_message(message.chat.id, "📢 Вот важные новости:\n\n" + get_news(), parse_mode="Markdown")
    elif message.text == "🚫 Блокировка пользователя" and message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя и время бана (например, `6706183152 10` для блокировки на 10 минут):")
        bot.register_next_step_handler(message, ban_user)

def ban_user(message):
    try:
        parts = message.text.split()
        user_id = int(parts[0])
        ban_time = int(parts[1]) * 60

        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Нельзя заблокировать администратора!")
            return

        banned_users[user_id] = time.time() + ban_time
        bot.send_message(message.chat.id, f"✅ Пользователь {user_id} заблокирован на {parts[1]} минут.")
        bot.send_message(user_id, f"🚫 Вы заблокированы на {parts[1]} минут.")

    except:
        bot.send_message(message.chat.id, "❌ Неверный формат! Введите ID и время в минутах.")

# 🔹 Webhook для стабильной работы
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/", methods=["GET", "POST"])
def index():
    return "Бот работает!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://flask-app-2ah4.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=3000)
