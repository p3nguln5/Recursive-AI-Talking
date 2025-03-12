document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO
    const socket = io();
    
    // DOM Elements
    const conversationForm = document.getElementById('conversation-form');
    const ai1Select = document.getElementById('ai1-select');
    const ai2Select = document.getElementById('ai2-select');
    const ai1Description = document.getElementById('ai1-description');
    const ai2Description = document.getElementById('ai2-description');
    const promptInput = document.getElementById('prompt-input');
    const turnsInput = document.getElementById('turns-input');
    const startBtn = document.getElementById('start-btn');
    const saveBtn = document.getElementById('save-btn');
    const conversationContainer = document.getElementById('conversation-container');
    const statusContainer = document.getElementById('status-container');
    const promptTokens = document.getElementById('prompt-tokens');
    const responseTokens = document.getElementById('response-tokens');
    const totalTokens = document.getElementById('total-tokens');
    
    // Global variables
    let personalities = {};
    let currentConversation = null;
    
    // Fetch personalities data
    fetch('/api/personalities')
        .then(response => response.json())
        .then(data => {
            personalities = data;
            updatePersonalityDescriptions();
        })
        .catch(error => {
            console.error('Error fetching personalities:', error);
            updateStatus('Error loading personalities. Please refresh the page.', 'danger');
        });
    
    // Event Listeners
    ai1Select.addEventListener('change', updatePersonalityDescriptions);
    ai2Select.addEventListener('change', updatePersonalityDescriptions);
    
    conversationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        startConversation();
    });
    
    saveBtn.addEventListener('click', function() {
        // The conversation is already saved on the server
        updateStatus('Conversation saved successfully!', 'success');
    });
    
    // Functions
    function updatePersonalityDescriptions() {
        if (Object.keys(personalities).length === 0) return;
        
        const ai1Key = ai1Select.value;
        const ai2Key = ai2Select.value;
        
        if (ai1Key) {
            const ai1 = personalities[ai1Key];
            ai1Description.textContent = ai1.system_instruction.substring(0, 100) + '...';
        } else {
            ai1Description.textContent = '';
        }
        
        if (ai2Key) {
            const ai2 = personalities[ai2Key];
            ai2Description.textContent = ai2.system_instruction.substring(0, 100) + '...';
        } else {
            ai2Description.textContent = '';
        }
        
        // Disable same selection in both dropdowns
        Array.from(ai2Select.options).forEach(option => {
            if (option.value === ai1Key && option.value !== '') {
                option.disabled = true;
            } else {
                option.disabled = false;
            }
        });
        
        Array.from(ai1Select.options).forEach(option => {
            if (option.value === ai2Key && option.value !== '') {
                option.disabled = true;
            } else {
                option.disabled = false;
            }
        });
    }
    
    function startConversation() {
        // Validate form
        if (!ai1Select.value || !ai2Select.value || !promptInput.value) {
            updateStatus('Please fill in all required fields.', 'danger');
            return;
        }
        
        // Clear previous conversation
        conversationContainer.innerHTML = '';
        
        // Update UI
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        updateStatus('Starting conversation...', 'info');
        
        // Reset token counters
        promptTokens.textContent = '0';
        responseTokens.textContent = '0';
        totalTokens.textContent = '0';
        
        // Prepare request data
        const requestData = {
            ai1: ai1Select.value,
            ai2: ai2Select.value,
            prompt: promptInput.value,
            turns: parseInt(turnsInput.value)
        };
        
        // Send request to server
        fetch('/api/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // Store current conversation
            currentConversation = data;
            
            // Display conversation
            displayConversation(data.conversation);
            
            // Update token usage
            updateTokenUsage(data.token_usage);
            
            // Update UI
            startBtn.disabled = false;
            startBtn.innerHTML = 'Start Conversation';
            saveBtn.disabled = false;
            updateStatus('Conversation completed!', 'success');
        })
        .catch(error => {
            console.error('Error starting conversation:', error);
            startBtn.disabled = false;
            startBtn.innerHTML = 'Start Conversation';
            updateStatus('Error generating conversation. Please try again.', 'danger');
        });
    }
    
    function displayConversation(conversation) {
        conversationContainer.innerHTML = '';
        
        conversation.forEach((message, index) => {
            const messageDiv = document.createElement('div');
            const isAi1 = index % 2 === 0;
            messageDiv.className = `message ${isAi1 ? 'message-ai1' : 'message-ai2'}`;
            
            const speaker = message.speaker;
            const color = getColorForSpeaker(speaker);
            
            messageDiv.innerHTML = `
                <div class="message-header color-${color}">${speaker}</div>
                <div class="message-content">${formatMessage(message.message)}</div>
                <div class="message-footer">
                    Tokens: ${message.token_usage.total_tokens}
                </div>
            `;
            
            conversationContainer.appendChild(messageDiv);
        });
        
        // Scroll to bottom
        conversationContainer.scrollTop = conversationContainer.scrollHeight;
    }
    
    function formatMessage(message) {
        // Convert line breaks to <br> tags
        return message.replace(/\n/g, '<br>');
    }
    
    function getColorForSpeaker(speaker) {
        for (const key in personalities) {
            if (personalities[key].name === speaker) {
                return personalities[key].color;
            }
        }
        return 'blue'; // Default color
    }
    
    function updateTokenUsage(tokenUsage) {
        promptTokens.textContent = tokenUsage.prompt_tokens;
        responseTokens.textContent = tokenUsage.response_tokens;
        totalTokens.textContent = tokenUsage.total_tokens;
    }
    
    function updateStatus(message, type = 'info') {
        const statusClass = type === 'danger' ? 'text-danger' : 
                           type === 'success' ? 'text-success' : 
                           type === 'warning' ? 'text-warning' : 'text-info';
        
        statusContainer.innerHTML = `<p class="${statusClass}">${message}</p>`;
    }
}); 