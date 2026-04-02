// Audio Recorder
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
    }

    async start() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.start();
        } catch (error) {
            console.error('Error accessing microphone:', error);
        }
    }

    stop() {
        return new Promise((resolve) => {
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                resolve(audioBlob);
            };
            this.mediaRecorder.stop();
        });
    }
}
