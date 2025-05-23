

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable LangChain tracing to prevent the error
os.environ["LANGCHAIN_TRACING_V2"] = "false"

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
    WEATHERAPI_BASE_URL2 = "https://api.weatherapi.com/v1"
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ANOTHERAPI_KEY=os.getenv("ANOTHERAPI_KEY")
    
    # Weather API Configuration
    WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    FORECAST_CNT = 8  # Get next 24 hours (3-hour intervals)
    
    # LLM Configuration
    LLM_MODEL = "gemini-1.5-flash"
    LLM_TEMPERATURE = 0.7