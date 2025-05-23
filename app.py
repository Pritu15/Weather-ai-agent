import os
import streamlit as st
from weather_agent import WeatherAgent
from database import WeatherHistoryDB
from config import Config
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import speech_recognition as sr
import uuid
from datetime import datetime

# Initialize clients
eleven_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
weather_agent = WeatherAgent()
db = WeatherHistoryDB()

def speak_text(text: str):
    audio_generator = eleven_client.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    
    # Convert generator to bytes
    # audio_bytes = b"".join(list(speak_text))
    
    # Save audio for debugging or reuse
    # with open("audio_files/speech.mp3", "wb") as f:
    #     f.write(audio_bytes)
    
    # Play the audio
    play(audio_generator)

def get_voice_input() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak your weather query.")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results; {e}"

def generate_chat_name(prompt: str) -> str:
    """Generate a chat name from the first prompt"""
    location, date = weather_agent.extract_location_and_date(prompt)
    if location and date:
        return f"Weather for {location} on {date}"
    elif location:
        return f"Weather for {location}"
    else:
        return f"Chat - {prompt[:20]}..." if len(prompt) > 20 else prompt

def main():
    st.set_page_config(page_title="Megher Vasha", page_icon="🌦️")
    st.title("🌦️ Megher Vasha - Weather Assistant")
    
    # Initialize session state
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    if "renaming_chat" not in st.session_state:
        st.session_state.renaming_chat = None
    if "new_chat_name" not in st.session_state:
        st.session_state.new_chat_name = ""

    # Load chats from database on first run
    if not st.session_state.chats:
        saved_chats = db.get_all_chats()
        for chat in saved_chats:
            st.session_state.chats[chat['chat_id']] = {
                'name': chat['chat_name'],
                'messages': chat['messages'],  # This now includes all messages
                'created_at': chat['created_at']
            }
    # Sidebar with chat management
    with st.sidebar:
        st.subheader("Chat History")
        
        # Button to create new chat
        if st.button("➕ New Chat"):
            new_chat_id = str(uuid.uuid4())
            st.session_state.chats[new_chat_id] = {
                'name': "New Chat",
                'messages': [],
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.current_chat_id = new_chat_id
            st.rerun()
        
        # List of available chats with rename functionality
        st.write("### Your Chats")
        for chat_id in sorted(
            st.session_state.chats.keys(),
            key=lambda x: st.session_state.chats[x]['created_at'],
            reverse=True
        ):
            chat = st.session_state.chats[chat_id]
            
            if st.session_state.renaming_chat == chat_id:
                new_name = st.text_input(
                    "Rename chat",
                    value=chat['name'],
                    key=f"rename_{chat_id}"
                )
                if st.button("✅ Save", key=f"save_{chat_id}"):
                    st.session_state.chats[chat_id]['name'] = new_name
                    db.update_chat_name(chat_id, new_name)
                    st.session_state.renaming_chat = None
                    st.rerun()
                if st.button("❌ Cancel", key=f"cancel_{chat_id}"):
                    st.session_state.renaming_chat = None
                    st.rerun()
            else:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        chat['name'],
                        key=f"select_{chat_id}",
                        use_container_width=True
                    ):
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                with col2:
                    if st.button("✏️", key=f"rename_btn_{chat_id}"):
                        st.session_state.renaming_chat = chat_id
                        st.rerun()

    # Main chat area
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id)
    
    if current_chat:
        st.subheader(current_chat['name'])
        
        # Display messages for current chat
        for message in current_chat['messages']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input area with voice button
    input_container = st.container()
    with input_container:
        col1, col2 = st.columns([10, 1])
        with col1:
            prompt = st.chat_input("Ask about the weather...", key="text_input")
        with col2:
            voice_clicked = st.button("🎙️", key="voice_button", help="Voice input")

    # Handle voice input
    if voice_clicked:
        prompt = get_voice_input()
        if prompt:
            # If this is the first message in a new chat, generate name
            if not current_chat['messages']:
                chat_name = generate_chat_name(prompt)
                st.session_state.chats[st.session_state.current_chat_id]['name'] = chat_name
                db.update_chat_name(st.session_state.current_chat_id, chat_name)
            
            # Add user message to current chat
            st.session_state.chats[st.session_state.current_chat_id]['messages'].append(
                {"role": "user", "content": prompt}
            )
            
            # Get assistant response
            with st.spinner("Checking weather..."):
                response = weather_agent.run(prompt)
                print(f"Assistant response: {response}")
                speak_text(response)
                print("Speaking response...")
                
            
            # Add assistant response to chat
            st.session_state.chats[st.session_state.current_chat_id]['messages'].append(
                {"role": "assistant", "content": response}
            )
            
            # Save entire chat to database
            db.save_chat(
                chat_id=st.session_state.current_chat_id,
                chat_name=st.session_state.chats[st.session_state.current_chat_id]['name'],
                messages=st.session_state.chats[st.session_state.current_chat_id]['messages']
            )
            
            # Rerun to update display
            st.rerun()

    # Handle text input
    if prompt:
        # If this is the first message in a new chat, generate name
        if not current_chat['messages']:
            chat_name = generate_chat_name(prompt)
            st.session_state.chats[st.session_state.current_chat_id]['name'] = chat_name
            db.update_chat_name(st.session_state.current_chat_id, chat_name)
        
        # Add user message to current chat
        st.session_state.chats[st.session_state.current_chat_id]['messages'].append(
            {"role": "user", "content": prompt}
        )
        
        # Get assistant response
        with st.spinner("Checking weather..."):
            response = weather_agent.run(prompt)
        
        # Add assistant response to chat
        st.session_state.chats[st.session_state.current_chat_id]['messages'].append(
            {"role": "assistant", "content": response}
        )
        
        # Save entire chat to database
        db.save_chat(
            chat_id=st.session_state.current_chat_id,
            chat_name=st.session_state.chats[st.session_state.current_chat_id]['name'],
            messages=st.session_state.chats[st.session_state.current_chat_id]['messages']
        )
        
        # Rerun to update display
        st.rerun()

if __name__ == "__main__":
    main()