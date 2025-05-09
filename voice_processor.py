# filepath: /home/pritu/Projects/Weather-ai-agent/voice_processor.py
import io
import os
import speech_recognition as sr
from pydub import AudioSegment
from elevenlabs import text_to_speech, play  # Removed set_api_key
from config import Config

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def listen(self):
        """Capture voice input and convert to text"""
        with self.microphone as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return None
        except sr.RequestError:
            print("Sorry, speech service is down.")
            return None
            
    def speak(self, text):
        """Convert text to speech and play it"""
        audio = text_to_speech(
            text=text,
            voice="Rachel",
            model="eleven_monolingual_v2",
            api_key=Config.ELEVENLABS_API_KEY  # Pass the API key here
        )
        play(audio)
        
    def text_to_speech(self, text, save_path=None):
        """Convert text to speech and optionally save to file"""
        audio = text_to_speech(
            text=text,
            voice="Rachel",
            model="eleven_monolingual_v2",
            api_key=Config.ELEVENLABS_API_KEY  # Pass the API key here
        )
        
        if save_path:
            with open(save_path, "wb") as f:
                f.write(audio)
                
        return audio