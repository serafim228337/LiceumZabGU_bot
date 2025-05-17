import aiohttp
import logging
import os
from dotenv import load_dotenv

load_dotenv(os.path.join("config", "cfg.env"))


async def get_weather():
    api_key = os.getenv("WEATHER_API_KEY")
    city = os.getenv("WEATHER_CITY", "Chita")
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&lang=ru"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return format_weather(data)
                logging.error(f"Weather API error: {response.status}")
                return "Не удалось получить данные о погоде"
    except Exception as e:
        logging.error(f"Weather request failed: {str(e)}")
        return "Ошибка подключения к сервису погоды"


def format_weather(data):
    location = data['location']
    current = data['current']

    return (
        f"🌦 Погода в {location['name']}:\n"
        f"🌡 Температура: {current['temp_c']}°C (ощущается как {current['feelslike_c']}°C)\n"
        f"☁️ Состояние: {current['condition']['text']}\n"
        f"💧 Влажность: {current['humidity']}%\n"
        f"🌬 Ветер: {current['wind_kph']} км/ч, {current['wind_dir']}\n"
        f"🕒 Последнее обновление: {current['last_updated']}\n"
    )