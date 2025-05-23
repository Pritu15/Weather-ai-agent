from database import WeatherHistoryDB
from textblob import TextBlob
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from config import Config
from weather_functions import WeatherFunctions
import nltk
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
import requests

class WeatherAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        self.agent = self._initialize_agent()
        self.db = WeatherHistoryDB()
        self._setup_nltk()

    def _setup_nltk(self):
        """Ensure required NLTK data is downloaded"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
   
    def _initialize_llm(self):
        """Initialize the language model"""
        return ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            google_api_key=Config.GEMINI_API_KEY
            # convert_system_message_to_human=True
        )
    
    def _initialize_agent(self):
        """Initialize the agent with tools"""
        weather_tool = Tool(
            name="GetWeather",
            func=self.get_weather_tool,
            description=(
                "Useful for getting weather information. "
                "Input should contain location and date (today/tomorrow/yesterday/actual date). "
                "Example: 'What's the weather in New York tomorrow?'"
            )
        )
        
        return initialize_agent(
            tools=[weather_tool],
            llm=self.llm,
            agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            early_stopping_method="generate"
        )
    
    def get_weather_tool(self, input_str: str) -> str:
        """Enhanced tool function with better error handling and retry logic"""
        try:
            location, date = self.extract_location_and_date(input_str)
            if not location:
                return "Please specify a valid location."
                
            if not date:
                date = "today"  # Default to today if no date specified
                
            # Get weather data with retry logic
            max_retries = 2
            data = None
            
            for attempt in range(max_retries):
                try:
                    if date == "today":
                        data = WeatherFunctions.get_current_weather(location)
                    elif date == "yesterday":
                        data = WeatherFunctions.get_historical_weather(location)
                    elif date == "tomorrow":
                        data = WeatherFunctions.get_weather_forecast(location)
                    else:  # Actual date string
                        data = WeatherFunctions.get_historical_weather(location)
                    
                    if data:
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        return f"⚠️ Failed to get weather data after {max_retries} attempts: {str(e)}"
                    continue
            
            if not data:
                return "Could not retrieve weather data."
            if date != "yesterday" :    
                response = WeatherFunctions.process_weather_data(data, date)
            else:
                response=WeatherFunctions.process_weather_response_historical(data)
            # Enhanced database logging with sentiment
            # self.db.save_query(
            #     input_str=input_str,
            #     response=response,
            #     location=location,
            #     date=date,
            #     sentiment=TextBlob(input_str).sentiment.polarity
            # )
            
            return response
            
        except Exception as e:
            return f"⚠️ Error processing weather request: {str(e)}"

    def extract_location_and_date(self, prompt: str) -> tuple:
        """Enhanced extraction supporting both relative and absolute dates"""
        try:
            # First try to find date keywords
            date_keywords = {
                "today": "today",
                "tomorrow": "tomorrow",
                "yesterday": "yesterday",
                "now": "today",
                "current": "today"
            }
            
            found_date = None
            for keyword, date_value in date_keywords.items():
                if keyword in prompt.lower():
                    found_date = date_value
                    break
            
            # Extract location using NLP
            location = self._extract_location(prompt)
            
            # If no date keyword found, try to parse actual date
            if not found_date:
                try:
                    blob = TextBlob(prompt)
                    for word, tag in blob.tags:
                        if tag == 'CD':  # Cardinal number (potential date component)
                            try:
                                date_obj = datetime.strptime(word, "%Y-%m-%d").date()
                                today = datetime.now().date()
                                
                                if date_obj == today:
                                    found_date = "today"
                                elif date_obj == today + timedelta(days=1):
                                    found_date = "tomorrow"
                                elif date_obj == today - timedelta(days=1):
                                    found_date = "yesterday"
                                else:
                                    found_date = word  # Use the raw date string
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass
            
            return location, found_date if found_date else "today"
            
        except Exception:
            return None, None

    def _extract_location(self, text: str) -> str:
        """Improved location extraction using NLP with IP fallback"""
        try:
            # First try to extract location using LLM
            model = self._initialize_llm()
            
            chatTemplate = ChatPromptTemplate.from_template(
                "Extract the location from the following text: {text}\n"
                "Return answer in a single word format like 'dhaka', 'newyork', 'paris' etc.\n"
                "Convert abbreviations like 'NY' to 'newyork'.\n"
                "If no location is mentioned, return 'none'."
            )

            messages = chatTemplate.format_messages(text=text)
            response = model(messages)
            location = response.content.strip().lower()
            
            print(f"Extracted location: {location}")

            # If location extraction failed or returned 'none', fall back to IP lookup
            if not location or location == 'none':
                print("Falling back to IP-based location detection")
                location, _ = WeatherFunctions.get_location_from_ip()
                location = location.lower() if location else ""
                print(f"IP-based location: {location}")
            
            return location
            
        except Exception as e:
            print(f"Error in location extraction: {e}")
            try:
                # Fall back to IP lookup if any error occurs
                location, _ = WeatherFunctions.get_location_from_ip()
                return location.lower() if location else ""
            except Exception as e:
                print(f"Error in IP-based location detection: {e}")
                return ""

    def run(self, prompt: str) -> str:
        """Run agent with enhanced context and sentiment analysis"""
        try:
            # Get context from previous queries
            context = self._get_context(prompt)
            
            # Add emoji based on sentiment
            sentiment = TextBlob(prompt).sentiment
            emoji = self._get_sentiment_emoji(sentiment.polarity)
            
            # Run the agent with context if available
            enhanced_prompt = f"{context}\n\nUser: {prompt}" if context else prompt
            response = self.agent.run(enhanced_prompt)
            
            return f"{emoji} {response}"
            
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def _get_context(self, prompt: str) -> str:
        """Get relevant context from history with sentiment filtering"""
        try:
            location = self._extract_location(prompt)
            if not location:
                return ""
                
            current_sentiment = TextBlob(prompt).sentiment.polarity
            
            # Get relevant historical queries
            history = self.db.get_recent_queries(
                location=location,
                limit=3,
                min_sentiment=current_sentiment - 0.3,
                max_sentiment=current_sentiment + 0.3
            )
            
            if not history:
                return ""
                
            context = "Previous related interactions:\n"
            for query in history:
                context += f"- On {query[1]} you asked: '{query[2]}'\n"
                context += f"  I responded: '{query[3]}'\n\n"
                
            return context
            
        except Exception:
            return ""  # Fail silently on context errors

    def _get_sentiment_emoji(self, score: float) -> str:
        """Get emoji based on sentiment score with more granularity"""
        if score > 0.5:
            return "😊"
        elif score > 0.2:
            return "🙂"
        elif score > 0:
            return "😐"
        elif score > -0.2:
            return "😕"
        elif score > -0.5:
            return "😠"
        else:
            return "🤬"