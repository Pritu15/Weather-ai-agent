from weather_agent import WeatherAgent
from voice_processor import VoiceProcessor
import argparse

def main():
    parser = argparse.ArgumentParser(description="Weather AI Agent")
    parser.add_argument("--voice", action="store_true", help="Enable voice input/output")
    args = parser.parse_args()
    
    agent = WeatherAgent()
    voice_processor = VoiceProcessor() if args.voice else None
    
    print("Weather AI Agent - Type 'exit' to quit")
    
    while True:
        if args.voice:
            print("\nSpeak your weather query...")
            query = voice_processor.listen()
            if query is None:
                continue
        else:
            query = input("\nEnter your weather query: ")
            
        if query.lower() == "exit":
            break
            
        response = agent.generate_response(query)
        
        print(f"\nResponse: {response}")
        
        if args.voice:
            voice_processor.speak(response)
            
if __name__ == "__main__":
    main()