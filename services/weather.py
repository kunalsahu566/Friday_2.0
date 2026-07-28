import json
import os
import urllib.error
import urllib.parse
import urllib.request

import settings  # Loads the optional project .env before reading the weather key.

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city):
    if not city:
        return "I need a city name to check the weather. Try 'weather in London'."
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather needs an OpenWeather API key. Add OPENWEATHER_API_KEY to your environment first."
    query = urllib.parse.urlencode({"q": city, "appid": api_key, "units": "metric"})
    try:
        with urllib.request.urlopen(f"{WEATHER_URL}?{query}", timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        return f"It's currently {round(data['main']['temp'])} degrees in {data['name']}, feels like {round(data['main']['feels_like'])} degrees, with {data['weather'][0]['description']}."
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return f"I couldn't find a city called {city}. Please check the spelling."
        return "I couldn't reach the weather service right now."
    except urllib.error.URLError:
        return "I couldn't reach the weather service right now. Check your internet connection."
