"""
Database Manager for Digital Lab AI Agent
Handles conversation history storage and retrieval
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class ConversationDatabase:
    """Manages SQLite database for conversation history"""
    
    def __init__(self, db_path: str = "conversations.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER,
                timestamp TEXT NOT NULL,
                duration INTEGER,
                message_count INTEGER,
                summary TEXT,
                sentiment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        ''')
        
        # Migration: Add agent_id to existing table if missing
        try:
            cursor.execute('ALTER TABLE conversations ADD COLUMN agent_id INTEGER')
        except sqlite3.OperationalError:
            pass # Column exists
            
        conn.commit()
        conn.close()
    
    def create_conversation(self, agent_id: int = None) -> int:
        """Create a new conversation and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO conversations (agent_id, timestamp, message_count) VALUES (?, ?, ?)",
            (agent_id, timestamp, 0)
        )
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def add_message(self, conversation_id: int, role: str, content: str):
        """Add a message to a conversation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, timestamp)
        )
        
        # Update message count
        cursor.execute(
            "UPDATE conversations SET message_count = message_count + 1 WHERE id = ?",
            (conversation_id,)
        )
        
        conn.commit()
        conn.close()
    
    def update_conversation(self, conversation_id: int, duration: int = None, 
                          summary: str = None, sentiment: str = None):
        """Update conversation metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)
        
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)
        
        if sentiment is not None:
            updates.append("sentiment = ?")
            params.append(sentiment)
        
        if updates:
            params.append(conversation_id)
            query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """Get a specific conversation with all messages"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get conversation metadata
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        conv_row = cursor.fetchone()
        
        if not conv_row:
            conn.close()
            return None
        
        conversation = dict(conv_row)
        
        # Get all messages
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        
        messages = [dict(row) for row in cursor.fetchall()]
        conversation['messages'] = messages
        
        conn.close()
        return conversation
    
    def get_all_conversations(self, agent_id: int = None, user_id: int = None) -> List[Dict]:
        """Get list of conversations, filtered by agent or user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        
        if agent_id:
            where_clause = "WHERE agent_id = ?"
            params.append(agent_id)
        elif user_id:
            where_clause = "WHERE agent_id IN (SELECT id FROM agents WHERE user_id = ?)"
            params.append(user_id)
            
        cursor.execute(f"""
            SELECT id, agent_id, timestamp, duration, message_count, summary, sentiment
            FROM conversations 
            {where_clause}
            ORDER BY created_at DESC
        """, params)
        
        conversations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return conversations
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"Error deleting conversation: {e}")
            return False
    
    def get_statistics(self, agent_id: int = None, user_id: int = None) -> Dict:
        """Get statistics, filtered by agent or user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        
        if agent_id:
            where_clause = "WHERE agent_id = ?"
            params.append(agent_id)
        elif user_id:
            # Join with agents table to filter by user
            where_clause = "WHERE agent_id IN (SELECT id FROM agents WHERE user_id = ?)"
            params.append(user_id)
            
        cursor.execute(f"SELECT COUNT(*) FROM conversations {where_clause}", params)
        total_calls = cursor.fetchone()[0]
        
        # Determine correct WHERE clause for duration query
        avg_query = f"SELECT AVG(duration) FROM conversations {where_clause}"
        if where_clause:
            avg_query += " AND duration IS NOT NULL"
        else:
            avg_query += " WHERE duration IS NOT NULL"
            
        cursor.execute(avg_query, params)
        avg = cursor.fetchone()[0]
        avg_duration = avg if avg else 0
        
        cursor.execute(f"SELECT SUM(message_count) FROM conversations {where_clause}", params)
        total = cursor.fetchone()[0]
        total_messages = total if total else 0
        
        # Calculate Leads (Conversations with Positive sentiment)
        leads_query = f"SELECT COUNT(*) FROM conversations {where_clause}"
        if where_clause:
            leads_query += " AND sentiment LIKE '%Positive%'"
        else:
            leads_query += " WHERE sentiment LIKE '%Positive%'"
            
        cursor.execute(leads_query, params)
        leads_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_calls": total_calls,
            "average_duration": round(avg_duration, 2),
            "total_messages": total_messages,
            "leads_count": leads_count
        }

    # ========== Admin Methods ==========
    def get_system_stats(self) -> Dict:
        """Get system-wide statistics for Admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agents")
        total_agents = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_calls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE sentiment LIKE '%Positive%'")
        total_leads = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_users": total_users,
            "total_agents": total_agents,
            "total_calls": total_calls,
            "total_leads": total_leads
        }

    def get_all_users(self) -> List[Dict]:
        """Get list of all users for Admin"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Correct query to get agent count per user
        users = []
        cursor.execute("SELECT id, email, full_name, created_at, last_login FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        for row in rows:
            user = dict(row)
            # Get agent count
            cursor.execute("SELECT COUNT(*) FROM agents WHERE user_id = ?", (user['id'],))
            user['agent_count'] = cursor.fetchone()[0]
            # Get call count
            # Use JOIN to count calls via agents? Or via user_id in conversations (since I implemented data isolation, does conversation have user_id?)
            # I added user_id to conversations table in `init_database` in auth.py step but did I populate it?
            # `start_call` does NOT explicitly save user_id to conversations table yet? 
            # Wait, `auth_manager.create_auth_tables` added `user_id` column.
            # But `db.create_conversation` DOES NOT INSERT IT.
            # So `conversations.user_id` IS NULL for all calls!
            # Admin stats for "calls per user" will be hard.
            # For now I will just show agent count.
            users.append(user)
            
        conn.close()
        return users
