from flask import Flask, render_template
import requests

app = Flask(__name__)

# 🔹 Ваш API-ключ для WeatherAPI
WEATHER_API_KEY = "485c304f7f4a4d2fa49141208250203"
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"  # API курса валют

# 🔹 Функция получения погоды из WeatherAPI
def get_weather():
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q=Dnipro&days=7&lang=ru"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        return {"error": "Ошибка получения данных о погоде"}, []

    # Погода на сегодня
    today_weather = {
        "temp": data["current"]["temp_c"],
        "description": data["current"]["condition"]["text"],
        "icon": data["current"]["condition"]["icon"]
    }

    # Погода на 7 дней
    weekly_weather = []
    for day in data["forecast"]["forecastday"]:
        weekly_weather.append({
            "date": day["date"],
            "temp": day["day"]["avgtemp_c"],
            "description": day["day"]["condition"]["text"],
            "icon": day["day"]["condition"]["icon"]
        })

    return today_weather, weekly_weather

# 🔹 Функция получения курса валют
def get_exchange_rates():
    response = requests.get(EXCHANGE_API_URL)
    data = response.json()
    return {
        "USD": data["rates"]["UAH"],
        "EUR": data["rates"]["UAH"] / data["rates"]["EUR"]
    }

@app.route("/")
def home():
    today_weather, weekly_weather = get_weather()
    exchange_rates = get_exchange_rates()
    return render_template("index.html", today_weather=today_weather, weekly_weather=weekly_weather, exchange_rates=exchange_rates)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
