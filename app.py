"""
Flask Backend for CV Optimizer - Agent-based architecture
Uses LangGraph for CV optimization and ReAct for assistant
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import traceback
from utils.pdf_parser import extract_text_from_pdf
from utils.cv_optimizer_agent import optimize_cv_with_agent
from utils.letter_generator import generate_cover_letter, parse_openai_error
from utils.skills_matcher import extract_skills, match_skills
from utils.assistant_agent import process_assistant_request_with_agent
from utils.pdf_generator import generate_harvard_pdf
from utils.rag_system import RAGSystem

try:
    from langchain.memory import ConversationBufferMemory
except ImportError:
    try:
        from langchain_core.memory import ConversationBufferMemory
    except ImportError:
        # Try to import message types for proper fallback
        try:
            from langchain_core.messages import HumanMessage, AIMessage
        except ImportError:
            # If message types not available, create simple compatible classes
            class HumanMessage:
                def __init__(self, content):
                    self.content = content
                    self.type = "human"
            
            class AIMessage:
                def __init__(self, content):
                    self.content = content
                    self.type = "ai"
        
        # Simple fallback with proper message types
        class SimpleChatMemory:
            def __init__(self):
                self.messages = []
            
            def add_user_message(self, msg):
                self.messages.append(HumanMessage(msg))
            
            def add_ai_message(self, msg):
                self.messages.append(AIMessage(msg))
        
        class ConversationBufferMemory:
            def __init__(self, memory_key="chat_history", return_messages=True):
                self.memory_key = memory_key
                self.return_messages = return_messages
                self.chat_memory = SimpleChatMemory()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for assistant conversation history
assistant_memory = {}  # {session_id: ConversationBufferMemory}

# In-memory storage for RAG systems
rag_systems = {}  # {session_id: RAGSystem}


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
    """API endpoint to optimize CV using agent"""
    try:
        data = request.json
        
        cv_text = data.get('cv_text', '')
        job_description = data.get('job_description', '')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not cv_text or not job_description:
            return jsonify({'error': 'CV text and job description are required'}), 400
        
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.3))
        min_experiences = int(data.get('min_experiences', 3))
        max_experiences = int(data.get('max_experiences', 8))
        max_date_years = data.get('max_date_years')
        if max_date_years:
            max_date_years = int(max_date_years)
        language = data.get('language', 'fr')
        session_id = data.get('session_id', 'default')
        
        # Get or create RAG system for this session
        if session_id not in rag_systems:
            try:
                rag_systems[session_id] = RAGSystem(api_key=api_key)
            except Exception as e:
                return jsonify({
                    'error': f'Error initializing RAG system: {str(e)}',
                    'agent_logs': []
                }), 500
        
        rag_system = rag_systems[session_id]
        
        # Use agent-based optimization with RAG
        result = optimize_cv_with_agent(
            cv_text=cv_text,
            job_description=job_description,
            api_key=api_key,
            model=model,
            temperature=temperature,
            min_experiences=min_experiences,
            max_experiences=max_experiences,
            max_date_years=max_date_years,
            language=language,
            rag_system=rag_system  # Pass RAG system to agent
        )
        
        if result.get('error'):
            error_info = parse_openai_error(Exception(result['error']))
            return jsonify({
                'error': error_info['user_message'],
                'error_code': error_info.get('error_code'),
                'agent_logs': result.get('agent_logs', [])
            }), 500
        
        return jsonify({
            'optimized_cv': result.get('optimized_cv'),
            'agent_logs': result.get('agent_logs', []),
            'cv_skills': result.get('cv_skills', []),
            'job_skills': result.get('job_skills', []),
            'skills_comparison': result.get('skills_comparison'),
            'sources': result.get('sources'),  # NEW: Return RAG sources
            'rag_details': result.get('rag_details'),  # NEW: Return detailed RAG info for logs
            'graph_structure': result.get('graph_structure'),  # NEW: Return graph structure for visualization
            'model_used': result.get('model_used', model),
            'word_count': result.get('word_count', 0)
        })
        
    except Exception as e:
        error_info = parse_openai_error(e)
        return jsonify({
            'error': error_info['user_message'],
            'error_code': error_info.get('error_code'),
            'error_details': str(e)
        }), 500


@app.route('/api/generate-letter', methods=['POST'])
def api_generate_letter():
    """API endpoint to generate cover letter"""
    try:
        data = request.json
        
        cv_text = data.get('cv_text', '')
        optimized_cv = data.get('optimized_cv', '')
        job_description = data.get('job_description', '')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not cv_text or not job_description:
            return jsonify({'error': 'CV text and job description are required'}), 400
        
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.7))
        target_words = int(data.get('letter_words', 300))
        language = data.get('language', 'fr')
        
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
        
        if result.get('error'):
            return jsonify({
                'error': result['error'],
                'error_code': result.get('error_code')
            }), 500
        
        return jsonify({
            'cover_letter': result.get('cover_letter'),
            'word_count': result.get('word_count', 0),
            'target_words': result.get('target_words', target_words),
            'model_used': result.get('model_used', model)
        })
        
    except Exception as e:
        error_info = parse_openai_error(e)
        return jsonify({
            'error': error_info['user_message'],
            'error_code': error_info.get('error_code')
        }), 500


@app.route('/api/extract-skills', methods=['POST'])
def api_extract_skills():
    """API endpoint to extract skills from text"""
    try:
        data = request.json
        
        text = data.get('text', '')
        text_type = data.get('text_type', 'cv')
        api_key = data.get('api_key', '')
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.2))
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        result = extract_skills(
            text=text,
            text_type=text_type,
            api_key=api_key,
            model=model,
            temperature=temperature
        )
        
        if result.get('status') == 'error':
            return jsonify({
                'error': result.get('error', 'Error extracting skills'),
                'skills': []
            }), 500
        
        return jsonify({
            'skills': result.get('skills', []),
            'count': result.get('count', 0)
        })
        
    except Exception as e:
        error_info = parse_openai_error(e)
        return jsonify({
            'error': error_info['user_message'],
            'error_code': error_info.get('error_code'),
            'skills': []
        }), 500


@app.route('/api/match-skills', methods=['POST'])
def api_match_skills():
    """API endpoint to match CV skills with job skills"""
    try:
        data = request.json
        
        cv_skills = data.get('cv_skills', [])
        job_skills = data.get('job_skills', [])
        api_key = data.get('api_key', '')
        cv_text = data.get('cv_text', '')
        job_text = data.get('job_text', '')
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.3))
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not cv_skills or not job_skills:
            return jsonify({'error': 'Both CV skills and job skills are required'}), 400
        
        result = match_skills(
            cv_skills=cv_skills,
            job_skills=job_skills,
            api_key=api_key,
            cv_text=cv_text,
            job_text=job_text,
            model=model,
            temperature=temperature
        )
        
        if result.get('status') == 'error':
            return jsonify({
                'error': result.get('error', 'Error matching skills'),
                'matched': [],
                'cv_only': [],
                'job_only': [],
                'interesting': []
            }), 500
        
        return jsonify({
            'matched': result.get('matched', []),
            'cv_only': result.get('cv_only', []),
            'job_only': result.get('job_only', []),
            'interesting': result.get('interesting', []),
            'stats': result.get('stats', {})
        })
        
    except Exception as e:
        error_info = parse_openai_error(e)
        return jsonify({
            'error': error_info['user_message'],
            'error_code': error_info.get('error_code')
        }), 500


@app.route('/api/assistant', methods=['POST'])
def api_assistant():
    """API endpoint for conversational assistant"""
    try:
        data = request.json
        
        user_request = data.get('request', '')
        original_cv = data.get('original_cv', '')
        optimized_cv = data.get('optimized_cv', '')
        job_description = data.get('job_description', '')
        cv_skills = data.get('cv_skills', [])
        job_skills = data.get('job_skills', [])
        matched_skills = data.get('matched_skills', {})
        api_key = data.get('api_key', '')
        session_id = data.get('session_id', 'default')
        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.7))
        language = data.get('language', 'fr')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        if not user_request:
            return jsonify({'error': 'User request is required'}), 400
        
        if not optimized_cv:
            return jsonify({'error': 'Optimized CV is required'}), 400
        
        # Get or create memory for this session
        if session_id not in assistant_memory:
            assistant_memory[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        memory = assistant_memory[session_id]
        
        # Get or create RAG system for this session
        if session_id not in rag_systems:
            try:
                rag_systems[session_id] = RAGSystem(api_key=api_key)
            except Exception as e:
                print(f"Warning: Could not initialize RAG system for session {session_id}: {str(e)}")
                rag_systems[session_id] = None
        
        rag_system = rag_systems.get(session_id)
        
        # Use agent-based assistant with RAG
        result = process_assistant_request_with_agent(
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
            language=language,
            memory=memory,
            rag_system=rag_system  # NEW: Pass RAG system
        )
        
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result['error'],
                'updated_cv': optimized_cv,
                'explanation': None
            }), 500
        
        return jsonify({
            'success': True,
            'action': result.get('action'),
            'updated_cv': result.get('updated_cv', optimized_cv),
            'explanation': result.get('explanation'),
            'sources': result.get('sources', []),  # NEW: Return RAG sources
            'agent_logs': result.get('agent_logs', [])
        })
        
    except Exception as e:
        error_info = parse_openai_error(e)
        return jsonify({
            'success': False,
            'error': error_info['user_message'],
            'error_code': error_info.get('error_code'),
            'updated_cv': data.get('optimized_cv', ''),
            'explanation': None
        }), 500


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint to handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Only PDF and TXT files are supported.'}), 400
        
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB'}), 400
        
        # Read file content
        file_content = file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        else:
            text = file_content.decode('utf-8', errors='ignore')
        
        if not text.strip():
            return jsonify({'error': 'Could not extract text from file'}), 400
        
        word_count = len(text.split())
        
        return jsonify({
            'text': text,
            'filename': file.filename,
            'size': len(file_content),
            'word_count': word_count
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error processing file: {str(e)}'
        }), 500


@app.route('/api/parse-pdf', methods=['POST'])
def api_parse_pdf():
    """API endpoint to parse PDF files (alias for /api/upload for compatibility)"""
    return api_upload()


@app.route('/api/download-pdf', methods=['POST'])
def api_download_pdf():
    """API endpoint to download CV as PDF"""
    try:
        data = request.json
        cv_text = data.get('cv_text', '')
        
        if not cv_text:
            return jsonify({'error': 'CV text is required'}), 400
        
        pdf_buffer = generate_harvard_pdf(cv_text)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='optimized_cv.pdf'
        )
        
    except Exception as e:
        return jsonify({
            'error': f'Error generating PDF: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)