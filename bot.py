import telebot
import requests
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# 🔹 Ваши токены
TOKEN = "7985818132:AAFwAdzb_v-mnbi79GBF7W61vdc73T2vl28"
NEWS_API_KEY = "41429bb3e88b44bea3b434ad8ec305ef"
WEATHER_API_KEY = "485c304f7f4a4d2fa49141208250203"
ADMIN_ID = 6706183152
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

bot = telebot.TeleBot(TOKEN)

# 🔹 База временно заблокированных пользователей
banned_users = {}

# 🔹 Главное меню (кнопки)
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🌤 Погода"), KeyboardButton("💰 Курс валют"))
    markup.add(KeyboardButton("📰 Новости"), KeyboardButton("🎵 Музыка"))
    if ADMIN_ID:
        markup.add(KeyboardButton("🚫 Блокировка пользователя"))
    return markup

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
    url = f"https://newsapi.org/v2/top-headlines?country=ua&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    articles = data["articles"][:5]  # Берём 5 новостей

    news_list = [f"📰 {a['title']}\n🔗 [Читать]({a['url']})" for a in articles]
    return "\n\n".join(news_list)

# 🔹 Проверка бана пользователя
def is_banned(user_id):
    if user_id in banned_users:
        if time.time() < banned_users[user_id]:  # Проверяем время разблокировки
            return True
        else:
            del banned_users[user_id]  # Разблокируем, если время истекло
    return False

# 🔹 Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    if is_banned(message.chat.id):
        bot.send_message(message.chat.id, "🚫 Вы временно заблокированы.")
        return

    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет, {user_name}! Выберите действие:", reply_markup=main_menu())

    # Уведомление админу
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
        bot.send_message(message.chat.id, "📢 Вот важные новости:\n\n" + get_news(), parse_mode="Markdown")
    elif message.text == "🚫 Блокировка пользователя" and message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя и время бана (например, `6706183152 10` для блокировки на 10 минут):")
        bot.register_next_step_handler(message, ban_user)

# 🔹 Функция блокировки пользователей
def ban_user(message):
    try:
        parts = message.text.split()
        user_id = int(parts[0])
        ban_time = int(parts[1]) * 60  # Преобразуем в секунды

        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Нельзя заблокировать администратора!")
            return

        banned_users[user_id] = time.time() + ban_time
        bot.send_message(message.chat.id, f"✅ Пользователь {user_id} заблокирован на {parts[1]} минут.")
        bot.send_message(user_id, f"🚫 Вы заблокированы на {parts[1]} минут.")

    except:
        bot.send_message(message.chat.id, "❌ Неверный формат! Введите ID и время в минутах.")

# 🔹 Запуск бота
bot.polling(none_stop=True)
