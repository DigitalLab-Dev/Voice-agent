# 🚀 Digital Lab AI Calling Agent - Quick Start Guide

## Installation & Setup

### Step 1: Install Dependencies

```bash
cd "/Volumes/University Material/Ai Project copy"
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python app.py
```

### Step 3: Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

## How to Use

### 1. Start a Call
- Click the **"Start Call"** button
- The agent will greet you: "Hello! This is Alex from Digital Lab..."

### 2. Interact with the Agent
- **Type a message** in the input field and click Send
- OR **Click the microphone icon** 🎙️ to speak
- OR press Enter to send your message

### 3. Customize Voice Settings
- **Gender**: Choose Male or Female voice
- **Pitch**: Adjust from -20 to +20
- **Speed**: Adjust from 0.5x to 2.0x
- Click **"Test Voice"** to hear a sample

### 4. End the Call
- Click **"End Call"** when done
- The summary panel will appear

### 5. Generate Summary
- Click **"Generate Summary"** button
- AI will analyze the conversation and create a summary
- Shows key topics, customer interests, and sentiment

### 6. View Call History
- See all past conversations in the left sidebar
- Click any conversation to view it again
- Click **"Delete"** to remove a conversation

### 7. Export Conversation
- After generating a summary, click **"Export"**
- Downloads conversation as a text file

## Features

✅ **Natural AI Conversations** - Powered by Google Gemini (free tier)
✅ **Voice Input & Output** - Browser-based speech recognition and synthesis
✅ **Dark Theme** - Beautiful interface with Digital Lab branding
✅ **Conversation History** - All calls saved with timestamps
✅ **AI Summaries** - Automatic conversation summarization
✅ **Voice Customization** - Gender, pitch, and speed controls
✅ **Export** - Download conversations as text files
✅ **Statistics** - Track total calls and average duration

## Tips

- **Voice Input**: Works best in Chrome/Edge browsers
- **Clear Audio**: Speak clearly for better recognition
- **Internet Required**: Needed for AI and speech services
- **Multiple Browsers**: Open in multiple tabs for testing

## Troubleshooting

**Port already in use?**
```bash
# The app runs on port 5000 by default
# If occupied, edit app.py and change the port number
```

**Voice not working?**
- Allow microphone permissions in browser
- Make sure you're using Chrome, Edge, or Safari
- Check your microphone is not muted

**AI not responding?**
- Check internet connection
- Verify Gemini API key is valid in config.py

## Project Structure

```
Ai Project copy/
├── app.py                  # Main Flask server
├── database.py             # Conversation storage
├── ai_services.py          # AI integration
├── requirements.txt        # Dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   ├── css/
│   │   └── style.css      # Dark theme styling
│   └── js/
│       └── main.js        # Frontend logic
└── digital_lab_agent/     # Original code (reference)
```

## For Your Semester  Project

### Demo Tips
1. Prepare 2-3 test scenarios (e.g., asking about SEO, web design)
2. Show voice customization features
3. Demonstrate conversation history and summaries
4. Export a conversation and show the file

### Screenshots to Take
- Main interface with dark theme
- Active call in progress
- Conversation with chat bubbles
- Voice control panel
- Summary generation
- Call history sidebar

### Video Recording
- Record a full call from start to finish
- Show all features in action
- Demonstrate voice input
- Generate and export summary

---

**Built with ❤️ for Digital Lab**

**Ready to impress your professor! 🌟**
