# Commands - CV Optimizer

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Application

### Start Flask Server

```bash
python3 app.py
```

The application will be available at: **http://localhost:5001**

### Stop Application

Press `Ctrl+C` in the terminal, or:

```bash
pkill -9 -f "python.*app.py"
```

## Development

### Check if Port is Available

```bash
lsof -ti:5001
```

### Kill Process on Port 5001

```bash
lsof -ti:5001 | xargs kill -9
```

### Test Application

```bash
curl http://localhost:5001/
```

## Git Commands

### Commit Changes

```bash
git add -A
git commit -m "Your commit message"
git push
```

### Check Status

```bash
git status
```