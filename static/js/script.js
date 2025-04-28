document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userMessage = document.getElementById('userMessage');
    const sendBtn = document.getElementById('sendBtn');
    const micBtn = document.getElementById('micBtn');

    // Generate a random session ID for this browser session
    const sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
    
    // Function to add a message to the chat UI
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user' : 'message bot';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Process message text (convert URLs to links, etc.)
        const processedText = message.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        contentDiv.innerHTML = processedText;
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = 'Typing...';
        
        loadingDiv.appendChild(contentDiv);
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return loadingDiv;
    }
    
    // Function to remove loading indicator
    function hideLoading(loadingDiv) {
        if (loadingDiv && loadingDiv.parentNode) {
            loadingDiv.parentNode.removeChild(loadingDiv);
        }
    }
    
    // Function to send message to server
    function sendMessage(message) {
        if (!message.trim()) return;
        
        // Add user message to UI
        addMessage(message, true);
        
        // Show loading indicator
        const loadingIndicator = showLoading();
        
        // Disable input while processing
        userMessage.disabled = true;
        sendBtn.disabled = true;
        
        // Send to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            hideLoading(loadingIndicator);
            
            // Add bot response to UI
            if (data.response) {
                addMessage(data.response);
            } else if (data.error) {
                addMessage('Error: ' + data.error);
            }
        })
        .catch(error => {
            // Remove loading indicator
            hideLoading(loadingIndicator);
            
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.');
        })
        .finally(() => {
            // Re-enable input
            userMessage.disabled = false;
            sendBtn.disabled = false;
            userMessage.value = '';
            userMessage.focus();
        });
    }
    
    // Function to reset conversation
    function resetConversation() {
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Clear UI
                chatMessages.innerHTML = '';
                
                // Add welcome message
                addMessage('Welcome to Pune University Support Chatbot! How can I help you today?');
            }
        })
        .catch(error => {
            console.error('Error resetting conversation:', error);
        });
    }
    
    // Event listeners
    sendBtn.addEventListener('click', function() {
        sendMessage(userMessage.value);
    });
    
    userMessage.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendMessage(userMessage.value);
        }
    });
    
    // Speech recognition for microphone button (if supported)
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'en-IN';
        recognition.continuous = false;
        
        micBtn.addEventListener('click', function() {
            recognition.start();
            micBtn.classList.add('listening');
        });
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userMessage.value = transcript;
            micBtn.classList.remove('listening');
            sendMessage(transcript);
        };
        
        recognition.onerror = function() {
            micBtn.classList.remove('listening');
        };
        
        recognition.onend = function() {
            micBtn.classList.remove('listening');
        };
    } else {
        micBtn.style.display = 'none';
    }
});