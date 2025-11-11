# CV Optimizer & Cover Letter Generator

A complete web application to optimize your CV and generate personalized cover letters using AI (OpenAI GPT). The application also includes an automatic skills analysis system to compare your profile with job offers.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Technologies Used](#technologies-used)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🎯 Generation (Part 1 - Red)

#### 1. **CV Optimization**
- CV customization according to job description
- Filtering by number of experiences (min/max)
- Date filtering (keep only the last X years)
- Multi-language support (French, English, Spanish)
- Temperature adjustment to control creativity
- OpenAI model selection (GPT-4o-mini, GPT-4, GPT-4 Turbo, GPT-3.5 Turbo)

#### 2. **Cover Letter Generation**
- Personalized and natural letters
- Target word count adjustment
- Letter conventions adapted to each language
- Authentic style to avoid AI detection

#### 3. **Automatic Skills Analysis**
- Automatic extraction of CV skills
- Automatic extraction of job offer skills
- Intelligent matching with color coding:
  - **Gray**: Skills only in CV
  - **Red**: Missing required skills
  - **Green**: Matching skills
  - **Blue**: Interesting CV skills (not mentioned in offer)
- Match statistics

#### 4. **User Interface**
- PDF/TXT file upload
- Text paste from clipboard
- Explanatory tooltips for technical parameters
- Error modals with clear messages
- Modern design inspired by BetterFuture AI

### 📚 History (Part 2 - Green)

- Automatic saving in localStorage
- Persistent history between sessions
- Filters by type (CV, Letters, All)
- Actions on each item:
  - Reload (restores parameters)
  - Copy
  - Download
  - Delete
- Maximum limit of 50 items

## 🏗️ Architecture

### Backend (Flask)

```
app.py                    # Main Flask application
utils/
  ├── cv_optimizer.py     # CV optimization
  ├── letter_generator.py # Letter generation
  ├── pdf_parser.py       # PDF text extraction
  └── skills_matcher.py   # Skills matching
```

### Frontend

```
templates/
  └── index.html          # Main interface
static/
  ├── css/
  │   └── style.css       # Styles (BetterFuture-inspired design)
  └── js/
      └── main.js         # JavaScript logic
```

### Data Flow

1. **Upload/Paste** → Text extraction → Storage in state
2. **Skills extraction** → OpenAI API → Skills storage
3. **Matching** → Comparison → Display with color coding
4. **Generation** → OpenAI API → Result → History saving

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key (get it at [platform.openai.com](https://platform.openai.com/account/api-keys))

### Installation Steps

1. **Clone the repository** (or download the files)

```bash
git clone <repo-url>
cd Test2
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv .venv
```

3. **Activate the virtual environment**

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Create the uploads folder** (if necessary)

```bash
mkdir uploads
```

## ⚙️ Configuration

### Environment Variables (optional)

You can create a `.env` file at the project root:

```env
OPENAI_API_KEY=your-api-key-here
FLASK_ENV=development
FLASK_DEBUG=True
```

**Note:** The application also works without a `.env` file - the API key can be entered directly in the interface.

### Application Configuration

Default settings are defined in `app.py`:

- **Port**: 5000
- **Host**: 127.0.0.1
- **Debug mode**: Enabled by default
- **Max file size**: 10MB
- **Accepted formats**: PDF, TXT

## 💻 Usage

### Launch the application

See [COMMANDS.md](./COMMANDS.md) for detailed commands.

**Quick method:**
```bash
python app.py
```

**Or with the script:**
```bash
chmod +x run.sh
./run.sh
```

### Access the application

Open your browser and go to: `http://127.0.0.1:5000`

### Usage Workflow

1. **Enter your OpenAI API key** in the provided field
2. **Load or paste your CV** (PDF or text)
3. **Load or paste the job description** (PDF or text)
4. **View the skills analysis** (automatic)
5. **Adjust parameters** if necessary:
   - Output language
   - Model
   - Temperature
   - Number of experiences
   - Number of words for the letter
6. **Optimize the CV** or **Generate the letter**
7. **View history** to retrieve your generations

## 📁 Project Structure

```
Test2/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── run.sh                     # Launch script
├── README.md                  # Complete documentation
├── README_SUMMARY.md          # Project summary
├── COMMANDS.md                # Commands guide
├── templates/
│   └── index.html             # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css         # CSS styles
│   └── js/
│       └── main.js            # Main JavaScript
├── utils/
│   ├── __init__.py
│   ├── cv_optimizer.py       # CV optimization module
│   ├── letter_generator.py   # Letter generation module
│   ├── pdf_parser.py         # PDF extraction module
│   └── skills_matcher.py     # Skills matching module
└── uploads/                  # Folder for uploaded files
```

## 🔌 API Endpoints

### `GET /`
Displays the main application page.

### `POST /api/parse-pdf`
Parses a PDF or TXT file and returns the extracted text.

**Request:**
- `file`: PDF or TXT file (multipart/form-data)

**Response:**
```json
{
  "text": "Extracted content...",
  "filename": "cv.pdf",
  "word_count": 500
}
```

### `POST /api/extract-skills`
Extracts main skills from a CV or job description.

**Request:**
```json
{
  "text": "CV or offer text...",
  "text_type": "cv" | "job",
  "api_key": "sk-...",
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "skills": ["Python", "JavaScript", "React", ...],
  "count": 15,
  "text_type": "cv"
}
```

### `POST /api/match-skills`
Compares and matches skills between CV and offer.

**Request:**
```json
{
  "cv_skills": ["Python", "React", ...],
  "job_skills": ["Python", "Vue.js", ...],
  "cv_text": "CV text...",
  "job_text": "Job description...",
  "api_key": "sk-...",
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "matched": ["Python", ...],
  "cv_only": ["React", ...],
  "job_only": ["Vue.js", ...],
  "interesting": ["TypeScript", ...],
  "stats": {
    "total_cv": 15,
    "total_job": 12,
    "matched_count": 8,
    "missing_count": 4,
    "match_percentage": 66.7
  }
}
```

### `POST /api/optimize-cv`
Optimizes a CV according to a job description.

**Request:**
```json
{
  "cv_text": "CV text...",
  "job_description": "Job description...",
  "api_key": "sk-...",
  "language": "fr",
  "model": "gpt-4o-mini",
  "temperature": 0.3,
  "min_experiences": 3,
  "max_experiences": 8,
  "max_date_years": 5
}
```

**Response:**
```json
{
  "optimized_cv": "Optimized CV...",
  "model_used": "gpt-4o-mini",
  "temperature": 0.3,
  "word_count": 1200
}
```

### `POST /api/generate-letter`
Generates a personalized cover letter.

**Request:**
```json
{
  "cv_text": "CV text...",
  "optimized_cv": "Optimized CV (optional)...",
  "job_description": "Job description...",
  "api_key": "sk-...",
  "language": "fr",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "target_words": 300
}
```

**Response:**
```json
{
  "cover_letter": "Cover letter...",
  "word_count": 295,
  "target_words": 300,
  "model_used": "gpt-4o-mini",
  "temperature": 0.7
}
```

## 🛠️ Technologies Used

### Backend
- **Flask 3.0+**: Python web framework
- **LangChain**: LLM application framework
- **LangChain OpenAI**: OpenAI integration
- **PyPDF2 / pdfplumber**: PDF text extraction
- **Flask-CORS**: CORS management

### Frontend
- **HTML5**: Structure
- **CSS3**: Styles (modern design, CSS variables)
- **JavaScript (ES6+)**: Client logic
- **localStorage API**: Data persistence

### AI
- **OpenAI GPT**: Language models
  - GPT-4o-mini (recommended)
  - GPT-4
  - GPT-4 Turbo
  - GPT-3.5 Turbo

## 📦 Dependencies

See `requirements.txt` for the complete list:

- `flask>=3.0.0`
- `flask-cors>=4.0.0`
- `langchain>=0.3.0`
- `langchain-openai>=0.1.22`
- `pydantic>=2.8.0`
- `python-dotenv>=1.0.1`
- `PyPDF2>=3.0.0`
- `pdfplumber>=0.10.0`
- `openai>=1.0.0`

## 🔧 Troubleshooting

### Error 401 - Invalid API key

**Problem:** "Incorrect API key provided"

**Solutions:**
1. Verify that you copied the complete key (starts with `sk-`)
2. Get a new key at [platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
3. Verify that your OpenAI account has available credits

### Error when uploading PDF

**Problem:** "Could not extract text from file"

**Solutions:**
1. Verify that the file is a valid PDF
2. Try converting the PDF to text first
3. Verify that the PDF is not password protected
4. Check the file size (max 10MB)

### Application won't start

**Problem:** Launch error

**Solutions:**
1. Verify that Python 3.8+ is installed: `python --version`
2. Verify that all dependencies are installed: `pip install -r requirements.txt`
3. Verify that port 5000 is not already in use
4. Check error logs in the terminal

### Skills don't display

**Problem:** Empty skills section

**Solutions:**
1. Verify that your API key is valid
2. Wait a few seconds (extraction in progress)
3. Verify that CV and job description are loaded
4. Check the browser console (F12) for errors

### History doesn't persist

**Problem:** History disappears after closing

**Solutions:**
1. Verify that your browser allows localStorage
2. Don't navigate in private mode
3. Verify that cookies are not blocked

## 🎨 Customization

### Modify colors

Edit `static/css/style.css` and modify CSS variables in `:root`:

```css
:root {
    --primary-color: #2563eb;
    --success-color: #10b981;
    --error-color: #ef4444;
    /* ... */
}
```

### Modify default models

Edit `templates/index.html` to add/remove models in the select.

### Modify prompts

Edit files in `utils/`:
- `cv_optimizer.py`: CV optimization prompts
- `letter_generator.py`: Letter generation prompts
- `skills_matcher.py`: Skills extraction prompts

## 🔒 Security

- **API Key**: Never stored on server, only in memory during session
- **Uploaded files**: Stored locally, not sent to third parties
- **Data**: All data remains on your machine (localStorage)
- **HTTPS**: Recommended in production (requires server configuration)

## 🚀 Deployment

### Production

To deploy in production:

1. **Disable debug mode** in `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

2. **Use a WSGI server** (e.g., Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Configure HTTPS** with a reverse proxy (Nginx)

4. **Environment variables**: Use a secure `.env` file

## 📝 Development Notes

### Prompt Structure

Prompts are designed to:
- Avoid AI detection (natural letters)
- Maintain authenticity (no false information)
- Adapt to context (language, conventions)

### Error Handling

- OpenAI errors parsed and translated to English
- Clear user messages with instructions
- Detailed server-side logs for debugging

### Performance

- Debounce on skills extraction (2 seconds)
- Limit of 50 items in history
- Asynchronous extraction to not block interface

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under MIT. See the `LICENSE` file for more details.

## 👤 Author

Developed as part of M1 Albert course - Agentic Systems

## 🙏 Acknowledgments

- Design inspired by [BetterFuture AI](https://betterfutureai-5e0926.webflow.io/)
- OpenAI for language models
- LangChain for LLM framework

---

For a quick summary, see [README_SUMMARY.md](./README_SUMMARY.md)  
For commands, see [COMMANDS.md](./COMMANDS.md)
