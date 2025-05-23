import requests
from datetime import datetime, timedelta
from config import Config
from typing import Optional, Tuple
from typing import Optional, Tuple
from config import Config
from typing import Dict, Optional
import re
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
    def get_location_from_ip() -> Tuple[Optional[str], Optional[str]]:
        """Get city and country from IP address using ipinfo.io"""
        try:
            res = requests.get("https://ipinfo.io/json", timeout=5)
            res.raise_for_status()  # Raise HTTPError if not 200
            data = res.json()
            city = data.get("city")
            country = data.get("country")
            if not city or not country:
                print("Warning: Incomplete location data:", data)
            return city, country
        except requests.exceptions.RequestException as e:
            print("Network or HTTP error:", e)
        except ValueError as e:
            print("JSON decode error:", e)
        except Exception as e:
            print("Unexpected error:", e)
        return None, None
    @staticmethod
    def get_historical_weather(city: Optional[str] = None, target_date: Optional[datetime] = None, api_key: Optional[str] = None) -> str:
        """
        Get detailed historical weather for a city on a specific date.

        If city is None, attempts to get location from IP.
        If target_date is None, defaults to yesterday.
        """
        print("get_historical_weather called")

        # Default target_date if not provided: yesterday (historical data can't be today or future)
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)

        # Format date for WeatherAPI: yyyy-mm-dd
        date_str = target_date.strftime("%Y-%m-%d")

        # Make sure the target date is not in the future or today
        if target_date.date() >= datetime.now().date():
            return "❌ Historical data is only available for past dates (not today or future)."

        print(f"City: {city}")
        print(f"Date: {date_str}")

        url = "http://api.weatherapi.com/v1/history.json"
        params = {
            "key": Config.ANOTHERAPI_KEY,
            "q": city,
            "dt": date_str,
            "aqi": "no",
            "alerts": "no"
        }

        try:
            res = requests.get(url, params=params)
            data = res.json()
            print(f"API response: {data}")

            if "forecast" not in data or "forecastday" not in data["forecast"]:
                return f"❌ No historical weather data found for {city} on {date_str}."

            day_data = data["forecast"]["forecastday"][0]["day"]

            max_temp = day_data["maxtemp_c"]
            min_temp = day_data["mintemp_c"]
            avg_temp = day_data["avgtemp_c"]
            max_wind = day_data["maxwind_kph"]
            total_precip = day_data["totalprecip_mm"]
            avg_humidity = day_data["avghumidity"]
            condition = day_data["condition"]["text"]

            print(f"Max Temp: {max_temp}°C")
            print(f"Min Temp: {min_temp}°C")
            print(f"Avg Temp: {avg_temp}°C")
            print(f"Max Wind: {max_wind} kph")
            print(f"Total Precipitation: {total_precip} mm")
            print(f"Avg Humidity: {avg_humidity}%")
            print(f"Condition: {condition}")

            return (
                f"📅 Historical weather in {city} on {date_str}:\n"
                f"🌡️ Max Temp: {max_temp}°C\n"
                f"🌡️ Min Temp: {min_temp}°C\n"
                f"🌡️ Avg Temp: {avg_temp}°C\n"
                f"🌬️ Max Wind Speed: {max_wind} kph\n"
                f"💧 Total Precipitation: {total_precip} mm\n"
                f"💧 Avg Humidity: {avg_humidity}%\n"
                f"📖 Condition: {condition}"
            )

        except Exception as e:
            print(f"Exception: {e}")
            return "❌ Error retrieving historical weather."
    @staticmethod
    def process_weather_response_historical(response: str) -> Optional[Dict[str, str]]:
        """
        Process the historical weather response string into a structured dictionary.
        
        Args:
            response: The string response from get_historical_weather function
            
        Returns:
            A dictionary with weather data if successful, None if the response indicates an error
        """
        # Check for error responses
        if response.startswith("❌"):
            return None
        
        # Initialize result dictionary
        weather_data = {}
        
        try:
            # Extract city and date from the first line
            first_line = response.split('\n')[0]
            city_match = re.search(r'in (.+?) on', first_line)
            date_match = re.search(r'on (\d{4}-\d{2}-\d{2})', first_line)
            
            if city_match:
                weather_data['city'] = city_match.group(1)
            if date_match:
                weather_data['date'] = date_match.group(1)
            
            # Extract all weather metrics
            metrics = {
                'Max Temp': 'max_temp',
                'Min Temp': 'min_temp',
                'Avg Temp': 'avg_temp',
                'Max Wind Speed': 'max_wind',
                'Total Precipitation': 'total_precip',
                'Avg Humidity': 'avg_humidity',
                'Condition': 'condition'
            }
            
            for line in response.split('\n')[1:]:
                for display_name, key in metrics.items():
                    if display_name in line:
                        # Extract the value after the colon
                        value = line.split(': ')[1]
                        weather_data[key] = value
                        break
            
            return weather_data
        
        except Exception as e:
            print(f"Error processing weather response: {e}")
            return None
    @staticmethod
    def get_coordinates(city_name: str) -> tuple[float, float] | None:
        """
        Get latitude and longitude for a given city name using the Nominatim API.
        
        Args:
            city_name (str): Name of the city.
            
        Returns:
            tuple: (latitude, longitude) or None if lookup fails.
        """
        geocode_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1
        }


        try:
            response = requests.get(geocode_url, params=params, headers={"User-Agent": "weather-app"})
            response.raise_for_status()
            results = response.json()
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                return lat, lon
            else:
                return None
        except requests.exceptions.RequestException:
            return None

    def get_hourly_weather(self,city_name: str, hours_before: int = 3, hours_after: int = 3) -> dict:
        """
        Fetch hourly weather data for a given city using Open-Meteo's API.
        
        Args:
            city_name (str): Name of the city.
            hours_before (int): Hours before current time.
            hours_after (int): Hours after current time.
        
        Returns:
            dict: Weather data or error message.
        """
        coordinates = self.get_coordinates(city_name)
        if coordinates is None:
            return {"error": f"Could not find coordinates for city: {city_name}"}

        latitude, longitude = coordinates
        now = datetime.utcnow()
        start_date = (now - timedelta(hours=hours_before)).strftime("%Y-%m-%dT%H:%M")
        end_date = (now + timedelta(hours=hours_after)).strftime("%Y-%m-%dT%H:%M")

        weather_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            "start_hour": start_date,
            "end_hour": end_date,
            "timezone": "auto"
        }

        try:
            response = requests.get(weather_url, params=params)
            response.raise_for_status()
            data = response.json()

            hourly_data = {
                "time": data["hourly"]["time"],
                "temperature_2m": data["hourly"]["temperature_2m"],
                "humidity": data["hourly"]["relative_humidity_2m"],
                "wind_speed": data["hourly"]["wind_speed_10m"],
                "precipitation": data["hourly"]["precipitation"]
            }
            return hourly_data

        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except KeyError:
            return {"error": "Unexpected API response format"}
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