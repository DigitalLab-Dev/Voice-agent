"""
Database Manager for Digital Lab AI Agent
Supports both SQLite (local dev) and PostgreSQL (production)
Uses SQLAlchemy ORM for database abstraction
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# ========== SQLAlchemy Models ==========

class Conversation(Base):
    """Conversation model"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration = Column(Integer, nullable=True)
    message_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")


class ConversationMetadata(Base):
    """Conversation metadata model for storing call state and custom data"""
    __tablename__ = 'conversation_metadata'
    
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), primary_key=True)
    data = Column(Text, nullable=False)  # JSON string (renamed from 'metadata' to avoid SQLAlchemy conflict)


# ========== Database Manager ==========

class ConversationDatabase:
    """Manages database for conversation history - supports SQLite and PostgreSQL"""
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection
        
        Args:
            db_url: Database URL. If None, uses environment variable DATABASE_URL (Railway)
                   or defaults to SQLite
        """
        if db_url is None:
            # Check for Railway PostgreSQL
            db_url = os.getenv('DATABASE_URL')
            
            # Railway provides postgres:// but SQLAlchemy needs postgresql://
            if db_url and db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            # Fallback to SQLite for local development
            if not db_url:
                db_path = os.path.join(os.path.dirname(__file__), 'conversations.db')
                db_url = f'sqlite:///{db_path}'
        
        logger.info(f"Initializing database with URL: {db_url.split('@')[0]}...")  # Hide credentials
        
        # Create engine
        if 'sqlite' in db_url:
            # SQLite-specific settings
            self.engine = create_engine(db_url, connect_args={'check_same_thread': False})
        else:
            # PostgreSQL settings
            self.engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=300  # Recycle connections after 5 minutes
            )
        
        # Create scoped session
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def create_conversation(self, agent_id: int = None) -> int:
        """Create a new conversation and return its ID"""
        session = self.Session()
        try:
            conversation = Conversation(
                agent_id=agent_id,
                timestamp=datetime.now(),
                message_count=0
            )
            session.add(conversation)
            session.commit()
            conversation_id = conversation.id
            return conversation_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise
        finally:
            session.close()
    
    def add_message(self, conversation_id: int, role: str, content: str):
        """Add a message to a conversation"""
        session = self.Session()
        try:
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                timestamp=datetime.now()
            )
            session.add(message)
            
            # Update message count
            conversation = session.query(Conversation).filter_by(id=conversation_id).first()
            if conversation:
                conversation.message_count += 1
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding message: {e}")
            raise
        finally:
            session.close()
    
    def update_conversation(self, conversation_id: int, duration: int = None, 
                          summary: str = None, sentiment: str = None):
        """Update conversation metadata"""
        session = self.Session()
        try:
            conversation = session.query(Conversation).filter_by(id=conversation_id).first()
            if conversation:
                if duration is not None:
                    conversation.duration = duration
                if summary is not None:
                    conversation.summary = summary
                if sentiment is not None:
                    conversation.sentiment = sentiment
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating conversation: {e}")
            raise
        finally:
            session.close()
    
    def get_conversation(self, conversation_id: int) -> Optional[Dict]:
        """Get a conversation by ID"""
        session = self.Session()
        try:
            conversation = session.query(Conversation).filter_by(id=conversation_id).first()
            if conversation:
                return {
                    'id': conversation.id,
                    'agent_id': conversation.agent_id,
                    'timestamp': conversation.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'duration': conversation.duration,
                    'message_count': conversation.message_count,
                    'summary': conversation.summary,
                    'sentiment': conversation.sentiment
                }
            return None
        finally:
            session.close()
    
    def get_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages for a conversation"""
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(
                conversation_id=conversation_id
            ).order_by(Message.timestamp).all()
            
            return [{
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for msg in messages]
        finally:
            session.close()
    
    def get_all_conversations(self, agent_id: int = None, limit: int = 100) -> List[Dict]:
        """Get all conversations, optionally filtered by agent_id"""
        session = self.Session()
        try:
            query = session.query(Conversation)
            
            if agent_id is not None:
                query = query.filter_by(agent_id=agent_id)
            
            conversations = query.order_by(Conversation.timestamp.desc()).limit(limit).all()
            
            return [{
                'id': conv.id,
                'agent_id': conv.agent_id,
                'timestamp': conv.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'duration': conv.duration,
                'message_count': conv.message_count,
                'summary': conv.summary,
                'sentiment': conv.sentiment
            } for conv in conversations]
        finally:
            session.close()
    
    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and all its messages"""
        session = self.Session()
        try:
            conversation = session.query(Conversation).filter_by(id=conversation_id).first()
            if conversation:
                session.delete(conversation)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting conversation: {e}")
            raise
        finally:
            session.close()
    
    def get_statistics(self, agent_id: int = None) -> Dict:
        """Get conversation statistics"""
        session = self.Session()
        try:
            query = session.query(Conversation)
            
            if agent_id is not None:
                query = query.filter_by(agent_id=agent_id)
            
            total_conversations = query.count()
            total_messages = query.with_entities(func.sum(Conversation.message_count)).scalar() or 0
            avg_duration = query.with_entities(func.avg(Conversation.duration)).scalar() or 0
            
            return {
                'total_conversations': total_conversations,
                'total_messages': int(total_messages),
                'average_duration': round(float(avg_duration), 2) if avg_duration else 0
            }
        finally:
            session.close()
    
    def get_system_stats(self) -> Dict:
        """Get system-wide statistics (for admin)"""
        session = self.Session()
        try:
            total_conversations = session.query(Conversation).count()
            total_messages = session.query(Message).count()
            avg_duration = session.query(func.avg(Conversation.duration)).scalar() or 0
            
            # Get unique agents count (if you have an agents table, adjust accordingly)
            unique_agents = session.query(Conversation.agent_id).distinct().count()
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'average_duration': round(float(avg_duration), 2) if avg_duration else 0,
                'active_agents': unique_agents
            }
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        self.Session.remove()
        self.engine.dispose()
    
    # ========== Metadata Management ==========
    
    def update_conversation_metadata(self, conversation_id: int, metadata: Dict):
        """Store metadata like start_time and system_prompt for conversations"""
        import json
        session = self.Session()
        try:
            metadata_json = json.dumps(metadata)
            
            # Check if metadata exists
            existing = session.query(ConversationMetadata).filter_by(
                conversation_id=conversation_id
            ).first()
            
            if existing:
                existing.data = metadata_json
            else:
                new_metadata = ConversationMetadata(
                    conversation_id=conversation_id,
                    data=metadata_json
                )
                session.add(new_metadata)
            
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating conversation metadata: {e}")
            raise
        finally:
            session.close()
    
    def get_conversation_metadata(self, conversation_id: int) -> Dict:
        """Retrieve metadata for a conversation"""
        import json
        session = self.Session()
        try:
            metadata = session.query(ConversationMetadata).filter_by(
                conversation_id=conversation_id
            ).first()
            
            if metadata:
                return json.loads(metadata.data)
            return {}
        finally:
            session.close()
