# Commands Guide - CV Optimizer

Quick reference for local development commands.

## Installation

### 1. Check Python version
```bash
python --version
# Should display Python 3.8 or higher
```

### 2. Create virtual environment (recommended)

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create uploads folder
```bash
mkdir uploads
```

## Launch

### Method 1: Direct Python command
```bash
python app.py
```

### Method 2: Using the script (macOS/Linux)
```bash
chmod +x run.sh
./run.sh
```

### Method 3: Using Flask CLI
```bash
export FLASK_APP=app.py
flask run
```

**Windows:**
```bash
set FLASK_APP=app.py
flask run
```

### Access the application
Open your browser and go to:
```
http://127.0.0.1:5000
```
or
```
http://localhost:5000
```

## Development

### Change port
Edit `app.py` line 217:
```python
app.run(debug=True, host='127.0.0.1', port=8080)  # Change port to 8080
```

### Disable debug mode
Edit `app.py` line 217:
```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

## Troubleshooting

### Port already in use

**macOS/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Module not found
```bash
# Make sure virtual environment is activated
pip install -r requirements.txt
```

### Python not found

**macOS/Linux:**
```bash
python3 --version
python3 app.py
```

## Useful Commands

### Update dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Deactivate virtual environment
```bash
deactivate
```

### Check Flask version
```bash
python -c "import flask; print(flask.__version__)"
```

### Test API endpoint
```bash
curl http://127.0.0.1:5000/
```

---

For more details, see [README.md](./README.md)
