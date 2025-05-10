import streamlit as st
from weather_agent import WeatherAgent
from database import WeatherHistoryDB  # <- Add this import

def main():
    # Initialize components
    weather_agent = WeatherAgent()
    db = WeatherHistoryDB()  # <- Initialize the database

    # Streamlit UI Configuration
    st.set_page_config(page_title="Megher Vasha", page_icon="🌦️")
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
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.spinner("Checking weather..."):
            response = weather_agent.run(prompt)
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        # Extract location and date info (optional: make this smarter)
        location, date = weather_agent.extract_location_and_date(prompt)

        # Save to DB
        db.save_query(prompt, response, location, date)

    # Optional: display recent queries
    with st.sidebar:
        st.subheader("Recent Queries")
        recent = db.get_recent_queries(limit=5)
        for row in recent:
            st.markdown(f"- **{row[1]}**: {row[2]} ({row[6]})")

    db.close()

if __name__ == "__main__":
    main()
