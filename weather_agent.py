from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
import requests
from datetime import datetime, timedelta
from config import Config

class WeatherAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.agent = self._initialize_agent()
        
    def _initialize_llm(self):
        return ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            google_api_key=Config.GEMINI_API_KEY,
            convert_system_message_to_human=True
        )
    
    def _initialize_agent(self):
        weather_tool = Tool(
            name="GetWeather",
            func=self.get_weather_tool,
            description=(
                "Useful for getting weather information. "
                "Input should be in format 'location, date' where date is 'today' or 'tomorrow'. "
                "Example: 'New York, today'"
            )
        )
        
        return initialize_agent(
            tools=[weather_tool],
            llm=self.llm,
            agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
    
    def get_current_weather(self, location: str) -> dict:
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
    
    def get_weather_forecast(self, location: str) -> dict:
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
    
    def process_weather_data(self, data: dict, date: str = "today") -> str:
        """Process weather data into human-readable format"""
        if not data:
            return "Could not retrieve weather data."
        
        if date == "today":
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
        else:  # For forecast data
            target_date = (datetime.now() + timedelta(days=1)).date()
            for item in data["list"]:
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
    
    def get_weather_tool(self, input_str: str) -> str:
        """Tool function for the agent to get weather data"""
        parts = [p.strip() for p in input_str.split(",")]
        if len(parts) != 2:
            return "Please specify both location and date (today or tomorrow)"
        
        location, date = parts
        date = date.lower()
        
        if date not in ["today", "tomorrow"]:
            return "Date must be either 'today' or 'tomorrow'"
        
        if date == "today":
            data = self.get_current_weather(location)
        else:  # tomorrow
            data = self.get_weather_forecast(location)
        
        return self.process_weather_data(data, date)
    
    def run(self, prompt: str) -> str:
        """Run the agent with the given prompt"""
        try:
            return self.agent.run(prompt)
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"