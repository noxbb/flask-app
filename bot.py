import os
import time
import requests
import telebot
from flask import Flask, request
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# 🔹 Загружаем переменные из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6706183152))
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# 🔹 Создаём Flask сервер
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)
banned_users = {}

# 🔹 Главное меню (кнопки)
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🌤 Погода"), KeyboardButton("💰 Курс валют"))
    markup.add(KeyboardButton("📰 Новости"), KeyboardButton("🎵 Музыка"))
    if ADMIN_ID:
        markup.add(KeyboardButton("🚫 Блокировка пользователя"))
    return markup

# 🔹 Проверка бана пользователя
def is_banned(user_id):
    if user_id in banned_users:
        if time.time() < banned_users[user_id]:
            return True
        else:
            del banned_users[user_id]
    return False

# 🔹 Функция получения погоды
def get_weather():
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q=Dnipro&days=1&lang=ru"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        return "❌ Ошибка получения данных о погоде."

    temp = data["current"]["temp_c"]
    description = data["current"]["condition"]["text"]
    return f"🌤 Погода в Днепре:\nТемпература: {temp}°C\n{description}"

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
        return "❌ Ошибка получения новостей."

    articles = data["articles"][:5]
    news_list = []
    for article in articles:
        title = article.get("title", "Без заголовка")
        url = article.get("url", "#")
        news_list.append(f"📰 {title}\n🔗 [Читать]({url})")

    return "\n\n".join(news_list)

# 🔹 Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    if is_banned(message.chat.id):
        bot.send_message(message.chat.id, "🚫 Вы временно заблокированы.")
        return

    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет, {user_name}! Выберите действие:", reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"🔔 Новый пользователь: {user_name} (ID: {message.chat.id})")

# 🔹 Обработчик кнопок
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
        bot.send_message(message.chat.id, "📢 Важные новости:\n\n" + get_news(), parse_mode="Markdown")
    elif message.text == "🎵 Музыка":
        bot.send_message(message.chat.id, "Введите название песни после команды /music")
    elif message.text == "🚫 Блокировка пользователя" and message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя и время бана (например, `6706183152 10` для блокировки на 10 минут):")
        bot.register_next_step_handler(message, ban_user)

# 🔹 Webhook для работы на Render
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/", methods=["GET", "POST"])
def index():
    return "Бот работает!", 200

# 🔹 Запуск Webhook
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)  # Ожидание перед установкой нового Webhook
    bot.set_webhook(url=f"https://flask-app-2ah4.onrender.com/{TOKEN}")
    print("✅ Webhook установлен!")
    app.run(host="0.0.0.0", port=3000)
