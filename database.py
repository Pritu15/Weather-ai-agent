import sqlite3
from datetime import datetime
import os
import uuid
from typing import List, Dict, Optional

class WeatherHistoryDB:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), 'weather_history.db')
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Create chats table to store chat metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                chat_name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table to store conversation history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
            )
        ''')
        
        self.conn.commit()

    def save_chat(self, chat_id: str, chat_name: str, messages: List[Dict]):
        """Save or update a chat with its messages"""
        cursor = self.conn.cursor()
        
        # Insert or update chat metadata
        cursor.execute('''
            INSERT OR REPLACE INTO chats (chat_id, chat_name, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (chat_id, chat_name))
        
        # Clear existing messages for this chat
        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        
        # Insert all messages
        for message in messages:
            cursor.execute('''
                INSERT INTO messages (chat_id, role, content)
                VALUES (?, ?, ?)
            ''', (chat_id, message['role'], message['content']))
        
        self.conn.commit()
    def get_all_chats(self) -> List[Dict]:
        """Get all chats with their messages"""
        cursor = self.conn.cursor()
        
        # Get all chats
        cursor.execute('SELECT chat_id, chat_name, created_at FROM chats ORDER BY created_at DESC')
        chats = cursor.fetchall()
        
        full_chats = []
        for chat in chats:
            chat_id, chat_name, created_at = chat
            
            # Get messages for this chat
            cursor.execute('''
                SELECT role, content 
                FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp ASC
            ''', (chat_id,))
            messages = [
                {"role": row[0], "content": row[1]}
                for row in cursor.fetchall()
            ]
            
            full_chats.append({
                'chat_id': chat_id,
                'chat_name': chat_name,
                'created_at': created_at,
                'messages': messages
            })
        
        return full_chats

    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """Get all messages for a specific chat"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
        ''', (chat_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        return messages

    def update_chat_name(self, chat_id: str, new_name: str):
        """Update the name of an existing chat"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE chats
            SET chat_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        ''', (new_name, chat_id))
        self.conn.commit()

    def delete_chat(self, chat_id: str):
        """Delete a chat and all its messages"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
        cursor.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id,))
        self.conn.commit()

    def close(self):
        """Close the database connection"""
        self.conn.close()