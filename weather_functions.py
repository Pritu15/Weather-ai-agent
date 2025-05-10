import requests
from datetime import datetime, timedelta
from config import Config

class WeatherFunctions:
    @staticmethod
    def get_current_weather(location: str) -> dict:
        """Get current weather data for a location"""
        url = f"{Config.WEATHER_BASE_URL}/weather"
        params = {
            "q": location,
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        try:
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except requests.RequestException:
            return None
    
    @staticmethod
    def get_weather_forecast(location: str) -> dict:
        """Get weather forecast for a location"""
        url = f"{Config.WEATHER_BASE_URL}/forecast"
        params = {
            "q": location,
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric",
            "cnt": Config.FORECAST_CNT
        }
        
        try:
            response = requests.get(url, params=params)
            return response.json() if response.status_code == 200 else None
        except requests.RequestException:
            return None
    
    @staticmethod
    def get_yesterdays_weather(location: str) -> dict:
        """Get yesterday's weather data for a location"""
        # First get coordinates for the location
        geocode_url = f"{Config.WEATHER_BASE_URL}/weather"
        geocode_params = {
            "q": location,
            "appid": Config.OPENWEATHER_API_KEY
        }
        
        try:
            # Get coordinates for the location
            geo_response = requests.get(geocode_url, params=geocode_params)
            if geo_response.status_code != 200:
                return None
                
            geo_data = geo_response.json()
            lat = geo_data['coord']['lat']
            lon = geo_data['coord']['lon']
            
            # Calculate yesterday's date range (00:00-23:59)
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            start = int(datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0).timestamp())
            end = int(datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59).timestamp())
            
            # Get historical data
            history_url = f"{Config.WEATHER_BASE_URL}/history/city"
            history_params = {
                "lat": lat,
                "lon": lon,
                "type": "hour",
                "start": start,
                "end": end,
                "appid": Config.OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            history_response = requests.get(history_url, params=history_params)
            return history_response.json() if history_response.status_code == 200 else None
        
        except (requests.RequestException, KeyError) as e:
            print(f"Error getting historical data: {str(e)}")
            return None

    @staticmethod
    def process_weather_data(data: dict, date: str = "today", hours_offset: int = 0) -> str:
        """Process weather data into human-readable format"""
        if not data:
            return "Could not retrieve weather data."
        
        if date == "today":
            if hours_offset == 0:
                weather = data["weather"][0]
                main = data["main"]
                wind = data["wind"]
                
                return (
                    f"Weather in {data.get('name', 'Unknown location')}:\n"
                    f"- Condition: {weather['description'].capitalize()}\n"
                    f"- Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                    f"- Humidity: {main['humidity']}%\n"
                    f"- Wind: {wind['speed']} m/s"
                )
            else:
                target_time = datetime.now() + timedelta(hours=hours_offset)
                for item in data.get("list", []):
                    if datetime.fromtimestamp(item["dt"]) == target_time:
                        weather = item["weather"][0]
                        main = item["main"]
                        wind = item["wind"]
                        
                        return (
                            f"Weather in {data['city']['name']} at {target_time.strftime('%Y-%m-%d %H:%M')}:\n"
                            f"- Condition: {weather['description'].capitalize()}\n"
                            f"- Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                            f"- Humidity: {main['humidity']}%\n"
                            f"- Wind: {wind['speed']} m/s"
                        )
                return "No weather data available for the specified time."
        
        elif date == "yesterday":
            target_date = (datetime.now() - timedelta(days=1)).date()
            for item in data.get("list", []):
                if datetime.fromtimestamp(item["dt"]).date() == target_date:
                    weather = item["weather"][0]
                    main = item["main"]
                    wind = item["wind"]
                    
                    return (
                        f"Weather for {data['city']['name']} yesterday:\n"
                        f"- Condition: {weather['description'].capitalize()}\n"
                        f"- Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                        f"- Humidity: {main['humidity']}%\n"
                        f"- Wind: {wind['speed']} m/s"
                    )
            return "No weather data available for yesterday."
        
        else:  # For forecast data (e.g., tomorrow)
            target_date = (datetime.now() + timedelta(days=1)).date()
            for item in data.get("list", []):
                if datetime.fromtimestamp(item["dt"]).date() == target_date:
                    weather = item["weather"][0]
                    main = item["main"]
                    wind = item["wind"]
                    
                    return (
                        f"Weather forecast for {data['city']['name']} tomorrow:\n"
                        f"- Condition: {weather['description'].capitalize()}\n"
                        f"- Temperature: {main['temp']}°C (feels like {main['feels_like']}°C)\n"
                        f"- Humidity: {main['humidity']}%\n"
                        f"- Wind: {wind['speed']} m/s"
                    )
            return "No forecast data available for tomorrow."