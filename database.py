import sqlite3
from datetime import datetime
from textblob import TextBlob
import os
from config import Config

class WeatherHistoryDB:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), 'weather_history.db')
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_query TEXT,
                agent_response TEXT,
                location TEXT,
                date_requested TEXT,
                sentiment_score REAL,
                sentiment_label TEXT
            )
        ''')
        self.conn.commit()

    def save_query(self, user_query: str, response: str, location: str, date_requested: str):
        """Save query and response with sentiment analysis"""
        sentiment = self._analyze_sentiment(user_query)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO query_history 
            (user_query, agent_response, location, date_requested, sentiment_score, sentiment_label)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_query, response, location, date_requested, 
              sentiment['score'], sentiment['label']))
        self.conn.commit()

    def get_recent_queries(self, location: str = None, limit: int = 5):
        """Get recent queries, optionally filtered by location"""
        cursor = self.conn.cursor()
        if location:
            cursor.execute('''
                SELECT * FROM query_history 
                WHERE location = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (location.lower(), limit))
        else:
            cursor.execute('''
                SELECT * FROM query_history 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        return cursor.fetchall()

    def _analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of text using TextBlob"""
        analysis = TextBlob(text)
        score = analysis.sentiment.polarity
        
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"
            
        return {"score": score, "label": label}

    def close(self):
        self.conn.close()