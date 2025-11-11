"""
Flask Backend for CV Optimizer and Cover Letter Generator
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from utils.pdf_parser import extract_text_from_pdf
from utils.cv_optimizer import optimize_cv
from utils.letter_generator import generate_cover_letter
from utils.skills_matcher import extract_skills, match_skills
from utils.assistant import process_assistant_request
from utils.pdf_generator import generate_harvard_pdf
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for assistant conversation history
assistant_history = {}  # {session_id: [messages]}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {str(e)}", 500


@app.route('/api/optimize-cv', methods=['POST'])
def api_optimize_cv():
    """API endpoint to optimize CV"""
    try:
        data = request.json
        
        # Extract parameters
        cv_text = data.get('cv_text', '')
        job_description = data.get('job_description', '')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not cv_text or not job_description:
            return jsonify({'error': 'CV text and job description are required'}), 400
        
        # Get optimization parameters
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.3))
        min_experiences = int(data.get('min_experiences', 3))
        max_experiences = int(data.get('max_experiences', 8))
        max_date_years = data.get('max_date_years')
        if max_date_years:
            max_date_years = int(max_date_years)
        language = data.get('language', 'fr')
        
        # Optimize CV
        result = optimize_cv(
            cv_text=cv_text,
            job_description=job_description,
            api_key=api_key,
            model=model,
            temperature=temperature,
            min_experiences=min_experiences,
            max_experiences=max_experiences,
            max_date_years=max_date_years,
            language=language
        )
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/generate-letter', methods=['POST'])
def api_generate_letter():
    """API endpoint to generate cover letter"""
    try:
        data = request.json
        
        # Extract parameters
        cv_text = data.get('cv_text', '')
        optimized_cv = data.get('optimized_cv', '')
        job_description = data.get('job_description', '')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not cv_text or not job_description:
            return jsonify({'error': 'CV text and job description are required'}), 400
        
        # Get generation parameters
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.7))
        target_words = int(data.get('target_words', 300))
        language = data.get('language', 'fr')
        
        # Generate cover letter
        result = generate_cover_letter(
            cv_text=cv_text,
            optimized_cv=optimized_cv or cv_text,
            job_description=job_description,
            api_key=api_key,
            model=model,
            temperature=temperature,
            target_words=target_words,
            language=language
        )
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/parse-pdf', methods=['POST'])
def api_parse_pdf():
    """API endpoint to parse PDF files"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF and TXT allowed'}), 400
        
        # Read file content
        file_content = file.read()
        
        # Extract text
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        else:
            text = file_content.decode('utf-8')
        
        if not text.strip():
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        return jsonify({
            'text': text,
            'filename': file.filename,
            'word_count': len(text.split())
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-skills', methods=['POST'])
def api_extract_skills():
    """API endpoint to extract skills from CV or job description"""
    try:
        data = request.json
        
        text = data.get('text', '')
        text_type = data.get('text_type', 'cv')  # 'cv' or 'job'
        api_key = data.get('api_key', '')
        model = data.get('model', 'gpt-4o-mini')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        result = extract_skills(text, api_key, text_type, model)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/match-skills', methods=['POST'])
def api_match_skills():
    """API endpoint to match skills between CV and job description"""
    try:
        data = request.json
        
        cv_skills = data.get('cv_skills', [])
        job_skills = data.get('job_skills', [])
        cv_text = data.get('cv_text', '')
        job_text = data.get('job_text', '')
        api_key = data.get('api_key', '')
        model = data.get('model', 'gpt-4o-mini')
        
        if not cv_skills or not job_skills:
            return jsonify({'error': 'Both CV and job skills are required'}), 400
        
        result = match_skills(
            cv_skills=cv_skills,
            job_skills=job_skills,
            cv_text=cv_text,
            job_text=job_text,
            api_key=api_key,
            model=model
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/api/assistant', methods=['POST'])
def api_assistant():
    """API endpoint for conversational assistant to adjust CV and skills"""
    try:
        data = request.json
        
        user_request = data.get('request', '')
        session_id = data.get('session_id', 'default')
        api_key = data.get('api_key', '')
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.7))
        language = data.get('language', 'fr')
        
        # Context data
        original_cv = data.get('original_cv', '')
        optimized_cv = data.get('optimized_cv', '')
        job_description = data.get('job_description', '')
        cv_skills = data.get('cv_skills', [])
        job_skills = data.get('job_skills', [])
        matched_skills = data.get('matched_skills', {})
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not user_request:
            return jsonify({'error': 'Request is required'}), 400
        
        if not optimized_cv:
            return jsonify({'error': 'Please generate an optimized CV first'}), 400
        
        # Process assistant request
        result = process_assistant_request(
            user_request=user_request,
            original_cv=original_cv,
            optimized_cv=optimized_cv,
            job_description=job_description,
            cv_skills=cv_skills,
            job_skills=job_skills,
            matched_skills=matched_skills,
            api_key=api_key,
            model=model,
            temperature=temperature,
            language=language
        )
        
        if 'error' in result:
            error_response = {'error': result['error']}
            if 'error_code' in result:
                error_response['error_code'] = result['error_code']
            return jsonify(error_response), 500
        
        # Store in history
        if session_id not in assistant_history:
            assistant_history[session_id] = []
        
        message = {
            'id': f"{session_id}_{len(assistant_history[session_id])}",
            'request': user_request,
            'response': result,
            'timestamp': str(os.urandom(8).hex())
        }
        
        assistant_history[session_id].append(message)
        
        return jsonify(result)
    
    except Exception as e:
        error_msg = str(e)
        # Try to parse OpenAI errors
        try:
            from utils.cv_optimizer import parse_openai_error
            parsed = parse_openai_error(e)
            error_msg = parsed.get('user_message', error_msg)
        except:
            pass
        return jsonify({'error': error_msg, 'traceback': traceback.format_exc()}), 500


@app.route('/api/assistant-history', methods=['GET'])
def api_get_assistant_history():
    """API endpoint to get assistant conversation history"""
    try:
        session_id = request.args.get('session_id', 'default')
        
        if session_id not in assistant_history:
            return jsonify({'history': []})
        
        return jsonify({'history': assistant_history[session_id]})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assistant-history', methods=['DELETE'])
def api_clear_assistant_history():
    """API endpoint to clear assistant history"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in assistant_history:
            assistant_history[session_id] = []
        
        return jsonify({'success': True, 'message': 'Assistant history cleared'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-pdf', methods=['POST'])
def api_generate_pdf():
    """API endpoint to generate PDF CV with Harvard template"""
    try:
        data = request.json
        cv_text = data.get('cv_text', '')
        
        if not cv_text:
            return jsonify({'error': 'CV text is required'}), 400
        
        # Generate PDF
        pdf_buffer = generate_harvard_pdf(cv_text)
        
        # Return PDF file
        from flask import Response
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': 'attachment; filename=optimized_cv.pdf'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

