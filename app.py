import streamlit as st
from weather_agent import WeatherAgent

def main():
    # Initialize the agent
    weather_agent = WeatherAgent()
    
    # Streamlit UI Configuration
    st.set_page_config(page_title="Megher Basha", page_icon="🌦️")
    st.title("🌦️ Megher Vasha")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the weather..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.spinner("Checking weather..."):
            response = weather_agent.run(prompt)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if __name__ == "__main__":
    main()