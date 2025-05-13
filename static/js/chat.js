// Chat functionality

let currentChatId = null;
let isTyping = false;

document.addEventListener('DOMContentLoaded', function() {
    // Load initial greeting message
    loadInitialGreeting();
    
    // Set up event listeners
    const sendButton = document.getElementById('send-button');
    const messageInput = document.getElementById('message-input');
    
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Make the first chat active by default
    const firstChat = document.querySelector('.chat-item');
    if (firstChat) {
        firstChat.classList.add('active');
    }
});

// Load the initial greeting message from the AI
function loadInitialGreeting() {
    fetch('/api/initial-message')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                addMessage(data.message, false);
            }
        })
        .catch(error => {
            console.error('Error loading initial greeting:', error);
            addMessage('أهلاً! أنا وكيل العقارات الذكي. كيف يمكنني مساعدتك؟', false);
        });
}

// Send a message to the server
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (message === '') return;
    
    // Add the user message to the chat
    addMessage(message, true);
    
    // Clear the input
    messageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send the message to the server
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            chat_id: currentChatId
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        hideTypingIndicator();
        
        if (data.status === 'success') {
            // Update the chat ID if this is a new conversation
            if (!currentChatId) {
                currentChatId = data.chat_id;
            }
            
            // Add the AI's response to the chat
            addMessage(data.message, false);
            
            // Update the last message in the active chat item
            updateLastMessage(data.message);
        } else {
            // Add an error message
            addMessage('عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.', false);
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('عذراً، حدث خطأ في الاتصال. يرجى التحقق من اتصالك بالإنترنت.', false);
    });
}

// Add a message to the chat
function addMessage(message, isUser) {
    const chatMessages = document.querySelector('.chat-messages');
    const messageElement = document.createElement('div');
    
    messageElement.className = isUser ? 'message message-out' : 'message message-in';
    
    const currentTime = getCurrentTime();
    
    messageElement.innerHTML = `
        <div class="message-text">${message}</div>
        <div class="message-time">${currentTime}</div>
    `;
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to the bottom of the chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show the typing indicator
function showTypingIndicator() {
    if (isTyping) return;
    
    isTyping = true;
    const chatMessages = document.querySelector('.chat-messages');
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.id = 'typing-indicator';
    
    typingIndicator.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Hide the typing indicator
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Update the last message in the active chat item
function updateLastMessage(message) {
    const activeChat = document.querySelector('.chat-item.active');
    if (activeChat) {
        const lastMessageElement = activeChat.querySelector('.chat-last-message');
        lastMessageElement.textContent = message;
        
        // Update time
        const timeElement = activeChat.querySelector('.chat-time');
        timeElement.textContent = getCurrentTime();
    }
}

// Helper function to get current time
function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}

// Load chat history if available
function loadChatHistory(chatId) {
    fetch(`/api/messages/${chatId}`)
        .then(response => response.json())
        .then(data => {
            // Clear existing messages
            const chatMessages = document.querySelector('.chat-messages');
            // Keep the date header
            const dateHeader = chatMessages.querySelector('.message-date');
            chatMessages.innerHTML = '';
            chatMessages.appendChild(dateHeader);
            
            // Add each message
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.is_user);
            });
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
        });
}

// Handle chat item clicks to load chat history
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function() {
            const chatId = this.getAttribute('data-chatid');
            currentChatId = chatId;
            
            // Update UI for selected chat
            document.querySelectorAll('.chat-item').forEach(chat => {
                chat.classList.remove('active');
            });
            this.classList.add('active');
            
            // Load messages for this chat
            loadChatHistory(chatId);
        });
    });
});
