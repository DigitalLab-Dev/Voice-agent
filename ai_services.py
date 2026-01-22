"""
AI Services Integration for Digital Lab Agent
Handles Groq AI, TTS, and STT services
"""

from groq import Groq
import os
import io
import base64
from typing import Optional, List, Dict
import tempfile
from demo_script import get_demo_response

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast, high-quality model

# System prompt for Digital Lab agent
SYSTEM_PROMPT = """You are Alex, a friendly sales agent for Digital Lab (digitallabservices.com).

Services: Video Editing, Graphic Design, Social Media, Ads Management, SEO, Copywriting, Web Development.

CRITICAL RULES:
1. Keep responses SHORT: 1-2 sentences max, then ask ONE follow-up question
2. Be conversational and friendly, not corporate
3. Focus on BENEFITS and getting them excited
4. Goal: Book a consultation call
5. For pricing: "Packages start at $500-$2000, but let's discuss YOUR needs on a quick call"
6. Listen more than you talk - keep it customer-centric
7. Sound human, not robotic

Example good response: "SEO is perfect for you! We help businesses rank #1 on Google. What industry are you in?"
Example bad response: "Search engine optimization is a comprehensive service that involves multiple strategies including..."

Be brief, friendly, and conversion-focused."""


class AIServices:
    """Handles all AI service integrations"""
    
    def __init__(self):
        """Initialize AI services"""
        # Initialize Groq
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.conversation_history = []
        
        # Demo mode settings
        self.demo_mode = False  # Disable demo mode - use real AI
        self.use_demo_on_error = True  # Use demo script when API fails
        
        # Voice settings
        self.voice_gender = "male"  # male or female
        self.voice_pitch = 0.0  # -20.0 to 20.0
        self.voice_speed = 1.0  # 0.25 to 4.0
    
    def set_voice_settings(self, gender: str = None, pitch: float = None, speed: float = None):
        """Update voice settings"""
        if gender:
            self.voice_gender = gender.lower()
        if pitch is not None:
            self.voice_pitch = max(-20.0, min(20.0, pitch))
        if speed is not None:
            self.voice_speed = max(0.25, min(4.0, speed))
    
    def get_ai_response(self, user_message: str) -> str:
        """
        Get AI response from Groq using conversation context
        """
        try:
            # Use demo script if demo mode is enabled
            if self.demo_mode:
                print("🎭 Demo mode active - using scripted response")
                ai_response = get_demo_response(user_message)
            else:
                # Build messages for Groq API
                messages = [
                    {"role": "system", "content": self.current_system_prompt}
                ]
                
                # Add conversation history (last 10 messages)
                for msg in self.conversation_history[-10:]:
                    messages.append({
                        "role": "user" if msg['role'] == 'user' else "assistant",
                        "content": msg['content']
                    })
                
                # Add current user message
                messages.append({
                    "role": "user",
                    "content": user_message
                })
                
                # Generate response with retry logic
                max_retries = 3
                retry_delay = 1
                
                for attempt in range(max_retries):
                    try:
                        response = self.groq_client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            max_tokens=150,  # Reduced for shorter responses
                            temperature=0.9,
                        )
                        ai_response = response.choices[0].message.content.strip()
                        
                        # Check if user is saying goodbye
                        goodbye_phrases = ["bye", "goodbye", "talk later", "end call", "that's all", "that's enough"]
                        if any(phrase in user_message.lower() for phrase in goodbye_phrases):
                            # Mark conversation as ending
                            ai_response += "\n[END_CALL]"
                        
                        break
                    except Exception as e:
                        if "429" in str(e) and attempt < max_retries - 1:
                            print(f"Rate limit hit, retrying in {retry_delay}s...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            print(f"API Error: {e}")
                            # Use demo script as intelligent fallback
                            if self.use_demo_on_error:
                                print("📱 API failed - switching to demo script")
                                ai_response = get_demo_response(user_message)
                            else:
                                # Random fallback
                                import random
                                fallbacks = [
                                    "I'm listening, please go on.",
                                    "Could you say that again?",
                                    "I see. Tell me more.",
                                    "Interesting. Please continue.",
                                    "I'm here, just thinking for a moment."
                                ]
                                ai_response = random.choice(fallbacks)
                            break
            
            # Store in history
            self.conversation_history.append({
                'role': 'user',
                'content': user_message
            })
            self.conversation_history.append({
                'role': 'agent',
                'content': ai_response
            })
            
            return ai_response
            
        except Exception as e:
            print(f"Error getting AI response: {e}")
            # Use demo script if enabled
            if self.use_demo_on_error:
                print("📱 Outer exception - using demo script")
                fallback = get_demo_response(user_message)
            else:
                import random
                fallbacks = [
                    "I'm listening, please go on.",
                    "Could you say that again?",
                    "I see. Tell me more.",
                    "Interesting. Please continue.",
                    "I'm here, just thinking for a moment."
                ]
                fallback = random.choice(fallbacks)
            self.conversation_history.append({
                'role': 'user',
                'content': user_message
            })
            self.conversation_history.append({
                'role': 'agent',
                'content': fallback
            })
            return fallback
    
    def generate_summary(self, messages: List[Dict]) -> Dict:
        """
        Generate conversation summary using Groq
        """
        try:
            # Build conversation text
            conv_text = "Conversation:\n\n"
            for msg in messages:
                role = "Agent" if msg['role'] == 'agent' else "Customer"
                conv_text += f"{role}: {msg['content']}\n"
            
            summary_prompt = f"""{conv_text}

Based on the above conversation between a Digital Lab customer service agent and a customer, provide:
1. Key topics discussed (bullet points)
2. Customer's main interests or needs
3. Any action items or next steps mentioned
4. Overall sentiment (positive, neutral, or negative)

Format your response as:

**Key Topics:**
- [topic 1]
- [topic 2]

**Customer Interests:**
[brief description]

**Action Items:**
[any next steps or recommendations]

**Sentiment:** [positive/neutral/negative]"""
            
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional conversation analyst."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Extract sentiment
            sentiment = "neutral"
            if "positive" in summary_text.lower():
                sentiment = "positive"
            elif "negative" in summary_text.lower():
                sentiment = "negative"
            
            return {
                "summary": summary_text,
                "sentiment": sentiment
            }
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                "summary": "Error generating summary. Please try again.",
                "sentiment": "neutral"
            }
    
    def text_to_speech_google(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using Google Cloud TTS
        Falls back to simple audio if Google Cloud not configured
        """
        try:
            # Note: For true Google TTS, need to set up Google Cloud credentials
            # For now, returning None to use browser's built-in speech synthesis
            return None
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
    
    def reset_conversation(self, system_prompt: str = None):
        """Reset conversation history and settings"""
        self.conversation_history = []
        self.current_system_prompt = system_prompt if system_prompt else SYSTEM_PROMPT
    
    def get_conversation_context(self) -> List[Dict]:
        """Get current conversation history"""
        return self.conversation_history.copy()


# Create global instance
ai_services = AIServices()
