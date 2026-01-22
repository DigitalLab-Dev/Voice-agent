"""
Authentication System for Digital Lab AI Agent
Handles user authentication, session management, and password security
"""

import bcrypt
import jwt
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

# Secret key for JWT (in production, use environment variable)
JWT_SECRET = os.getenv('JWT_SECRET', 'digital-lab-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_HOURS = 24

class AuthManager:
    """Handles all authentication operations"""
    
    def __init__(self, db_path='conversations.db'):
        self.db_path = db_path
        self.create_auth_tables()
    
    def create_auth_tables(self):
        """Create users and sessions tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                business_name TEXT,
                industry TEXT,
                services TEXT,
                tone TEXT,
                system_prompt TEXT,
                greeting_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Update conversations table to include user_id (handle if column already exists)
        try:
            cursor.execute('ALTER TABLE conversations ADD COLUMN user_id INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass
            
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def create_user(self, email: str, password: str, full_name: str = None) -> dict:
        """Create new user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if email exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                conn.close()
                return {'success': False, 'error': 'Email already registered'}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (email, password_hash, full_name)
                VALUES (?, ?, ?)
            ''', (email, password_hash, full_name))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'full_name': full_name
            }
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, email: str, password: str) -> dict:
        """Authenticate user and return JWT token"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get user
            cursor.execute('''
                SELECT id, email, password_hash, full_name
                FROM users WHERE email = ?
            ''', (email,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                conn.close()
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user['id'],))
            conn.commit()
            conn.close()
            
            # Generate JWT token
            token = self.create_token(user['id'], user['email'])
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }
            }
            
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_token(self, user_id: int, email: str) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXP_DELTA_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {'success': True, 'user_id': payload['user_id'], 'email': payload['email']}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'error': 'Invalid token'}
    
    def get_user(self, user_id: int) -> dict:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, email, full_name, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def get_agent(self, agent_id: int) -> dict:
        """Get specific agent configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
            agent = cursor.fetchone()
            conn.close()
            
            if agent:
                return dict(agent)
            return None
        except Exception as e:
            print(f"Error getting agent: {e}")
            return None

    def get_user_agents(self, user_id: int) -> list:
        """Get all agents for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM agents WHERE user_id = ? ORDER BY id DESC', (user_id,))
            agents = cursor.fetchall()
            conn.close()
            
            return [dict(agent) for agent in agents]
        except Exception as e:
            print(f"Error getting user agents: {e}")
            return []

    def create_agent(self, user_id: int, agent_data: dict) -> bool:
        """Create a new agent for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO agents (user_id, business_name, industry, services, tone, system_prompt, greeting_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                agent_data['business_name'],
                agent_data['industry'],
                agent_data['services'],
                agent_data['tone'],
                agent_data['system_prompt'],
                agent_data['greeting_message']
            ))
            
            agent_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return agent_id
        except Exception as e:
            print(f"Error creating agent: {e}")
            return None

    def update_agent(self, agent_id: int, user_id: int, agent_data: dict) -> bool:
        """Update existing agent"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE agents 
                SET business_name=?, industry=?, services=?, tone=?, system_prompt=?, greeting_message=?
                WHERE id=? AND user_id=?
            ''', (
                agent_data['business_name'],
                agent_data['industry'],
                agent_data['services'],
                agent_data['tone'],
                agent_data['system_prompt'],
                agent_data['greeting_message'],
                agent_id,
                user_id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating agent: {e}")
            return False

# Create global instance
auth_manager = AuthManager()

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        result = auth_manager.verify_token(token)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 401
        
        # Add user info to request
        request.current_user = result
        
        return f(*args, **kwargs)
    
    return decorated_function
