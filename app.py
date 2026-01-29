"""
Flask Web Application for Digital Lab AI Calling Agent
Main server with improved security, rate limiting, and proper logging
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = ['GROQ_API_KEY', 'JWT_SECRET']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

from database import ConversationDatabase
from ai_services import ai_services
from auth import AuthManager, require_auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET')
app.config['SESSION_TYPE'] = 'filesystem'
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize database (will use PostgreSQL on Railway via DATABASE_URL)
db = ConversationDatabase()

# Initialize auth manager with database instance
auth_manager = AuthManager(db)

# Initialize admin user (runs on every startup, including Gunicorn)
logger.info("Initializing admin user...")
auth_manager.create_admin_user("syedaliturab@gmail.com", "Admin@123")

logger.info("Application initialized successfully")


# ========== PAGE ROUTES ==========

@app.route('/')
def landing():
    """Serve landing page"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serve login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Serve signup page"""
    return render_template('signup_new.html')

@app.route('/dashboard')
def dashboard():
    """Serve dashboard (requires auth in frontend)"""
    return render_template('dashboard.html')

@app.route('/agent')
def agent():
    """Serve agent interface (requires auth in frontend)"""
    return render_template('agent.html')

@app.route('/agent_builder')
def agent_builder():
    """Serve agent builder interface"""
    return render_template('agent_builder.html')


# ========== AUTH API ENDPOINTS ==========

def standardized_error(message, code=400):
    """Return standardized error response"""
    return jsonify({'success': False, 'error': message}), code

def standardized_success(data, code=200):
    """Return standardized success response"""
    response = {'success': True}
    response.update(data)
    return jsonify(response), code

# ========== PRE-SIGNUP EMAIL VERIFICATION ENDPOINTS ==========

