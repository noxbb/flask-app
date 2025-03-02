import telebot
import requests
from bs4 import BeautifulSoup

# 🔹 Ваши токены
TOKEN = "7985818132:AAFwAdzb_v-mnbi79GBF7W61vdc73T2vl28"
WEATHER_API_KEY = "485c304f7f4a4d2fa49141208250203"
ADMIN_ID = 6706183152
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

bot = telebot.TeleBot(TOKEN)

# 🔹 Функция получения погоды
def get_weather(city="Dnipro"):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=1&lang=ru"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        return "Ошибка получения данных о погоде 😢"

    temp = data["current"]["temp_c"]
    description = data["current"]["condition"]["text"]
    icon = data["current"]["condition"]["icon"]

    return f"🌤 Погода в {city}:\nТемпература: {temp}°C\n{description}\n"

# 🔹 Функция получения курса валют
def get_exchange_rates():
    response = requests.get(EXCHANGE_API_URL)
    data = response.json()
    usd = data["rates"]["UAH"]
    eur = data["rates"]["UAH"] / data["rates"]["EUR"]

    return f"💰 Курс валют:\n1 USD = {round(usd, 2)} UAH\n1 EUR = {round(eur, 2)} UAH"

# 🔹 Функция поиска музыки
def search_music(query):
    url = f"https://ruo.morsmusic.org/search/{query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = soup.find_all("div", class_="track")
    music_list = []

    for track in results[:5]:  # Берём только 5 треков
        title = track.find("div", class_="title").text.strip()
        link = track.find("a", class_="play")["href"]
        full_link = f"https://ruo.morsmusic.org{link}"
        music_list.append(f"🎵 {title}\n🔗 [Скачать]({full_link})")

    if not music_list:
        return "Музыка не найдена 😢"

    return "\n\n".join(music_list)

# 🔹 Команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет, {user_name}! Я могу показать погоду, курс валют и найти музыку 🎶\n\n"
                                      "Команды:\n"
                                      "🌤 /weather - Погода в Днепре\n"
                                      "💰 /exchange - Курс валют\n"
                                      "🎵 /music Название - Найти музыку\n")

    # Уведомление администратору о новом пользователе
    bot.send_message(ADMIN_ID, f"🔔 Новый пользователь: {user_name} (ID: {message.chat.id})")

# 🔹 Команда /weather
@bot.message_handler(commands=['weather'])
def weather_message(message):
    bot.send_message(message.chat.id, get_weather())

# 🔹 Команда /exchange
@bot.message_handler(commands=['exchange'])
def exchange_message(message):
    bot.send_message(message.chat.id, get_exchange_rates())

# 🔹 Команда /music
@bot.message_handler(commands=['music'])
def music_message(message):
    query = message.text.replace("/music", "").strip()
    if not query:
        bot.send_message(message.chat.id, "🎵 Введите название песни после команды /music")
        return

    bot.send_message(message.chat.id, "🔍 Ищу музыку...")
    music_results = search_music(query)
    bot.send_message(message.chat.id, music_results, parse_mode="Markdown")

# 🔹 Запуск бота
bot.polling(none_stop=True)
