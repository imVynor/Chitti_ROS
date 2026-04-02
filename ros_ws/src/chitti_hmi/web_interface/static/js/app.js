// Main Application
let sessionId = null;
let socket = null;
let recorder = null;
let isRecording = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize socket connection
    socket = io();
    
    // Get session ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get('session_id') || 'unknown';
    
    document.getElementById('sessionId').textContent = `Session: ${sessionId.substring(0, 8)}...`;
    
    // Setup button event listeners
    const recordButton = document.getElementById('recordButton');
    recordButton.addEventListener('mousedown', startRecording);
    recordButton.addEventListener('mouseup', stopRecording);
    recordButton.addEventListener('touchstart', startRecording);
    recordButton.addEventListener('touchend', stopRecording);
    
    // Setup socket listeners
    socket.on('connect', function() {
        console.log('Connected to server');
        updateStatus('Ready to speak');
    });
    
    socket.on('transcription_result', function(data) {
        console.log('Received transcription:', data);
        document.getElementById('transcription').innerHTML = 
            `<p>${data.text}</p>`;
        updateStatus('Tap and hold to speak');
    });
    
    socket.on('robot_response', function(data) {
        console.log('Received response:', data);
        document.getElementById('response').innerHTML = 
            `<p>${data.response}</p>`;
    });
});

function startRecording() {
    if (!isRecording) {
        recorder = new AudioRecorder();
        recorder.start();
        isRecording = true;
        
        const button = document.getElementById('recordButton');
        button.classList.add('recording');
        updateStatus('🔴 Recording... Release to stop');
    }
}

function stopRecording() {
    if (isRecording) {
        recorder.stop().then(audioBlob => {
            isRecording = false;
            
            const button = document.getElementById('recordButton');
            button.classList.remove('recording');
            updateStatus('⏳ Processing...');
            
            // Send audio to server
            const formData = new FormData();
            formData.append('audio', audioBlob, 'audio.webm');
            formData.append('session_id', sessionId);
            
            fetch('/api/voice', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error:', error);
                updateStatus('Error sending audio');
            });
        });
    }
}

function updateStatus(message) {
    document.getElementById('status').textContent = message;
}
