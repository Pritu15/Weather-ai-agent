import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Weather API
    WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # ElevenLabs for TTS/STT
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # LLM Configuration
    LLM_PROVIDER = "gemini"  # or "gemini"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Location defaults
    DEFAULT_LOCATION = "New York"
    DEFAULT_LAT = 40.7128
    DEFAULT_LON = -74.0060