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


class User(Base):
    """User authentication model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_verified = Column(Integer, default=0)


class Agent(Base):
    """AI Agent model"""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    business_name = Column(String(255))
    industry = Column(String(100))
    services = Column(Text)
    voice = Column(String(50), default='alloy')
    personality = Column(Text)
    system_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class VerificationCode(Base):
    """Email verification codes"""
    __tablename__ = 'verification_codes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



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
    
    # ========== Auth Management Methods ==========
    
    def create_user(self, email: str, password_hash: str, full_name: str = None) -> int:
        """Create a new user"""
        session = self.Session()
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                is_verified=0
            )
            session.add(user)
            session.commit()
            return user.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(email=email).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'full_name': user.full_name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_verified': user.is_verified
                }
            return None
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'full_name': user.full_name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'is_verified': user.is_verified
                }
            return None
        finally:
            session.close()
    
    def update_user_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating last login: {e}")
        finally:
            session.close()
    
    def verify_user(self, email: str):
        """Mark user as verified"""
        session = self.Session()
        try:
            user = session.query(User).filter_by(email=email).first()
            if user:
                user.is_verified = 1
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error verifying user: {e}")
        finally:
            session.close()
    
    def count_users(self) -> int:
        """Get total user count"""
        session = self.Session()
        try:
            return session.query(User).count()
        finally:
            session.close()
    
    def get_all_users_with_agents(self) -> List[Dict]:
        """Get all users with their agent count"""
        session = self.Session()
        try:
            from sqlalchemy import func
            results = session.query(
                User.id,
                User.email,
                User.full_name,
                User.created_at,
                func.count(Agent.id).label('agent_count')
            ).outerjoin(Agent, User.id == Agent.user_id)\
             .group_by(User.id, User.email, User.full_name, User.created_at)\
             .order_by(User.created_at.desc())\
             .all()
            
            users = []
            for row in results:
                users.append({
                    'id': row.id,
                    'email': row.email,
                    'full_name': row.full_name,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'agent_count': row.agent_count
                })
            return users
        finally:
            session.close()
    
    # Agent methods
    def create_agent(self, user_id: int, name: str, **kwargs) -> int:
        """Create a new agent"""
        session = self.Session()
        try:
            agent = Agent(
                user_id=user_id,
                name=name,
                business_name=kwargs.get('business_name'),
                industry=kwargs.get('industry'),
                services=kwargs.get('services'),
                voice=kwargs.get('voice', 'alloy'),
                personality=kwargs.get('personality'),
                system_prompt=kwargs.get('system_prompt')
            )
            session.add(agent)
            session.commit()
            return agent.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating agent: {e}")
            raise
        finally:
            session.close()
    
    def get_agent(self, agent_id: int) -> Optional[Dict]:
        """Get agent by ID"""
        session = self.Session()
        try:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if agent:
                return {
                    'id': agent.id,
                    'user_id': agent.user_id,
                    'name': agent.name,
                    'business_name': agent.business_name,
                    'industry': agent.industry,
                    'services': agent.services,
                    'voice': agent.voice,
                    'personality': agent.personality,
                    'system_prompt': agent.system_prompt,
                    'created_at': agent.created_at.isoformat() if agent.created_at else None
                }
            return None
        finally:
            session.close()
    
    def get_user_agents(self, user_id: int) -> List[Dict]:
        """Get all agents for a user"""
        session = self.Session()
        try:
            agents = session.query(Agent).filter_by(user_id=user_id).all()
            return [{
                'id': a.id,
                'user_id': a.user_id,
                'name': a.name,
                'business_name': a.business_name,
                'industry': a.industry,
                'services': a.services,
                'voice': a.voice,
                'personality': a.personality,
                'system_prompt': a.system_prompt,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in agents]
        finally:
            session.close()
    
    def update_agent(self, agent_id: int, **kwargs):
        """Update agent details"""
        session = self.Session()
        try:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if agent:
                for key, value in kwargs.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating agent: {e}")
        finally:
            session.close()
    
    def delete_agent(self, agent_id: int):
        """Delete an agent"""
        session = self.Session()
        try:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            if agent:
                session.delete(agent)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting agent: {e}")
        finally:
            session.close()
    
    def count_agents(self) -> int:
        """Get total agent count"""
        session = self.Session()
        try:
            return session.query(Agent).count()
        finally:
            session.close()
    
    # Verification code methods
    def create_verification_code(self, email: str, code: str, expires_at: datetime) -> int:
        """Create a verification code"""
        session = self.Session()
        try:
            vc = VerificationCode(
                email=email,
                code=code,
                expires_at=expires_at
            )
            session.add(vc)
            session.commit()
            return vc.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating verification code: {e}")
            raise
        finally:
            session.close()
    
    def get_verification_code(self, email: str, code: str) -> Optional[Dict]:
        """Get verification code"""
        session = self.Session()
        try:
            vc = session.query(VerificationCode).filter_by(
                email=email,
                code=code
            ).first()
            
            if vc:
                return {
                    'id': vc.id,
                    'email': vc.email,
                    'code': vc.code,
                    'expires_at': vc.expires_at.isoformat() if vc.expires_at else None,
                    'created_at': vc.created_at.isoformat() if vc.created_at else None
                }
            return None
        finally:
            session.close()
    
    def delete_verification_code(self, email: str, code: str):
        """Delete a verification code"""
        session = self.Session()
        try:
            session.query(VerificationCode).filter_by(
                email=email,
                code=code
            ).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting verification code: {e}")
        finally:
            session.close()
