# Digital Lab AI Calling Agent - Project Structure

## 📁 Core Application Files

```
/Volumes/University Material/Ai Project copy/
│
├── 🚀 Main Application
│   ├── app.py                    # Flask backend server
│   ├── ai_services.py            # Google Gemini AI integration
│   ├── database.py               # SQLite conversation storage
│   └── demo_script.py            # Pre-scripted demo responses
│
├── 🎨 Frontend
│   ├── templates/
│   │   └── index.html            # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css         # Dark theme styling
│       └── js/
│           └── main.js           # JS logic & Web Speech API
│
├── 💾 Data
│   └── conversations.db          # SQLite database (conversation history)
│
├── 📦 Configuration
│   └── requirements.txt          # Python dependencies
│
└── 📖 Documentation
    ├── PRESENTATION_GUIDE.md     # Class demo instructions
    ├── QUICKSTART.md             # Setup guide
    └── PROJECT_REQUIREMENTS.md   # Requirements documentation
```

## ✨ What Each File Does

### **Application Core**
- **app.py**: Flask server with REST API endpoints and WebSocket support
- **ai_services.py**: Handles Gemini AI responses and demo mode
- **database.py**: Manages conversation history storage and retrieval
- **demo_script.py**: Contains 40+ pre-written responses for presentations

### **Frontend**
- **index.html**: User interface with call controls and chat window
- **style.css**: Dark theme design with Digital Lab branding
- **main.js**: Voice recognition, TTS, and real-time messaging

### **Data**
- **conversations.db**: Stores all conversation history, messages, and summaries

### **Documentation**
- **PRESENTATION_GUIDE.md**: Step-by-step demo guide for class presentation
- **QUICKSTART.md**: Installation and usage instructions
- **PROJECT_REQUIREMENTS.md**: Feature requirements and specifications

## 🗑️ Cleaned Up (Removed)

The following unused files have been removed:
- ❌ `test_conversation.py` - Test script
- ❌ `test_demo_mode.py` - Test script
- ❌ `check_models.py` - Model verification script
- ❌ `aifc.py` - Unrelated audio codec file
- ❌ `audioop.py` - Unrelated audio operations
- ❌ `agent_debug.log` - Debug logs
- ❌ `call_logs/` - Old logs directory
- ❌ `digital_lab_agent/` - Old implementation (not used)
- ❌ `__pycache__/` - Python cache files

## 🚀 How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py

# Open browser
http://localhost:5001
```

## 📊 File Statistics

**Total Essential Files**: 13
- Python files: 4
- HTML/CSS/JS: 3
- Database: 1
- Documentation: 3
- Config: 1
- Virtual env: 1 directory

**Total Size**: ~100KB (excluding database and venv)

## 🎯 All Systems Ready!

Your project is now clean and contains ONLY the files necessary for:
✅ Running the AI agent
✅ Web interface
✅ Conversation history
✅ Demo mode for presentation
✅ Documentation
