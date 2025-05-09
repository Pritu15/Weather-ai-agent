import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from config import Config

class WeatherAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        
    def _initialize_llm(self):
        if Config.LLM_PROVIDER == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,
                google_api_key=Config.GEMINI_API_KEY
            )
        else:
            raise ValueError("Invalid LLM provider specified in config")
            
    def _create_prompt_template(self):
        return ChatPromptTemplate.from_messages([
            ("system", """You are a friendly weather assistant. Provide accurate, concise weather information based on the data provided.
             For questions about yesterday, today, or tomorrow, use the available weather data.
             For metaphorical questions like "rain cats and dogs", interpret them as asking about heavy rain.
             If you don't have data for a specific request, say so politely.
             Keep responses under 2 sentences unless more detail is explicitly requested."""),
            ("human", "{query}"),
            ("ai", "{weather_data}"),
            ("human", "Based on the above, answer this weather query: {user_query}")
        ])
        
    def get_weather_data(self, location: str, date: str) -> Optional[Dict[str, Any]]:
        """Fetch weather data for a location and date"""
        base_url = Config.WEATHER_BASE_URL
        
        try:
            if date == "today":
                url = f"{base_url}/weather?q={location}&appid={Config.WEATHER_API_KEY}&units=metric"
                response = requests.get(url)
                data = response.json()
                return self._process_current_weather(data)
                
            elif date == "tomorrow":
                url = f"{base_url}/forecast?q={location}&appid={Config.WEATHER_API_KEY}&units=metric&cnt=8"
                response = requests.get(url)
                data = response.json()
                return self._process_forecast(data, days_ahead=1)
                
            elif date == "yesterday":
                # Historical data requires paid plan in OpenWeatherMap
                # For demo purposes, we'll return None
                return None
                
            else:
                return None
                
        except requests.RequestException:
            return None
            
    def _process_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process current weather data from API"""
        if data.get("cod") != 200:
            return None
            
        return {
            "location": data.get("name", "Unknown location"),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "date": datetime.fromtimestamp(data["dt"]).strftime("%Y-%m-%d")
        }
        
    def _process_forecast(self, data: Dict[str, Any], days_ahead: int = 1) -> Optional[Dict[str, Any]]:
        """Process forecast data from API"""
        if data.get("cod") != "200":
            return None
            
        # Get forecast for the specified day ahead
        target_date = (datetime.now() + timedelta(days=days_ahead)).date()
        
        for item in data["list"]:
            item_date = datetime.fromtimestamp(item["dt"]).date()
            if item_date == target_date:
                return {
                    "location": data["city"]["name"],
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "humidity": item["main"]["humidity"],
                    "weather": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "wind_speed": item["wind"]["speed"],
                    "date": item_date.strftime("%Y-%m-%d"),
                    "time": datetime.fromtimestamp(item["dt"]).strftime("%H:%M")
                }
                
        return None
        
    def analyze_query(self, query: str) -> Dict[str, str]:
        """Analyze the user query to extract location and date"""
        # Simple analysis - in a real app you'd use more sophisticated NLP
        query_lower = query.lower()
        location = Config.DEFAULT_LOCATION
        date = "today"
        
        if "tomorrow" in query_lower:
            date = "tomorrow"
        elif "yesterday" in query_lower:
            date = "yesterday"
            
        # Simple location detection (very basic)
        location_keywords = ["in ", "at ", "for "]
        for keyword in location_keywords:
            if keyword in query_lower:
                start_idx = query_lower.find(keyword) + len(keyword)
                location = query[start_idx:].split()[0]
                break
                
        return {"location": location, "date": date}
        
    def generate_response(self, query: str) -> str:
        """Generate a weather response for the given query"""
        analysis = self.analyze_query(query)
        weather_data = self.get_weather_data(analysis["location"], analysis["date"])
        
        if not weather_data:
            return "Sorry, I couldn't retrieve weather data for that request."
            
        chain = self.prompt_template | self.llm | StrOutputParser()
        
        response = chain.invoke({
            "query": f"What's the weather like in {analysis['location']} on {analysis['date']}?",
            "weather_data": str(weather_data),
            "user_query": query
        })
        
        return response