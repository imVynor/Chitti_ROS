from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import sys

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
CORS(app)

# Store for routing
sessions = {}


@app.route('/')
def index():
    return render_template('voice_input.html')


@app.route('/voice/<session_id>')
def voice_interface(session_id):
    """Voice input interface for specific session"""
    return render_template('voice_input.html')


@app.route('/api/voice', methods=['POST'])
def process_voice():
    """Handle voice input"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'message': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'unknown')
        
        # Here audio would be processed by external service
        # For now, just acknowledge receipt
        return jsonify({
            'status': 'success',
            'message': 'Audio received',
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
