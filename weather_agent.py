from database import WeatherHistoryDB
from textblob import TextBlob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from config import Config
from weather_functions import WeatherFunctions
import nltk
from datetime import datetime

class WeatherAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.agent = self._initialize_agent()
        self.db = WeatherHistoryDB()
        self._setup_nltk()

    def _setup_nltk(self):
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')

    # ... [keep existing initialization methods] ...
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
                "Input should be in format 'location, date' where date is 'today', 'tomorrow'or'yesterday'. "
                "Example: 'New York, today'"
            )
        )
        
        return initialize_agent(
            tools=[weather_tool],
            llm=self.llm,
            agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    

    def get_weather_tool(self, input_str: str) -> str:
        """Tool function with history and sentiment support"""
        parts = [p.strip() for p in input_str.split(",")]
        if len(parts) != 2:
            return "Please specify both location and date (today/tomorrow/yesterday)"
        
        location, date = parts
        date = date.lower()
        
        if date not in ["today", "tomorrow", "yesterday"]:
            return "Date must be 'today', 'tomorrow', or 'yesterday'"
        
        # Get weather data
        if date == "today":
            data = WeatherFunctions.get_current_weather(location)
        elif date == "yesterday":
            data = WeatherFunctions.get_yesterdays_weather(location)
        else:
            data = WeatherFunctions.get_weather_forecast(location)
        
        response =WeatherFunctions.process_weather_data(data, date)
        
        # Save to database with sentiment analysis
        self.db.save_query(input_str, response, location, date)
        
        return response
    def extract_location_and_date(self, prompt: str) -> tuple:
        """Extract location and date from the prompt"""
        parts = [p.strip() for p in prompt.split(",")]
        if len(parts) != 2:
            return None, None
        
        location, date = parts
        date = date.lower()
        
        if date not in ["today", "tomorrow", "yesterday"]:
            return location, None
        
        return location, date
    def run(self, prompt: str) -> str:
        """Run agent with context from history and sentiment analysis"""
        try:
            # Get context from previous queries
            context = self._get_context(prompt)
            
            # Add emoji based on sentiment
            sentiment = TextBlob(prompt).sentiment
            emoji = self._get_sentiment_emoji(sentiment.polarity)
            
            # Run the agent
            if context:
                enhanced_prompt = f"{context}\n\nUser: {prompt}"
            else:
                enhanced_prompt = prompt
                
            response = self.agent.run(enhanced_prompt)
            
            return f"{emoji} {response}"
            
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def _get_context(self, prompt: str) -> str:
        """Get relevant context from history"""
        # Extract location from prompt
        location = self._extract_location(prompt)
        if not location:
            return ""
            
        # Get recent queries about this location
        history = self.db.get_recent_queries(location=location)
        if not history:
            return ""
            
        context = "Previous interactions about this location:\n"
        for query in history:
            context += f"- You asked: '{query[2]}' on {query[1]}\n"
            context += f"  I responded: '{query[3]}'\n\n"
            
        return context

    def _extract_location(self, text: str) -> str:
        """Simple location extraction from text"""
        # This is a basic implementation - consider using NER for better results
        common_locations = ["New York", "London", "Paris"]  # Add your common locations
        for loc in common_locations:
            if loc.lower() in text.lower():
                return loc
        return ""

    def _get_sentiment_emoji(self, score: float) -> str:
        """Get emoji based on sentiment score"""
        if score > 0.3:
            return "😊"
        elif score > 0.1:
            return "🙂"
        elif score < -0.3:
            return "😠"
        elif score < -0.1:
            return "😕"
        else:
            return "😐"