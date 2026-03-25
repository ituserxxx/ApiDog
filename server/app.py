from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['DEBUG'] = os.getenv('DEBUG', 'True') == 'True'
app.config['PORT'] = int(os.getenv('PORT', 5000))

@app.route('/')
def index():
    return jsonify({
        'message': 'ApiGog Flask API Server',
        'status': 'running'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'ApiGog API'
    })

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        port=app.config['PORT'],
        host='0.0.0.0'
    )
