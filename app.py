from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import werkzeug

# Import our utility functions
from utils.parser import parse_resume
from utils.ats_scorer import analyze_resume
from utils.ai_detector import detect_ai_content
from utils.humanizer import humanize_text
from utils.optimizer import optimize_resume
from utils.citation import generate_citations
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder='frontend')
CORS(app) # Enable CORS for all routes

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('frontend', path)):
        return send_from_directory('frontend', path)
    return serve_frontend()

@app.route('/api/analyze-ats', methods=['POST'])
def api_analyze_ats():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
        
        resume_file = request.files['resume']
        job_desc = request.form.get('job_desc', '')
        
        if not resume_file.filename or not job_desc.strip():
            return jsonify({'error': 'Resume file and job description are required'}), 400
            
        parsed_data = parse_resume(resume_file)
        if not parsed_data or not parsed_data.get('text'):
            return jsonify({'error': 'Could not extract text from the file'}), 400
            
        results = analyze_resume(parsed_data, job_desc)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect-ai', methods=['POST'])
def api_detect_ai():
    try:
        data = request.json
        text = data.get('text', '')
        
        if len(text.split()) < 10:
            return jsonify({'error': 'Please enter at least 10 words'}), 400
            
        results = detect_ai_content(text)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context

@app.route('/api/humanize', methods=['POST'])
def api_humanize():
    try:
        data = request.json
        text = data.get('text', '')
        tone = data.get('tone', 'Professional')
        model = data.get('model', 'llama3')
        
        if not text.strip():
            return jsonify({'error': 'Text is required'}), 400
            
        generator = humanize_text(text, tone=tone, model=model)
        return Response(stream_with_context(generator), mimetype='text/plain')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
def api_optimize():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400
            
        resume_file = request.files['resume']
        job_desc = request.form.get('job_desc', '')
        model = request.form.get('model', 'llama3')
        
        parsed_data = parse_resume(resume_file)
        if not parsed_data or not parsed_data.get('text'):
            return jsonify({'error': 'Could not extract text from the file'}), 400
            
        results = analyze_resume(parsed_data, job_desc)
        missing_keywords = results.get('missing_keywords', [])
        
        generator = optimize_resume(parsed_data['text'], job_desc, missing_keywords, model=model)
        return Response(stream_with_context(generator), mimetype='text/plain')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cite', methods=['POST'])
def api_cite():
    try:
        data = request.json
        text = data.get('text', '')
        model = data.get('model', 'llama3')
        
        if not text.strip():
            return jsonify({'error': 'Text is required'}), 400
            
        generator = generate_citations(text, model=model)
        return Response(stream_with_context(generator), mimetype='text/plain')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