@app.route('/api/auth/send-verification-code', methods=['POST'])
@limiter.limit("10 per hour")
def send_verification_code():
    """Send verification code to email before signup"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return standardized_error('Email required', 400)
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return standardized_error('Invalid email format', 400)
        
        result = auth_manager.send_pre_signup_verification(email)
        
        if result['success']:
            logger.info(f"Verification code sent to: {email}")
            return standardized_success({
                'message': 'Verification code sent! Please check your email.'
            })
        else:
            return standardized_error(result.get('error', 'Failed to send code'), 400)
            
    except Exception as e:
        logger.error(f"Send verification code error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/verify-code', methods=['POST'])
@limiter.limit("20 per hour")
def verify_code():
    """Verify email code before signup"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return standardized_error('Email and code required', 400)
        
        result = auth_manager.verify_pre_signup_code(email, code)
        
        if result['success']:
            logger.info(f"Email verified: {email}")
            return standardized_success({'message': 'Email verified successfully!'})
        else:
            return standardized_error(result.get('error', 'Verification failed'), 400)
            
    except Exception as e:
        logger.error(f"Verify code error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/resend-code', methods=['POST'])
@limiter.limit("5 per hour")
def resend_code():
    """Resend verification code"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return standardized_error('Email required', 400)
        
        result = auth_manager.resend_pre_signup_code(email)
        
        if result['success']:
            logger.info(f"Verification code resent to: {email}")
            return standardized_success({'message': 'Code resent successfully!'})
        else:
            return standardized_error(result.get('error', 'Failed to resend code'), 400)
            
    except Exception as e:
        logger.error(f"Resend code error: {str(e)}")
        return standardized_error('Internal server error', 500)


@app.route('/api/auth/signup', methods=['POST'])
@limiter.limit("10 per hour")  # Doubled from 5
def signup():
    """Register new user with email verification"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        full_name = data.get('full_name', '').strip()
        
        # Input validation
        if not email or not password:
            return standardized_error('Email and password required', 400)
        
        if len(password) < 8:
            return standardized_error('Password must be at least 8 characters', 400)
        
        if len(email) > 255 or len(full_name) > 255:
            return standardized_error('Input too long', 400)
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return standardized_error('Invalid email format', 400)
        
        result = auth_manager.create_user(email, password, full_name)
        
        if result['success']:
            # Send verification email
            verification_result = auth_manager.send_verification_email(result['user_id'], email)
            
            if verification_result['success']:
                logger.info(f"New user registered: {email} (pending verification)")
                return standardized_success({
                    'message': 'Account created! Please check your email for a verification code.',
                    'user_id': result['user_id'],
                    'requires_verification': True
                }, 201)
            else:
                logger.warning(f"User created but email failed: {email}")
                return standardized_success({
                    'message': 'Account created but email verification failed. Please contact support.',
                    'user_id': result['user_id'],
                    'requires_verification': False
                }, 201)
        else:
            return standardized_error(result.get('error', 'Registration failed'), 400)
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per hour")  # Doubled from 10
def login():
    """Authenticate user"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return standardized_error('Email and password required', 400)
        
        result = auth_manager.authenticate_user(email, password)
        
        if result['success']:
            logger.info(f"User logged in: {email}")
            return standardized_success(result)
        else:
            logger.warning(f"Failed login attempt: {email}")
            return standardized_error(result.get('error', 'Authentication failed'), 401)
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/verify-email', methods=['POST'])
@limiter.limit("20 per hour")  # Doubled from 10
def verify_email():
    """Verify email with code"""
    try:
        data = request.json
        user_id = data.get('user_id')
        code = data.get('code', '').strip()
        
        if not user_id or not code:
            return standardized_error('User ID and code required', 400)
        
        result = auth_manager.verify_email_code(user_id, code)
        
        if result['success']:
            # Auto-login after verification
            user = auth_manager.get_user(user_id)
            if user:
                token = auth_manager.create_token(user_id, user['email'])
                logger.info(f"Email verified: {user['email']}")
                return standardized_success({
                    'message': 'Email verified successfully!',
                    'token': token,
                    'user': user
                })
        
        return standardized_error(result.get('error', 'Verification failed'), 400)
        
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/resend-verification', methods=['POST'])
@limiter.limit("6 per hour")  # Doubled from 3
def resend_verification():
    """Resend verification email"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return standardized_error('Email required', 400)
        
        # Get user by email (assuming you add this method)
        result = auth_manager.resend_verification_email(email)
        
        if result['success']:
            return standardized_success({'message': 'Verification email sent!'})
        else:
            return standardized_error(result.get('error', 'Failed to send email'), 400)
            
    except Exception as e:
        logger.error(f"Resend verification error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/request-password-reset', methods=['POST'])
@limiter.limit("6 per hour")  # Doubled from 3
def request_password_reset():
    """Request password reset"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return standardized_error('Email required', 400)
        
        result = auth_manager.send_password_reset_email(email)
        
        # Always return success for security (don't reveal if email exists)
        logger.info(f"Password reset requested for: {email}")
        return standardized_success({'message': 'If email exists, reset code has been sent'})
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("10 per hour")  # Doubled from 5
def reset_password():
    """Reset password with code"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not email or not code or not new_password:
            return standardized_error('Email, code, and new password required', 400)
        
        if len(new_password) < 8:
            return standardized_error('Password must be at least 8 characters', 400)
        
        result = auth_manager.reset_password_with_code(email, code, new_password)
        
        if result['success']:
            logger.info(f"Password reset successful: {email}")
            return standardized_success({'message': 'Password reset successfully!'})
        else:
            return standardized_error(result.get('error', 'Reset failed'), 400)
            
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user profile"""
    try:
        user_id = request.current_user['user_id']
        user = auth_manager.get_user(user_id)
        
        if user:
            return standardized_success({'user': user})
        else:
            return standardized_error('User not found', 404)
            
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return standardized_error('Internal server error', 500)


# ========== AGENT MANAGEMENT ==========


@app.route('/api/agent/create', methods=['POST'])
@require_auth
@limiter.limit("20 per hour")  # Doubled from 10
def create_agent():
    """Create new agent with input validation"""
    try:
        data = request.json
        user_id = request.current_user['user_id']
        
        # Input validation
        business_name = data.get('business_name', '').strip()
        industry = data.get('industry', '').strip()
        services = data.get('services', '').strip()
        tone = data.get('tone', '').strip()
        goal = data.get('call_goal', 'Book a consultation').strip()
        agent_name = data.get('agent_name', 'Alex').strip()
        
        if not business_name or not industry or not services:
            return standardized_error('Business name, industry, and services are required', 400)
        
        if len(business_name) > 255 or len(agent_name) > 100:
            return standardized_error('Input too long', 400)
        
        # Generate system prompt
        system_prompt = f"""You are {agent_name}, a friendly AI representative for {business_name}, a company in the {industry} industry.

Your Goal: {goal}

Services Offered:
{services}

Tone: {tone}
- Keep responses short (1-2 sentences).
- Ask one clear follow-up question at a time.
- Be helpful and professional.
- If asked about pricing, give a general range but steer towards booking a consultation for a quote.

CRITICAL INSTRUCTIONS:
1. Always stay in character as {agent_name}.
2. Do not make up facts about the company that aren't listed above.
3. If unsure, offer to have a human team member call them back.
4. Focus on benefits, not just features.
"""

        greeting_message = f"Hello! This is {agent_name} calling from {business_name}. How are you doing today?"

        agent_data = {
            'business_name': business_name,
            'industry': industry,
            'services': services,
            'tone': tone,
            'system_prompt': system_prompt,
            'greeting_message': greeting_message
        }
        
        agent_id = auth_manager.create_agent(user_id, agent_data)
        
        if agent_id:
            logger.info(f"Agent created: {business_name} by user {user_id}")
            return standardized_success({'agent_id': agent_id}, 201)
        else:
            return standardized_error('Failed to create agent', 500)
            
    except Exception as e:
        logger.error(f"Create agent error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/agents', methods=['GET'])
@require_auth
def get_user_agents():
    """Get all agents for current user"""
    try:
        user_id = request.current_user['user_id']
        agents = auth_manager.get_user_agents(user_id)
        return standardized_success({'agents': agents})
    except Exception as e:
        logger.error(f"Get agents error: {str(e)}")
        return standardized_error('Internal server error', 500)

@app.route('/api/agent/<int:agent_id>', methods=['DELETE'])
@require_auth
def delete_agent(agent_id):
    """Delete agent (with ownership check)"""
    try:
        user_id = request.current_user['user_id']
        
        # Verify ownership
        agent = auth_manager.get_agent(agent_id)
        if not agent:
            return standardized_error('Agent not found', 404)
        
        if agent['user_id'] != user_id:
            logger.warning(f"Unauthorized agent deletion attempt: user {user_id}, agent {agent_id}")
            return standardized_error('Unauthorized', 403)
        
        result = auth_manager.delete_agent(agent_id)
        
        if result['success']:
            logger.info(f"Agent deleted: {agent_id} by user {user_id}")
            return standardized_success({'message': 'Agent deleted successfully'})
        else:
            return standardized_error('Failed to delete agent', 500)
            
    except Exception as e:
        logger.error(f"Delete agent error: {str(e)}")
        return standardized_error('Internal server error', 500)


# ========== CALL MANAGEMENT (Fixed Multi-User Support) ==========


@app.route('/api/start_call', methods=['POST'])
@limiter.limit("40 per hour")  # Doubled from 20
def start_call():
    """
    Start a new call (Fixed for multi-user support)
    NO MORE GLOBAL STATE - uses database to track calls
    """
    try:
        logger.info("Start call request received")
        
        # Get auth token if present
        auth_header = request.headers.get('Authorization')
        user_agent = None
        user_id = None
        
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            user_data = auth_manager.verify_token(token)
            if user_data['success']:
                user_id = user_data['user_id']
                data = request.json or {}
                agent_id = data.get('agent_id')
                
                if agent_id:
                    agent = auth_manager.get_agent(agent_id)
                    # Verify ownership
                    if agent and agent['user_id'] == user_id:
                        user_agent = agent
                else:
                    # Fallback to latest agent
                    agents = auth_manager.get_user_agents(user_id)
                    if agents:
                        user_agent = agents[0]
        
        # Create conversation in database
        agent_id_val = user_agent['id'] if user_agent else None
        conversation_id = db.create_conversation(agent_id=agent_id_val)
        
        # Determine system prompt and greeting
        if user_agent:
            system_prompt = user_agent['system_prompt']
            greeting = user_agent['greeting_message']
        else:
            system_prompt = None  # Will use default in ai_services
            greeting = f"Hello! This is Alex speaking from Digital Lab. How can I assist you today?"
        
        # Store conversation metadata (start_time AND system_prompt)
        metadata = {
            'start_time': time.time(),
            'system_prompt': system_prompt  # CRITICAL: Store custom prompt per conversation
        }
        db.update_conversation_metadata(conversation_id, metadata)
        
        # Reset AI conversation context with specific prompt
        # NOTE: This is still needed for the greeting, but subsequent messages will use DB
        if user_agent:
            ai_services.reset_conversation(system_prompt=system_prompt)
        else:
            ai_services.reset_conversation()
        
        # Add greeting to database
        db.add_message(conversation_id, 'agent', greeting)
        
        logger.info(f"Call started successfully: conversation_id={conversation_id}, user={user_id}")
        
        return standardized_success({
            'conversation_id': conversation_id,
            'message': greeting
        })
        
    except Exception as e:
        logger.error(f"Start call error: {str(e)}")
        return standardized_error('Failed to start call', 500)



@app.route('/api/send_message', methods=['POST'])
@limiter.limit("120 per minute")  # Doubled from 60
def send_message():
    """
    Process user message and get AI response (Fixed for multi-user)
    Uses conversation_id to identify call, no global state
    """
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        user_message = data.get('message', '').strip()
        
        if not conversation_id:
            return standardized_error('Conversation ID required', 400)
        
        if not user_message:
            return standardized_error(' Message cannot be empty', 400)
        
        # Verify conversation exists
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            return standardized_error('Conversation not found', 404)
        
        # CRITICAL FIX: Retrieve conversation-specific system prompt from database
        metadata = db.get_conversation_metadata(conversation_id)
        system_prompt = metadata.get('system_prompt')  # May be None for default
        
        # Reset AI context with THIS conversation's system prompt
        # This ensures each conversation uses its own custom agent config
        if system_prompt:
            ai_services.reset_conversation(system_prompt=system_prompt)
        else:
            ai_services.reset_conversation()  # Use default prompt
        
        # Restore conversation history from database to maintain context
        conversation_data = db.get_conversation(conversation_id)
        ai_services.conversation_history = []
        if conversation_data and 'messages' in conversation_data:
            for msg in conversation_data['messages']:
                ai_services.conversation_history.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # Add user message to database
        db.add_message(conversation_id, 'user', user_message)
        
        # Get AI response
        ai_response = ai_services.get_ai_response(user_message)
        
        # Check for auto-termination signal
        should_end_call = False
        if "[END_CALL]" in ai_response:
            should_end_call = True
            ai_response = ai_response.replace("[END_CALL]", "").strip()
        
        # Add agent response to database
        db.add_message(conversation_id, 'agent', ai_response)
        
        logger.info(f"Message processed for conversation {conversation_id}")
        
        return standardized_success({
            'response': ai_response,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'should_end_call': should_end_call
        })
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        return standardized_error('Failed to process message', 500)


@app.route('/api/end_call', methods=['POST'])
def end_call():
    """
    End the current call (Fixed for multi-user)
    Uses conversation_id, no global state
    """
    try:
        data = request.json or {}
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return standardized_error('Conversation ID required', 400)
        
        # Get conversation to retrieve start time
        metadata = db.get_conversation_metadata(conversation_id)
        start_time = metadata.get('start_time') if metadata else time.time()
        
        # Calculate duration
        duration = int(time.time() - start_time)
        
        # Update conversation in database
        db.update_conversation(conversation_id, duration=duration)
        
        logger.info(f"Call ended: conversation_id={conversation_id}, duration={duration}s")
        
        return standardized_success({
            'conversation_id': conversation_id,
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"End call error: {str(e)}")
        return standardized_error('Failed to end call', 500)


@app.route('/api/voice_settings', methods=['POST'])
def update_voice_settings():
    """Update voice settings"""
    data = request.json
    
    gender = data.get('gender')
    pitch = data.get('pitch')
    speed = data.get('speed')
    
    ai_services.set_voice_settings(gender=gender, pitch=pitch, speed=speed)
    
    return jsonify({"success": True})


@app.route('/api/generate_summary', methods=['POST'])
def generate_summary():
    """Generate summary for a conversation"""
    data = request.json
    conv_id = data.get('conversation_id')
    
    if not conv_id:
        return jsonify({"error": "Missing conversation ID"}), 400
        
    conversation = db.get_conversation(conv_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
        
    # Generate summary using AI
    result = ai_services.generate_summary(conversation['messages'])
    
    if result:
        # Save to database
        db.update_conversation(
            conv_id, 
            summary=result['summary'],
            sentiment=result['sentiment']
        )
        return jsonify({"success": True, **result})
    
    return jsonify({"error": "Failed to generate summary"}), 500


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get conversation history"""
    agent_id = request.args.get('agent_id')
    user_id = None
    
    if agent_id:
        try:
            agent_id = int(agent_id)
        except ValueError:
            agent_id = None
            
    # If no specific agent requested, restrict to current user's agents
    if not agent_id:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            user_data = auth_manager.verify_token(token)
            if user_data['success']:
                user_id = user_data['user_id']
            
    conversations = db.get_all_conversations(agent_id=agent_id, user_id=user_id)
    return jsonify({"conversations": conversations})


@app.route('/api/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation details"""
    conversation = db.get_conversation(conversation_id)
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    return jsonify({"conversation": conversation})


@app.route('/api/conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation (with ownership check)"""
    try:
        # Get auth header
        auth_header = request.headers.get('Authorization')
        user_id = None
        
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            user_data = auth_manager.verify_token(token)
            if user_data['success']:
                user_id = user_data['user_id']
        
        if not user_id:
            return standardized_error('Unauthorized', 401)
        
        # Get conversation to verify ownership
        conversation = db.get_conversation(conversation_id)
        if not conversation:
            return standardized_error('Conversation not found', 404)
        
        # Verify user owns the agent that created this conversation
        if conversation.get('agent_id'):
            agent = auth_manager.get_agent(conversation['agent_id'])
            if agent and agent['user_id'] != user_id:
                logger.warning(f"Unauthorized conversation deletion attempt: user {user_id}, conv {conversation_id}")
                return standardized_error('Unauthorized - you do not own this conversation', 403)
        
        # Delete conversation
        success = db.delete_conversation(conversation_id)
        
        if success:
            logger.info(f"Conversation deleted: {conversation_id} by user {user_id}")
            return standardized_success({'message': 'Conversation deleted'})
        else:
            return standardized_error('Failed to delete conversation', 500)
            
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        return standardized_error('Internal server error', 500)

    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to delete conversation"}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get call statistics"""
    agent_id = request.args.get('agent_id')
    user_id = None
    
    if agent_id:
        try:
            agent_id = int(agent_id)
        except ValueError:
            agent_id = None
            
    # If no specific agent requested, restrict to current user's agents
    if not agent_id:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
            user_data = auth_manager.verify_token(token)
            if user_data['success']:
                user_id = user_data['user_id']
    
    stats = db.get_statistics(agent_id=agent_id, user_id=user_id)
    return jsonify({"statistics": stats})


# ========== Admin Routes ==========
@app.route('/admin')
def admin_dashboard():
    """Serve admin dashboard"""
    # Simple protection: Check parameter or rely on frontend to redirect if not admin
    # Real protection should be done via middleware/session
    return render_template('admin.html')

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
def get_admin_stats():
    """Get system stats for admin"""
    # Check if admin (hardcoded for now)
    if request.current_user['email'] != 'syedaliturab@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
        
    # Get conversation stats from database
    db_stats = db.get_system_stats()
    
    # Get user and agent counts from database
    total_users = db.count_users()
    total_agents = db.count_agents()
    
    # Get leads count (conversations with positive sentiment)
    from database import Conversation
    session = db.Session()
    try:
        total_leads = session.query(Conversation).filter(
            Conversation.sentiment.like('%Positive%')
        ).count()
    finally:
        session.close()
    
    # Map to frontend-expected field names
    stats = {
        'total_users': total_users,
        'total_agents': total_agents,
        'total_calls': db_stats.get('total_conversations', 0),  # Rename for frontend
        'total_leads': total_leads
    }
    
    return jsonify({"stats": stats})

@app.route('/api/admin/users', methods=['GET'])
@require_auth
def get_admin_users():
    """Get all users for admin"""
    if request.current_user['email'] != 'syedaliturab@gmail.com':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get all users with agent counts from database
    users = db.get_all_users_with_agents()
    return jsonify({"users": users})

@app.route('/api/export/<int:conversation_id>', methods=['GET'])
def export_conversation(conversation_id):
    """Export conversation as text file"""
    conversation = db.get_conversation(conversation_id)
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    # Create text content
    content = f"Digital Lab - Conversation Export\n"
    content += f"Date: {conversation['timestamp']}\n"
    content += f"Duration: {conversation.get('duration', 'N/A')} seconds\n"
    content += f"="*60 + "\n\n"
    
    for message in conversation['messages']:
        role = "Agent" if message['role'] == 'agent' else "Customer"
        content += f"[{message['timestamp']}] {role}: {message['content']}\n\n"
    
    if conversation.get('summary'):
        content += f"\n{'='*60}\nSUMMARY:\n{conversation['summary']}\n"
    
    # Save to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f"conversation_{conversation_id}.txt",
        mimetype='text/plain'
    )


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv('PORT', 5001))
    
    # Check if we're in production
    is_production = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER')
    
    if not is_production:
        print("\n" + "="*60)
        print("🚀 Digital Lab AI Calling Agent")
        print("="*60)
        print(f"\n📱 Starting server...")
        print(f"🌐 Open your browser to: http://localhost:{port}")
        print(f"\n👤 Admin login: syedaliturab@gmail.com / Admin@123")
        print(f"\n💡 Press Ctrl+C to stop the server\n")
    
    # Run the app
    # In production, debug should be False
    app.run(debug=not is_production, host='0.0.0.0', port=port)
