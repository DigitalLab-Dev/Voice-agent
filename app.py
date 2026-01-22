"""
Flask Web Application for Digital Lab AI Calling Agent
Main server with WebSocket support for real-time communication
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from datetime import datetime
import time
from database import ConversationDatabase
from ai_services import ai_services
from auth import auth_manager, require_auth
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'digital-lab-ai-agent-secret-key'
CORS(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
db = ConversationDatabase()

# Current call state
current_call = {
    'active': False,
    'conversation_id': None,
    'start_time': None,
    'messages': []
}



@app.route('/')
def landing():
    """Serve landing page"""
    return render_template('landing.html')

@app.route('/login')
def login_page():
    """Serve login page"""
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    """Serve signup page"""
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    """Serve dashboard (requires auth in frontend)"""
    return render_template('dashboard.html')

@app.route('/agent')
def agent():
    """Serve agent interface (requires auth in frontend)"""
    return render_template('index.html')


# === AUTH API ENDPOINTS ===

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Register new user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    result = auth_manager.create_user(email, password, full_name)
    
    if result['success']:
        # Auto-login: generate token
        token = auth_manager.create_token(result['user_id'], result['email'])
        
        # Structure response like login
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': result['user_id'],
                'email': result['email'],
                'full_name': result['full_name']
            }
        }), 201
    else:
        return jsonify(result), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    result = auth_manager.authenticate_user(email, password)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user profile"""
    user_id = request.current_user['user_id']
    user = auth_manager.get_user(user_id)
    
    if user:
        return jsonify({'user': user}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/agent_builder')
def agent_builder():
    """Serve agent builder interface"""
    return render_template('agent_builder.html')

@app.route('/api/agent/create', methods=['POST'])
@require_auth
def create_agent():
    """Create new agent"""
    data = request.json
    user_id = request.current_user['user_id']
    
    # Generate system prompt (same logic as before)
    business_name = data.get('business_name')
    industry = data.get('industry')
    services = data.get('services')
    tone = data.get('tone')
    goal = data.get('call_goal', 'Book a consultation')
    agent_name = data.get('agent_name', 'Alex')
    
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
    
    # ALWAYS create new agent
    agent_id = auth_manager.create_agent(user_id, agent_data)
    
    if agent_id:
        return jsonify({'success': True, 'agent_id': agent_id}), 201
    else:
        return jsonify({'success': False, 'error': 'Failed to create agent'}), 500

@app.route('/api/agents', methods=['GET'])
@require_auth
def get_user_agents():
    """Get all agents for current user"""
    user_id = request.current_user['user_id']
    agents = auth_manager.get_user_agents(user_id)
    return jsonify({'agents': agents})

@app.route('/api/start_call', methods=['POST'])
def start_call():
    """Start a new call"""
    global current_call
    
    print("DEBUG: /api/start_call hit")
    
    # Auto-reset if active
    if current_call['active']:
        print("DEBUG: Forcing reset of existing call")
        end_call()
    
    if current_call['active']:
        return jsonify({"error": "Call already in progress"}), 400
    
    # Check headers for auth token
    auth_header = request.headers.get('Authorization')
    user_agent = None
    
    if auth_header:
        token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        user_data = auth_manager.verify_token(token)
        if user_data['success']:
            # Get specific agent if ID provided, else get latest
            data = request.json or {}
            agent_id = data.get('agent_id')
            
            if agent_id:
                agent = auth_manager.get_agent(agent_id)
                # Verify ownership
                if agent and agent['user_id'] == user_data['user_id']:
                    user_agent = agent
            else:
                # Fallback to latest agent
                agents = auth_manager.get_user_agents(user_data['user_id'])
                if agents:
                    user_agent = agents[0]
    
    # Create new conversation in database with AGENT ID
    agent_id_val = user_agent['id'] if user_agent else None
    conversation_id = db.create_conversation(agent_id=agent_id_val)
    
    # Reset AI conversation context with SPECIFIC SYSTEM PROMPT
    if user_agent:
        ai_services.reset_conversation(system_prompt=user_agent['system_prompt'])
        greeting = user_agent['greeting_message']
    else:
        # Fallback to default
        ai_services.reset_conversation()
        greeting = f"Hello! This is Alex speaking from Digital Lab. How can I assist you today?"
    
    # Initialize call state
    current_call = {
        'active': True,
        'conversation_id': conversation_id,
        'start_time': time.time(),
        'messages': []
    }
    
    # Add to database
    db.add_message(conversation_id, 'agent', greeting)
    
    # Add to current messages
    current_call['messages'].append({
        'role': 'agent',
        'content': greeting,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
    
    return jsonify({
        "success": True,
        "conversation_id": conversation_id,
        "message": greeting
    })


@app.route('/api/send_message', methods=['POST'])
def send_message():
    """Process user message and get AI response"""
    global current_call
    
    if not current_call['active']:
        return jsonify({"error": "No active call"}), 400
    
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # Add user message to database
    db.add_message(current_call['conversation_id'], 'user', user_message)
    
    # Add to current messages
    current_call['messages'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
    
    # Get AI response
    ai_response = ai_services.get_ai_response(user_message)
    
    # Check for auto-termination signal
    should_end_call = False
    if "[END_CALL]" in ai_response:
        should_end_call = True
        ai_response = ai_response.replace("[END_CALL]", "").strip()
    
    # Add agent response to database
    db.add_message(current_call['conversation_id'], 'agent', ai_response)
    
    # Add to current messages
    current_call['messages'].append({
        'role': 'agent',
        'content': ai_response,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
    
    return jsonify({
        "success": True,
        "response": ai_response,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "should_end_call": should_end_call
    })


@app.route('/api/end_call', methods=['POST'])
def end_call():
    """End the current call"""
    global current_call
    
    if not current_call['active']:
        return jsonify({"error": "No active call"}), 400
    
    # Calculate duration
    duration = int(time.time() - current_call['start_time'])
    
    # Update conversation in database
    db.update_conversation(current_call['conversation_id'], duration=duration)
    
    conversation_id = current_call['conversation_id']
    
    # Reset call state
    current_call = {
        'active': False,
        'conversation_id': None,
        'start_time': None,
        'messages': []
    }
    
    return jsonify({
        "success": True,
        "conversation_id": conversation_id,
        "duration": duration
    })


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
    """Delete a conversation"""
    success = db.delete_conversation(conversation_id)
    
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
    if request.current_user['email'] != 'admin@digitallab.com':
        return jsonify({"error": "Unauthorized"}), 403
        
    stats = db.get_system_stats()
    return jsonify({"stats": stats})

@app.route('/api/admin/users', methods=['GET'])
@require_auth
def get_admin_users():
    """Get all users for admin"""
    if request.current_user['email'] != 'admin@digitallab.com':
        return jsonify({"error": "Unauthorized"}), 403
        
    users = db.get_all_users()
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


# WebSocket events for real-time communication
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to Digital Lab AI Agent'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('user_speaking')
def handle_user_speaking(data):
    """Handle real-time user speaking status"""
    emit('agent_status', {'status': 'listening'}, broadcast=True)


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 Digital Lab AI Calling Agent")
    print("="*60)
    print(f"\n📱 Starting server...")
    print(f"🌐 Open your browser to: http://localhost:5001")
    print(f"\n💡 Press Ctrl+C to stop the server\n")
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
