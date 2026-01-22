// Digital Lab AI Calling Agent - Frontend JavaScript

// Global state
let currentCallId = null;
let isCallActive = false;
let callStartTime = null;
let durationInterval = null;
let socket = null;

// Voice recognition
let recognition = null;
let synthesis = window.speechSynthesis;
let currentVoice = null;

// Voice settings
let voiceSettings = {
    gender: 'male',
    pitch: 0,
    speed: 1.0
};

// ========== Initialize on Page Load ==========
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();

    // Check for auto-start parameters
    const urlParams = new URLSearchParams(window.location.search);
    const autostart = urlParams.get('autostart');
    const agentId = urlParams.get('agent_id');

    if (agentId) {
        // Store agent ID for this session
        sessionStorage.setItem('current_agent_id', agentId);
    }

    if (autostart === 'true') {
        // Auto-click start button if parameters exist
        setTimeout(() => {
            const startBtn = document.getElementById('startCallBtn');
            if (startBtn) {
                startBtn.click();
            }
        }, 800);
    }
    setupEventListeners();
    loadConversationHistory();
    loadStatistics();
    initializeVoiceControls();
});

// ========== Initialization ==========
function initializeApp() {
    // Initialize Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false; // We'll restart manually for better control
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            console.log("Heard:", transcript);

            // Only send if it's not empty and call is active
            if (transcript.trim() && isCallActive) {
                document.getElementById('messageInput').value = transcript;
                sendMessage();
            }
        };

        recognition.onend = function () {
            // Auto-restart if call is active and agent is NOT speaking
            if (isCallActive && !synthesis.speaking) {
                try {
                    recognition.start();
                    console.log("Listening restarted...");
                } catch (e) {
                    console.log("Could not restart immediately");
                }
            }
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error);
            if (event.error !== 'no-speech' && event.error !== 'aborted') {
                // showNotification('Voice input error. Retrying...', 'warning');
            }
        };
    }

    // Load available voices for TTS
    if (synthesis) {
        synthesis.onvoiceschanged = loadVoices;
        loadVoices();
    }
}

function loadVoices() {
    const voices = synthesis.getVoices();

    // Select appropriate voice based on gender setting
    updateVoiceFromSettings();
}

function updateVoiceFromSettings() {
    const voices = synthesis.getVoices();
    const gender = voiceSettings.gender;

    // Try to find a voice matching the gender preference
    currentVoice = voices.find(voice =>
        voice.name.toLowerCase().includes(gender) ||
        (gender === 'male' && !voice.name.toLowerCase().includes('female')) ||
        (gender === 'female' && voice.name.toLowerCase().includes('female'))
    ) || voices[0];
}

