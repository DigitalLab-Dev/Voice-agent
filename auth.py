import os
import jwt
import bcrypt
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'digital-lab-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_HOURS = 24

class AuthManager:
    """Handles all authentication operations using PostgreSQL via database instance"""
    
    def __init__(self, db):
        """
        Initialize with database instance
        Args:
            db: ConversationDatabase instance (uses PostgreSQL on Railway, SQLite locally)
        """
        self.db = db
        # No more SQLite connections! Database tables are created by database.py
    
    def create_auth_tables(self):
        """No-op: Tables are created by database.py Base.metadata.create_all()"""
        pass
    
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
            # Check if email exists
            existing_user = self.db.get_user_by_email(email)
            if existing_user:
                return {'success': False, 'error': 'Email already registered'}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            user_id = self.db.create_user(email, password_hash, full_name)
            
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
            # Get user
            user = self.db.get_user_by_email(email)
            
            if not user:
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Verify password
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid email or password'}
            
            # Update last login
            self.db.update_user_last_login(user['id'])
            
            # Generate JWT token
            token = self.create_token(user['id'], user['email'])
            
            # Check if user is admin
            is_admin = user['email'] == 'syedaliturab@gmail.com'
            redirect_to = '/admin' if is_admin else '/dashboard'
            
            return {
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'is_admin': is_admin
                },
                'redirect_to': redirect_to
            }
            
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_token(self, user_id: int, email: str) -> str:
        """Generate JWT token for user"""
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
            return {
                'valid': True,
                'user_id': payload['user_id'],
                'email': payload['email']
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
    
    def get_user_id_from_email(self, email: str):
        """Get user ID from email"""
        user = self.db.get_user_by_email(email)
        return user['id'] if user else None
    
    def get_user_agents(self, user_id: int):
        """Get all agents for a user"""
        return self.db.get_user_agents(user_id)
    
    def create_agent(self, user_id: int, name: str, **kwargs):
        """Create a new agent"""
        return self.db.create_agent(user_id, name, **kwargs)
    
    def get_agent(self, agent_id: int):
        """Get agent by ID"""
        return self.db.get_agent(agent_id)
    
    def update_agent(self, agent_id: int, **kwargs):
        """Update agent"""
        return self.db.update_agent(agent_id, **kwargs)
    
    def delete_agent(self, agent_id: int):
        """Delete agent"""
        return self.db.delete_agent(agent_id)
    
    def create_verification_code(self, email: str) -> str:
        """Create verification code and return it"""
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(hours=24)
        self.db.create_verification_code(email, code, expires_at)
        return code
    
    def verify_code(self, email: str, code: str) -> bool:
        """Verify verification code"""
        vc = self.db.get_verification_code(email, code)
        if not vc:
            return False
        
        # Check if expired
        expires_at = datetime.fromisoformat(vc['expires_at'])
        if datetime.utcnow() > expires_at:
            self.db.delete_verification_code(email, code)
            return False
        
        # Mark user as verified
        self.db.verify_user(email)
        self.db.delete_verification_code(email, code)
        return True
    
    def send_verification_email(self, email: str, code: str) -> bool:
        """Send verification code via email"""
        try:
            smtp_host = os.getenv('SMTP_HOST')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_host, smtp_user, smtp_password]):
                print("SMTP not configured - skipping email")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email
            msg['Subject'] = 'Digital Lab - Verification Code'
            
            body = f"""
            <html>
            <body>
                <h2>Welcome to Digital Lab!</h2>
                <p>Your verification code is: <strong>{code}</strong></p>
                <p>This code will expire in 24 hours.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def create_admin_user(self, email: str, password: str):
        """Create admin user if doesn't exist"""
        existing = self.db.get_user_by_email(email)
        if existing:
            print(f"ℹ️  Admin user {email} already exists")
            return existing
        
        password_hash = self.hash_password(password)
        user_id = self.db.create_user(email, password_hash, "System Admin")
        self.db.verify_user(email)
        print(f"✅ Created admin user: {email}")
        return {'id': user_id, 'email': email}


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({"error": "No token provided"}), 401
        
        # Import here to avoid circular dependency
        from app import auth_manager
        
        # Verify token
        result = auth_manager.verify_token(token)
        
        if not result['valid']:
            return jsonify({"error": result.get('error', 'Invalid token')}), 401
        
        # Add user info to request
        request.current_user = result
        
        return f(*args, **kwargs)
    
    return decorated_function
