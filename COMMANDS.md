For fefe

cd "/Users/fefe/Desktop/Cours M1 Albert/Semestre 1/Agentic systems/Projet/Resume optimizer/Resume Optimizer" && python app.py








# Commands Guide - CV Optimizer

## 🚀 Quick Start

### Installation (une seule fois)
```bash
pip install -r requirements.txt
mkdir uploads
```

### Lancer l'application
```bash
python app.py
```

Puis ouvrez : **http://127.0.0.1:5000**

---

## 📚 Guide Complet

### Installation détaillée

#### 1. Vérifier la version Python
```bash
python --version
# Doit afficher Python 3.8 ou supérieur
```

#### 2. Créer un environnement virtuel (recommandé)

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

#### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

#### 4. Créer le dossier uploads
```bash
mkdir uploads
```

### Méthodes de lancement

#### Méthode 1: Commande Python directe
```bash
python app.py
```

#### Méthode 2: Script (macOS/Linux)
```bash
chmod +x run.sh
./run.sh
```

#### Méthode 3: Flask CLI
```bash
export FLASK_APP=app.py
flask run
```

**Windows:**
```bash
set FLASK_APP=app.py
flask run
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