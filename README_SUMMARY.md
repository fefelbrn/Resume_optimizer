# CV Optimizer & Cover Letter Generator

## 📖 About

Intelligent web application that uses AI (OpenAI GPT) to optimize your CV and generate personalized cover letters. The application automatically analyzes skills and compares your profile with job offers to help you better target your applications.

## ✨ Main Features

### 🎯 Generation (Part 1)
- **CV Optimization**: Personalizes your CV according to job description
- **Letter Generation**: Creates natural and authentic cover letters
- **Skills Analysis**: Automatically compares your skills with the offer
- **Multi-language**: Support for French, English, Spanish
- **Adjustable Parameters**: Temperature, model, number of experiences, etc.

### 📚 History (Part 2)
- **Automatic Saving**: All your CVs and letters are saved
- **Persistence**: History remains available even after closing
- **Quick Actions**: Reload, copy, download, delete
- **Filters**: By type (CV, Letters, All)

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the application**
   ```bash
   python app.py
   ```

3. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

4. **Enter your OpenAI API key** and start!

## 🎨 Design

Modern and clean interface inspired by BetterFuture AI with:
- Responsive design
- Smooth animations
- Intuitive color coding for skills
- Explanatory tooltips
- Clear error modals

## 🔑 Prerequisites

- Python 3.8+
- OpenAI API key ([get it here](https://platform.openai.com/account/api-keys))
- Modern web browser

## 📊 Skills Analysis

The system automatically analyzes:
- ✅ **Green**: Matching skills
- ❌ **Red**: Missing skills
- 🔵 **Blue**: Interesting skills (not mentioned)
- ⚪ **Gray**: Skills only in CV

## 💾 Storage

- **History**: Saved in localStorage (persists between sessions)
- **API Key**: Never stored, only in memory
- **Files**: Processed locally, not sent to third parties

## 🛠️ Technologies

- **Backend**: Flask, LangChain, OpenAI
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **AI**: GPT-4o-mini, GPT-4, GPT-4 Turbo

## 📝 Usage

1. Load your CV (PDF or text)
2. Load the job description
3. View the skills analysis (automatic)
4. Adjust parameters if needed
5. Optimize your CV or generate a letter
6. View history to retrieve your generations

## 🔒 Security

- API key used only during session
- Data stored locally
- No transmission to third parties

## 📚 Complete Documentation

For more details, see:
- [README.md](./README.md) - Complete documentation
- [COMMANDS.md](./COMMANDS.md) - Commands guide