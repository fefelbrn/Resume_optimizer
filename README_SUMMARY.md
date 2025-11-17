# CV Optimizer - Summary

## 🎯 The Problem

Optimizing a CV for a job posting is a complex process that requires:
- **Identifying relevant skills** in both the CV and job description
- **Finding matches** between candidate skills and required skills
- **Identifying gaps** to guide improvements
- **Adapting content** by highlighting the most relevant elements
- **Generating a personalized cover letter**

Doing this manually is time-consuming, subjective, and can lead to suboptimal CVs.

## 💡 Our Solution

An intelligent web application that automates CV optimization using **AI agents** capable of:
- **Semantically understanding** the CV and job description (RAG - Retrieval-Augmented Generation)
- **Intelligently extracting and comparing** skills
- **Automatically optimizing** the CV by highlighting relevant elements
- **Conversationally assisting** users to refine the CV
- **Visualizing the process** with a workflow graph of the optimization pipeline

## 🏗️ Architecture & Technologies

### Core Technologies

- **LangChain & LangGraph**: AI agent framework for orchestrating complex workflows
- **OpenAI GPT**: Language models for understanding and generating content
- **RAG (Retrieval-Augmented Generation)**: Vectorization and semantic search for precise context
- **Chroma**: Vector database for storing and searching embeddings
- **Flask**: Python backend for the API
- **Mermaid.js**: Interactive visualization of the LangGraph workflow

### Agent-Based Architecture

The system uses **two types of agents**:

#### 1. **CV Optimization Agent** (LangGraph)
Sequential 7-step workflow:
1. Analyze CV structure
2. Extract CV skills
3. **Vectorize CV** (RAG) → Chunks indexed for semantic search
4. Extract job description skills
5. **Vectorize job description** (RAG) → Chunks indexed
6. **Intelligent skill comparison** using cosine similarity
7. Generate optimized CV with RAG context

**Why LangGraph?** 
- Structured and visualizable workflow
- Robust state management between steps
- Complete process traceability

#### 2. **Assistant Agent** (AgentExecutor + ReAct)
Conversational agent that:
- Understands natural language requests
- Uses tools to modify the CV (update sections, search, etc.)
- Maintains conversation context
- Supports custom sections (Certifications, etc.)

**Why ReAct?**
- "Reasoning + Acting" pattern: agent reasons before acting
- Intelligent decision-making on which tools to use
- Observes results before responding

### RAG: The Heart of Precision

**Problem solved**: How to find the most relevant parts of a long CV for a specific job posting?

**RAG Solution**:
1. **Vectorization**: CV and job description are split into chunks and converted to vectors (embeddings)
2. **Indexing**: Vectors are stored in a vector database (Chroma)
3. **Semantic search**: To generate the optimized CV, retrieve the most similar chunks (top 5 CV, top 3 JD)
4. **Cosine similarity**: Normalized scores (0-100%) to measure relevance

**Result**: The LLM generates the optimized CV based on the most relevant parts, not the entire document.

## 📊 Key Features

### 1. Automatic Optimization
- Intelligent skill extraction (CV + Job description)
- Comparison with cosine similarity
- Optimized CV generation with RAG context
- Multi-language support (FR, EN, ES)

### 2. Skills Analysis
- **Match rate**: Percentage of job skills found in CV (e.g., 50% = 8/16 skills)
- **Similarity score**: Average similarity of matched skills (e.g., 92%)
- Color-coded tags: Green (match), Red (missing), Gray (CV only), Blue (interesting)

### 3. Conversational Assistant
- CV modifications in natural language
- Correction of detected skills
- Update specific sections
- Conversation history maintained

### 4. Logs & Visualization
- **LangGraph Graph**: Interactive visualization of the workflow (7 nodes, execution flow)
- **RAG Metrics**: Vectorization details, chunks, similarity scores
- **Statistics**: Match rate vs similarity score, execution steps

### 5. Cover Letter Generation
- Personalized based on CV and job description
- Configurable length
- Multi-language support

## 🎬 Video Demonstrations

📹 **Frontend**: [Watch on YouTube](https://www.youtube.com/watch?v=38EIjO1rtUs) - User interface and features

📹 **Backend**: [Watch on YouTube](https://www.youtube.com/watch?v=41vr0_noGPg) - Technical architecture and implementation

## 🚀 Technology Stack

- **Backend**: Flask (Python)
- **AI**: LangChain, LangGraph, OpenAI GPT
- **RAG**: OpenAI Embeddings, Chroma (vector DB)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Visualization**: Mermaid.js (graphs)
- **PDF**: PyPDF2, pdfplumber, ReportLab

## 💡 Key Strengths

✅ **Intelligent agents**: Autonomous reasoning on which tools to use  
✅ **Integrated RAG**: Precise context through semantic search  
✅ **Visualizable workflow**: LangGraph graph to understand the process  
✅ **Clear metrics**: Distinction between match rate and similarity score  
✅ **Conversational assistant**: Modifications in natural language  
✅ **Modular architecture**: Reusable tools, independent agents  

## 📈 Result

A system that transforms a manual and subjective process into an automated, intelligent, and transparent workflow, enabling candidates to create optimized CVs in minutes instead of hours.
