document.getElementById('send-button').addEventListener('click', sendMessage);

function sendMessage() {
    const userMessage = document.getElementById('user-input').value;
    if (userMessage.trim() === '') return;

    displayMessage('You', userMessage);
    document.getElementById('user-input').value = '';

    // Show typing indicator
    document.getElementById('typing-indicator').style.display = 'block';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        displayMessage('Bot', data.response);
        document.getElementById('typing-indicator').style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage('Bot', 'Sorry, something went wrong.');
        document.getElementById('typing-indicator').style.display = 'none';
    });
}

function displayMessage(sender, message) {
    const chatHistory = document.getElementById('chat-history');
    const messageElement = document.createElement('p');
    messageElement.textContent = `${sender}: ${message}`;
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}
