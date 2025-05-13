// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Mobile sidebar toggle
    if (window.innerWidth <= 480) {
        const chatHeader = document.querySelector('.chat-header');
        const mobileSidebarToggle = document.createElement('i');
        mobileSidebarToggle.className = 'fas fa-arrow-left mobile-toggle';
        
        chatHeader.querySelector('.chat-info').prepend(mobileSidebarToggle);
        
        mobileSidebarToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.add('active');
        });
        
        // Close sidebar when clicking on a chat item
        document.querySelectorAll('.chat-item').forEach(item => {
            item.addEventListener('click', function() {
                document.querySelector('.sidebar').classList.remove('active');
            });
        });
    }
    
    // Activate chat when clicking on a chat item
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all chat items
            document.querySelectorAll('.chat-item').forEach(chat => {
                chat.classList.remove('active');
            });
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Update chat title in the header
            const chatName = this.querySelector('.chat-title').textContent;
            document.querySelector('.chat-name').textContent = chatName;
        });
    });
    
    // Send on Enter key press
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('send-button').click();
        }
    });
    
    // Dialect selector
    const dialectSelect = document.getElementById('dialect-select');
    if (dialectSelect) {
        dialectSelect.addEventListener('change', function() {
            const selectedDialect = this.value;
            
            // Call API to change dialect
            fetch('/api/dialect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dialect: selectedDialect }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Add a system message about the dialect change
                    const chatMessages = document.querySelector('.chat-messages');
                    const systemMessage = document.createElement('div');
                    systemMessage.className = 'message message-in';
                    systemMessage.innerHTML = `
                        <div class="message-text">${data.message}</div>
                        <div class="message-time">${getCurrentTime()}</div>
                    `;
                    chatMessages.appendChild(systemMessage);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            })
            .catch(error => {
                console.error('Error changing dialect:', error);
            });
        });
    }
    
    // Load available dialects
    fetch('/api/dialects')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const dialectSelect = document.getElementById('dialect-select');
                // Clear any existing options
                dialectSelect.innerHTML = '';
                
                // Add options for each available dialect
                data.dialects.forEach(dialect => {
                    const option = document.createElement('option');
                    option.value = dialect;
                    option.textContent = dialect.charAt(0).toUpperCase() + dialect.slice(1);
                    dialectSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading dialects:', error);
        });
});

// Helper function to get current time in HH:MM format
function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}