// ========== Event Listeners ==========
function setupEventListeners() {
    // Call controls
    document.getElementById('startCallBtn').addEventListener('click', startCall);
    document.getElementById('endCallBtn').addEventListener('click', endCall);

    // Message input
    document.getElementById('sendMessageBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Voice input button
    document.getElementById('voiceInputBtn').addEventListener('click', startVoiceInput);

    // Voice settings
    document.querySelectorAll('input[name="gender"]').forEach(input => {
        input.addEventListener('change', function () {
            voiceSettings.gender = this.value;
            updateVoiceFromSettings();
            updateBackendVoiceSettings();
        });
    });

    document.getElementById('pitchSlider').addEventListener('input', function () {
        voiceSettings.pitch = parseInt(this.value);
        document.getElementById('pitchValue').textContent = this.value;
        updateBackendVoiceSettings();
    });

    document.getElementById('speedSlider').addEventListener('input', function () {
        voiceSettings.speed = parseInt(this.value) / 100;
        document.getElementById('speedValue').textContent = voiceSettings.speed.toFixed(1) + 'x';
        updateBackendVoiceSettings();
    });

    document.getElementById('testVoice').addEventListener('click', testVoice);

    // Summary panel
    document.getElementById('generateSummaryBtn').addEventListener('click', generateSummary);
    document.getElementById('exportBtn').addEventListener('click', exportConversation);
    document.getElementById('closeSummaryBtn').addEventListener('click', closeSummaryPanel);
}

// ========== Call Management ==========
async function startCall() {
    if (isCallActive) return;

    try {
        showLoading(true);
        updateStatus('Connecting...');

        // Check for auth token
        const token = localStorage.getItem('auth_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Check for specific agent ID in session
        const agentId = sessionStorage.getItem('current_agent_id');
        const body = {};
        if (agentId) {
            body.agent_id = parseInt(agentId);
        }

        const response = await fetch('/api/start_call', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (data.success) {
            console.log("Call started successfully. CID:", data.conversation_id);
            currentCallId = data.conversation_id;
            isCallActive = true;
            callStartTime = Date.now();

            // Update UI
            document.getElementById('startCallBtn').style.display = 'none';
            document.getElementById('endCallBtn').style.display = 'inline-flex';
            document.getElementById('callDuration').style.display = 'flex';
            document.getElementById('messageInputArea').style.display = 'flex';
            document.getElementById('callStatus').textContent = 'Active';
            document.getElementById('callStatus').classList.add('active');

            // Clear welcome message and show conversation
            document.getElementById('conversationWindow').innerHTML = '';

            // Add greeting message
            addMessage('agent', data.message);

            // Speak greeting
            console.log("Speaking greeting:", data.message);
            speakText(data.message);

            // Start duration timer
            startDurationTimer();

        } else {
            console.error("Start call failed:", data);
            alert("Failed to start call: " + (data.error || "Unknown error"));
        }

        showLoading(false);

    } catch (error) {
        console.error('Error starting call:', error);
        alert("System Error: " + error.message);
        showLoading(false);
    }
}

async function endCall() {
    try {
        showLoading(true);

        const response = await fetch('/api/end_call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            isCallActive = false;

            // Update UI
            document.getElementById('startCallBtn').style.display = 'inline-flex';
            document.getElementById('endCallBtn').style.display = 'none';
            document.getElementById('callDuration').style.display = 'none';
            document.getElementById('messageInputArea').style.display = 'none';
            document.getElementById('callStatus').textContent = 'Ready';
            document.getElementById('callStatus').classList.remove('active');

            // Stop duration timer
            clearInterval(durationInterval);

            // Show summary panel explicitly
            const summaryPanel = document.getElementById('summaryPanel');
            if (summaryPanel) {
                summaryPanel.style.display = 'block';
                // Reset placeholder
                document.getElementById('summaryContent').innerHTML = `
                    <p class="summary-placeholder">Conversation ended. Click "Generate Summary" to visualize key insights.</p>
                `;
            }

            // Reload history and stats
            loadConversationHistory();
            loadStatistics();
        }

        showLoading(false);

    } catch (error) {
        console.error('Error ending call:', error);
        showNotification('Failed to end call', 'error');
        showLoading(false);
    }
}

function startDurationTimer() {
    durationInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('durationText').textContent =
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

// ========== Message Handling ==========
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message || !isCallActive) return;

    // Clear input
    input.value = '';

    // Add user message to UI
    addMessage('user', message);

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (data.success) {
            // Add agent response
            addMessage('agent', data.response);

            // Speak response
            speakText(data.response);

            // Check if call should auto-terminate
            if (data.should_end_call) {
                console.log('Auto-ending call after goodbye...');
                // Wait for agent to finish speaking, then end call
                setTimeout(() => {
                    endCall();
                }, 3000); // 3 second delay for speech to complete
            }
        }

    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        showNotification('Failed to send message', 'error');
    }
}

function addMessage(role, content) {
    const conversationWindow = document.getElementById('conversationWindow');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-content">${escapeHtml(content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;

    conversationWindow.appendChild(messageDiv);
    conversationWindow.scrollTop = conversationWindow.scrollHeight;
}

function showTypingIndicator() {
    const conversationWindow = document.getElementById('conversationWindow');

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message agent';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    conversationWindow.appendChild(typingDiv);
    conversationWindow.scrollTop = conversationWindow.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// ========== Text-to-Speech ==========
function speakText(text) {
    if (!synthesis) return;

    // Stop recognition while agent speaks to avoid echo
    if (recognition) {
        try {
            recognition.stop();
        } catch (e) { }
    }

    // Cancel any ongoing speech
    synthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    // Apply voice settings
    if (currentVoice) {
        utterance.voice = currentVoice;
    }

    // Pitch: -20 to 20 → 0 to 2
    utterance.pitch = 1 + (voiceSettings.pitch / 20);
    utterance.pitch = Math.max(0, Math.min(2, utterance.pitch));

    // Speed
    utterance.rate = voiceSettings.speed;

    // Resume listening after speech ends
    utterance.onend = function () {
        if (isCallActive && recognition) {
            try {
                recognition.start();
                console.log("Agent finished speaking, listening resumed...");
            } catch (e) {
                console.log("Could not restart listening immediately");
            }
        }
    };

    synthesis.speak(utterance);
}

function testVoice() {
    speakText("Hello, this is Alex from Digital Lab. How can I assist you today?");
}

// ========== Voice Input ==========
function startVoiceInput() {
    if (!recognition) {
        showNotification('Voice input not supported in this browser', 'warning');
        return;
    }

    if (!isCallActive) {
        showNotification('Please start a call first', 'warning');
        return;
    }

    try {
        recognition.start();
        document.getElementById('voiceInputBtn').style.background = 'var(--danger)';

        setTimeout(() => {
            document.getElementById('voiceInputBtn').style.background = '';
        }, 3000);

    } catch (error) {
        console.error('Voice input error:', error);
    }
}

// ========== Summary Generation ==========
async function generateSummary() {
    if (!currentCallId) return;

    try {
        showLoading(true);

        const response = await fetch('/api/generate_summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conversation_id: currentCallId })
        });

        const data = await response.json();

        if (data.success) {
            const summaryContent = document.getElementById('summaryContent');
            summaryContent.innerHTML = `
                <div class="summary-text">
                    ${data.summary.replace(/\n/g, '<br>')}
                </div>
                <div class="summary-sentiment">
                    <strong>Sentiment:</strong> <span style="color: ${getSentimentColor(data.sentiment)}">${data.sentiment.toUpperCase()}</span>
                </div>
            `;
        }

        showLoading(false);

    } catch (error) {
        console.error('Error generating summary:', error);
        showNotification('Failed to generate summary', 'error');
        showLoading(false);
    }
}

function getSentimentColor(sentiment) {
    switch (sentiment.toLowerCase()) {
        case 'positive': return 'var(--success)';
        case 'negative': return 'var(--danger)';
        default: return 'var(--warning)';
    }
}

function closeSummaryPanel() {
    document.getElementById('summaryPanel').style.display = 'none';
    document.getElementById('summaryContent').innerHTML = '<p class="summary-placeholder">Click "Generate Summary" to create an AI-powered summary of this conversation</p>';
    currentCallId = null;
}

// ========== Conversation History ==========
async function loadConversationHistory() {
    try {
        // Get current agent ID if available
        const agentId = sessionStorage.getItem('current_agent_id');
        let url = '/api/conversations';
        if (agentId) {
            url += `?agent_id=${agentId}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        const historyList = document.getElementById('historyList');

        if (data.conversations.length === 0) {
            historyList.innerHTML = '<p class="no-history">No previous calls</p>';
            return;
        }

        historyList.innerHTML = '';

        data.conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'history-item';

            const date = new Date(conv.timestamp);
            const timeStr = date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            item.innerHTML = `
                <div class="history-item-header">
                    <div class="history-item-time">${timeStr}</div>
                    <div class="history-item-duration">${conv.duration || '0'}s</div>
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted);">
                    ${conv.message_count || 0} messages
                </div>
                <button class="history-item-delete" onclick="deleteConversation(${conv.id}, event)">Delete</button>
            `;

            item.onclick = function (e) {
                if (!e.target.classList.contains('history-item-delete')) {
                    loadConversation(conv.id);
                }
            };

            historyList.appendChild(item);
        });

    } catch (error) {
        console.error('Error loading history:', error);
    }
}

async function loadConversation(id) {
    try {
        const response = await fetch(`/api/conversation/${id}`);
        const data = await response.json();

        if (data.conversation) {
            const conversationWindow = document.getElementById('conversationWindow');
            conversationWindow.innerHTML = '';

            if (data.conversation.messages) {
                // Parse messages if stored as JSON string, otherwise use as is
                let messages = data.conversation.messages;
                if (typeof messages === 'string') {
                    try {
                        messages = JSON.parse(messages);
                    } catch (e) {
                        messages = [];
                    }
                }

                messages.forEach(msg => {
                    addMessage(msg.role, msg.content);
                });
            }

            // Show summary panel if summary exists
            if (data.conversation.summary) {
                const summaryPanel = document.getElementById('summaryPanel');
                const summaryContent = document.getElementById('summaryContent');

                summaryPanel.style.display = 'block';
                summaryContent.innerHTML = `
                    <div class="summary-text">
                        ${data.conversation.summary.replace(/\n/g, '<br>')}
                    </div>
                    <div class="summary-sentiment">
                        <strong>Sentiment:</strong> <span style="color: ${getSentimentColor(data.conversation.sentiment)}">${data.conversation.sentiment.toUpperCase()}</span>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

async function deleteConversation(id, event) {
    if (event) {
        event.stopPropagation();
    }

    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }

    try {
        const response = await fetch(`/api/conversation/${id}`, {
            method: 'DELETE'
        });
        const data = await response.json();

        if (data.success) {
            loadConversationHistory();
            loadStatistics();

            // If viewing this conversation, clear it
            if (currentCallId === id) {
                document.getElementById('conversationWindow').innerHTML = `
                    <div class="welcome-message">
                        <h2>👋 Ready to help?</h2>
                        <p>Start a conversation to begin assisting customers.</p>
                    </div>
                `;
                closeSummaryPanel();
            }
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
    }
}

// ========== Statistics ==========
async function loadStatistics() {
    try {
        // Get current agent ID if available
        const agentId = sessionStorage.getItem('current_agent_id');
        let url = '/api/statistics';
        if (agentId) {
            url += `?agent_id=${agentId}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.statistics) {
            document.getElementById('totalCalls').textContent = data.statistics.total_calls;
            document.getElementById('avgDuration').textContent = data.statistics.average_duration + 's';
        }

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// ========== Export ==========
async function exportConversation() {
    if (!currentCallId) return;

    window.location.href = `/api/export/${currentCallId}`;
}

// ========== Backend Voice Settings Update ==========
async function updateBackendVoiceSettings() {
    try {
        await fetch('/api/voice_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(voiceSettings)
        });
    } catch (error) {
        console.error('Error updating voice settings:', error);
    }
}

// ========== Utility Functions ==========
function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function updateStatus(status) {
    const statusEl = document.getElementById('callStatus');
    if (statusEl) {
        statusEl.textContent = status;
    }
}

function showNotification(message, type = 'info') {
    // Simple alert for critical errors, console for others
    console.log(`[${type.toUpperCase()}] ${message}`);
    if (type === 'error') {
        alert(message);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
