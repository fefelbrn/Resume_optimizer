# Commands Guide - CV Optimizer

## 🚀 Step-by-Step Guide to Run on Localhost

### Step 1: Open Terminal
- **macOS**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Win + R`, type "cmd", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### Step 2: Navigate to Project Directory
```bash
cd "file/path"
```

**Note**: Adjust the path if your project is located elsewhere.

### Step 3: Check Python Installation
```
python3 --version
```


### Step 4: Install Dependencies
```
pip3 install -r requirements.txt
```

**What this does**: Creates a folder to store uploaded PDF/TXT files

### Step 6: Launch the Application
```
python3 app.py
```

## 🛑 How to Stop the Application

### Method 1: In Terminal
- Press `Ctrl + C` in the terminal where the app is running

### Method 2: Kill Process (if terminal is closed)
**macOS/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```