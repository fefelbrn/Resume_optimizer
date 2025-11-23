# CV Optimizer - Agent-Based Architecture

A comprehensive CV optimization and cover letter generation application built with LangChain and LangGraph, using an agent-based architecture for intelligent document processing.

## Overview

This project is a complete rewrite of a CV optimizer application, restructured from the ground up to leverage LangChain's agent framework and LangGraph's workflow capabilities. We've eliminated all fallback implementations and built a pure agent-based system that uses tools, state management, and conversational memory.

## 📹 Video Demonstrations

We've created two video presentations to showcase the application:

- **Frontend Presentation**: [Watch on YouTube](https://www.youtube.com/watch?v=38EIjO1rtUs) - Demonstrates the user interface, features, and user experience of the CV optimizer application
- **Backend Presentation**: [Watch on YouTube](https://www.youtube.com/watch?v=41vr0_noGPg) - Explains the technical architecture, agent-based system, and implementation details

These videos provide a comprehensive overview of both the frontend functionality and the backend architecture. Watch them to get a complete understanding of how the system works!

## Architecture

### Why We Chose This Architecture

We decided to rebuild the application using agents because:

1. **Modularity**: Each agent has a specific responsibility and can be developed, tested, and improved independently
2. **Extensibility**: New tools and capabilities can be added without modifying core agent logic
3. **Intelligence**: Agents can reason about which tools to use and in what order, making the system more flexible
4. **Maintainability**: Clear separation between tools, agents, and workflows makes the codebase easier to understand and maintain

### Core Components

#### 1. CV Optimization Agent (`utils/cv_optimizer_agent.py`)

**What it does**: Optimizes a CV to match a specific job description using a multi-step workflow.

**How it works**: 
- Built with **LangGraph** using a `StateGraph` workflow
- Implements a 7-node sequential pipeline with RAG (Retrieval-Augmented Generation):
  1. **Analyze Structure**: Uses `analyze_cv_structure_tool` to identify CV sections
  2. **Extract CV Skills**: Uses `extract_skills_tool` to identify candidate skills
  3. **Index CV in RAG**: Vectorizes CV chunks for semantic search
  4. **Extract Job Skills**: Uses `extract_skills_tool` to identify required job skills
  5. **Index JD in RAG**: Vectorizes job description chunks for semantic search
  6. **Compare Skills**: Uses `compare_skills_tool_with_rag` to find matches, gaps, and interesting skills using cosine similarity
  7. **Generate Optimized CV**: Uses LLM with RAG context from previous steps to create tailored CV

**Why this approach**: The workflow ensures each step builds on the previous one, providing rich context for the final optimization. The state management allows us to track progress and handle errors gracefully.

#### 2. Assistant Agent (`utils/assistant_agent.py`)

**What it does**: Provides conversational assistance to refine CVs and correct skill detection.

**How it works**:
- Uses **AgentExecutor** with **ReAct** pattern (Reasoning + Acting)
- Implements conversational memory with `ConversationBufferMemory`
- Has access to 5 tools for CV manipulation:
  - `update_cv_section`: Modify specific CV sections
  - `search_cv`: Find content in CV
  - `extract_cv_skills`: Extract skills from CV text
  - `extract_job_skills`: Extract skills from job description
  - `compare_skills`: Compare CV and job skills

**Why this approach**: The ReAct pattern allows the agent to reason about user requests, decide which tools to use, execute them, and observe results before responding. This creates a more intelligent and responsive assistant.

#### 3. Tools (`utils/tools.py`)

**What they are**: Reusable functions that agents can call to perform specific tasks.

**How they work**:
- Implemented using LangChain's `@tool` decorator
- Each tool is self-contained and can be used by any agent
- Tools include:
  - `extract_skills_tool`: Extracts skills from text using LLM
  - `compare_skills_tool`: Compares CV and job skills, identifies matches/gaps
  - `analyze_cv_structure_tool`: Analyzes CV structure and sections
  - `update_cv_section_tool`: Updates specific CV sections
  - `search_cv_content_tool`: Searches for content in CV

**Why this approach**: Tools provide a clean abstraction layer. Agents don't need to know implementation details, just what each tool does. This makes the system more modular and testable.

#### 4. RAG System (`utils/rag_system.py`)

**What it does**: Handles vectorization, storage, and semantic search of CVs and Job Descriptions using embeddings.

**How it works**:
- Uses OpenAI embeddings to convert text chunks into vectors
- Stores vectors in Chroma vector database
- Performs semantic search to retrieve most relevant chunks
- Calculates cosine similarity scores (normalized to 0-1 range) for ranking
- Provides context-aware retrieval for CV optimization

**Why this approach**: RAG enables the system to focus on the most relevant parts of the CV and job description, improving the quality of optimization by using semantic understanding rather than simple keyword matching.

#### 5. Skills Matcher (`utils/skills_matcher.py`)

**What it does**: Wrapper module that provides a clean API for skill extraction and matching.

**How it works**: Uses the tools from `tools.py` to provide simplified functions for the frontend.

**Why this approach**: Provides a clean separation between the agent internals and the API layer.

#### 6. Observability System (`utils/langfuse_config.py`)

**What it does**: Provides unified tracing and observability for the entire LangGraph workflow using Langfuse.

**How it works**:
- Creates a single trace for each CV optimization workflow
- All nodes (analyze_structure, extract_cv_skills, etc.) create spans under the same trace
- Captures input parameters (CV length, job description length, model, etc.) at trace level
- Updates trace output with results (optimized CV length, word count, skills counts, etc.)
- Links all LLM calls and tool invocations to the parent trace

**Why this approach**: 
- **Unified view**: Instead of multiple separate traces, you see one complete workflow trace
- **Better debugging**: All operations are grouped together, making it easier to understand the full optimization process
- **Performance insights**: Track latency and costs across the entire workflow
- **Session tracking**: Monitor multiple optimization sessions over time

### Application Flow

1. **User uploads CV and job description** → Files are parsed and text is extracted
2. **Skills are automatically extracted** → Both CV and job description skills are identified
3. **Skills are matched** → System identifies matches, gaps, and interesting skills using RAG and cosine similarity
4. **User requests CV optimization** → CV Optimization Agent runs the 7-step workflow with RAG:
   - CV and JD are vectorized and indexed
   - Semantic search retrieves most relevant chunks
   - Skills are compared using embeddings
   - CV is optimized with RAG context
5. **Optimized CV is generated** → User can review and download
6. **Execution logs are available** → User can view detailed logs including:
   - Graph visualization of the LangGraph workflow
   - RAG vectorization details (chunks, similarity scores)
   - Skills matching statistics (match rate vs similarity score)
   - Agent execution steps
7. **User can request adjustments** → Assistant Agent uses tools to make changes
8. **Conversation history is maintained** → Assistant remembers context across requests

## Technology Stack

- **Backend**: Flask (Python web framework)
- **AI Framework**: LangChain, LangGraph
- **LLM**: OpenAI GPT models (configurable)
- **Observability**: Langfuse (tracing and monitoring)
- **RAG**: OpenAI Embeddings, Chroma (vector database)
- **PDF Processing**: PyPDF2, pdfplumber
- **PDF Generation**: ReportLab
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Visualization**: Mermaid.js (workflow graphs)

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- (Optional) Langfuse account for observability

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "projet resume optimizer"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root (optional, for Langfuse observability):
   ```env
   # Langfuse Configuration (Optional - for observability)
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
   ```
   
   **Note**: The OpenAI API key is provided by users through the web interface and is not stored.

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5001`

## Project Structure

```
.
├── app.py                      # Flask application and API endpoints
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (optional, for Langfuse)
├── templates/
│   └── index.html             # Frontend interface
├── static/
│   ├── css/
│   │   └── style.css         # Styling
│   └── js/
│       └── main.js           # Frontend logic
├── uploads/                   # Temporary storage for uploaded files
└── utils/
    ├── __init__.py
    ├── cv_optimizer_agent.py  # LangGraph workflow for CV optimization
    ├── assistant_agent.py     # ReAct agent for conversational assistant
    ├── tools.py               # LangChain tools (@tool decorator)
    ├── rag_system.py         # RAG system for vectorization and semantic search
    ├── skills_matcher.py     # Skills extraction and matching API
    ├── langfuse_config.py   # Langfuse configuration for observability
    ├── pdf_parser.py         # PDF text extraction
    ├── pdf_generator.py      # PDF generation (Harvard template)
    └── letter_generator.py   # Cover letter generation
```

## Key Design Decisions

### 1. Agent-Based Architecture
We chose to use agents instead of simple function calls because:
- Agents can reason about which tools to use
- They can handle complex, multi-step tasks
- They provide better error handling and recovery
- They make the system more extensible

### 2. LangGraph for CV Optimization
We used LangGraph instead of a simple chain because:
- The optimization process has clear sequential steps
- State management is crucial for tracking intermediate results
- Error handling is easier with explicit workflow nodes
- The workflow is visualizable and debuggable
- Graph structure can be exported and visualized in the logs for transparency

### 3. AgentExecutor for Assistant
We used AgentExecutor with ReAct because:
- The assistant needs to make decisions about which tools to use
- Conversational context is important
- The ReAct pattern (think → act → observe) fits perfectly
- Memory management is built-in

### 4. Tool-Based Design
We implemented everything as tools because:
- Tools are reusable across agents
- They provide a clean API boundary
- They're easy to test independently
- They make the system more modular

### 5. RAG for Context-Aware Optimization
We integrated RAG (Retrieval-Augmented Generation) because:
- Semantic search finds the most relevant parts of CV and job description
- Cosine similarity provides accurate relevance scoring
- Vectorization enables efficient similarity calculations
- Context-aware generation produces more targeted optimizations
- Similarity scores are normalized (0-1) for consistent interpretation

### 6. No Fallbacks
We removed all fallback implementations because:
- Agents should handle errors gracefully themselves
- Fallbacks create code duplication
- They make the system harder to maintain
- They hide architectural issues

### 7. Unified Observability with Langfuse
We integrated Langfuse for observability because:
- Provides a single unified trace for the entire LangGraph workflow
- All nodes create spans under the same trace, not separate traces
- Captures input/output at the trace level for better debugging
- Enables performance monitoring and cost tracking
- Makes it easy to understand the complete optimization flow

## API Endpoints

- `GET /` - Serve the main interface
- `POST /api/optimize-cv` - Optimize CV using LangGraph agent
- `POST /api/generate-letter` - Generate cover letter
- `POST /api/extract-skills` - Extract skills from text
- `POST /api/match-skills` - Match CV and job skills
- `POST /api/assistant` - Conversational assistant (AgentExecutor)
- `POST /api/parse-pdf` - Parse uploaded PDF/TXT files
- `POST /api/download-pdf` - Download CV as PDF

## Configuration

### Application Settings

The application runs on port **5001** (changed from 5000 to avoid conflicts with macOS AirPlay Receiver).

### User Configuration (Web Interface)

All user configuration is done through the web interface:
- **OpenAI API key**: User-provided, not stored (used only for the current session)
- **Model selection**: GPT-4o-mini, GPT-4, etc.
- **Temperature settings**: Controls randomness in LLM responses
- **Language selection**: French, English, Spanish
- **CV optimization parameters**: Min/max experiences, date filters

### Observability Configuration (Optional)

The application supports **Langfuse** for observability and tracing. This is optional but recommended for monitoring and debugging.

**To enable Langfuse**:
1. Create a Langfuse account at [langfuse.com](https://langfuse.com)
2. Get your public key and secret key from the Langfuse dashboard
3. Create a `.env` file in the project root:
   ```env
   LANGFUSE_PUBLIC_KEY=your_public_key_here
   LANGFUSE_SECRET_KEY=your_secret_key_here
   LANGFUSE_HOST=https://cloud.langfuse.com  # Optional
   ```

**What Langfuse provides**:
- **Unified tracing**: All nodes of the LangGraph workflow are traced as a single trace with multiple spans
- **Input/Output tracking**: Trace input (optimization parameters) and output (results) are captured
- **Performance monitoring**: Latency and cost tracking for each operation
- **Debugging**: Detailed logs of all LLM calls and tool invocations
- **Session management**: Track multiple optimization sessions

**Without Langfuse**: The application works normally, but observability features are disabled.

## Development History

We started with a working application that had mixed implementations (some agent-based, some not). We decided to:

1. **Clean up the codebase** - Remove all non-agent implementations
2. **Rebuild with pure agents** - Use LangGraph for workflows, AgentExecutor for assistants
3. **Implement proper tools** - All functionality as LangChain tools
4. **Fix integration issues** - Ensure frontend and backend work seamlessly
5. **Test and verify** - Make sure all features work with the new architecture

The result is a clean, maintainable, and extensible agent-based system that leverages the full power of LangChain and LangGraph.

## Detailed Workflow Examples

### CV Optimization Workflow

When a user requests CV optimization, here's exactly what happens:

1. **State Initialization**: The `CVOptimizationState` is created with all input parameters (CV text, job description, API key, model, etc.)

2. **Node 1 - Analyze Structure**: 
   - The `analyze_cv_structure_tool` is invoked
   - It parses the CV text to identify sections (Experience, Education, Skills, etc.)
   - Results are stored in `state["cv_structure"]`
   - Agent logs: "✓ Analyzed CV structure: Found X sections"

3. **Node 2 - Extract CV Skills**:
   - The `extract_skills_tool` is called with `text_type="cv"`
   - An LLM analyzes the CV text and extracts all skills
   - Skills are returned as a JSON array
   - Results stored in `state["cv_skills"]`
   - Agent logs: "✓ Extracted X skills from CV"

4. **Node 3 - Index CV in RAG**:
   - CV text is split into chunks (default: 500 characters with 50 overlap)
   - Chunks are vectorized using OpenAI embeddings
   - Vectors are stored in Chroma vector database
   - Results stored in `state["rag_system"]`
   - Agent logs: "✓ Indexed CV in vector database: X chunks"

5. **Node 4 - Extract Job Skills**:
   - Same `extract_skills_tool` is called with `text_type="job"`
   - The job description is analyzed for required/preferred skills
   - Results stored in `state["job_skills"]`
   - Agent logs: "✓ Extracted X skills from job description"

6. **Node 5 - Index JD in RAG**:
   - Job description is split into chunks
   - Chunks are vectorized and stored in vector database
   - Results stored in `state["rag_system"]`
   - Agent logs: "✓ Indexed job description in vector database: X chunks"

7. **Node 6 - Compare Skills**:
   - The `compare_skills_tool_with_rag` performs intelligent matching using embeddings
   - Uses cosine similarity to match CV and job skills
   - It identifies: matched skills (green), missing skills (red), CV-only skills (gray), interesting skills (blue)
   - Provides match rate (percentage of job skills found) and average similarity score
   - Results stored in `state["skills_comparison"]`
   - Agent logs: "✓ Compared skills using RAG + cosine similarity: X matches, Y missing"

8. **Node 7 - Generate Optimized CV**:
   - RAG system retrieves most relevant CV and JD chunks using semantic search
   - Cosine similarity scores are calculated for each chunk (normalized to 0-1 range)
   - All previous results are compiled into context
   - An LLM prompt is constructed with:
     - Original CV
     - Job description
     - RAG-retrieved relevant chunks (top 5 CV chunks, top 3 JD chunks)
     - CV structure information
     - Skills analysis (matches, gaps, interesting skills with match rate and similarity scores)
     - Optimization parameters (min/max experiences, date filters)
   - The LLM generates a tailored CV using the most relevant context
   - Results stored in `state["optimized_cv"]` and `state["sources"]`
   - Agent logs: "✓ Generated optimized CV (X words) with RAG context"

9. **Return Results**: The final state is returned with the optimized CV, all intermediate results, RAG sources, graph structure, and agent logs.

### Assistant Agent Workflow

When a user asks the assistant to make changes:

1. **Request Processing**: User message is received along with context (current CV, job description, skills)

2. **Memory Retrieval**: Conversation history is loaded from `ConversationBufferMemory`

3. **Tool Selection**: The agent (using ReAct pattern) reasons about which tools to use:
   - "User wants to add Python skill" → Use `search_cv` to find Skills section, then `update_cv_section`
   - "User wants to correct a typo" → Use `search_cv` to locate the error, then `update_cv_section`
   - "User wants to check skills" → Use `extract_cv_skills` and `compare_skills`

4. **Tool Execution**: Selected tools are executed with appropriate parameters

5. **Result Observation**: Agent observes tool results and decides if more actions are needed

6. **Response Generation**: Agent formulates a response explaining what was done

7. **Memory Update**: Conversation is saved to memory for future context

## Technical Deep Dive

### State Management in LangGraph

The `CVOptimizationState` is a TypedDict that ensures type safety and clear state structure:

```python
class CVOptimizationState(TypedDict):
    cv_text: str
    job_description: str
    api_key: str
    # ... other fields
    cv_structure: Optional[Dict[str, Any]]
    cv_skills: List[str]
    job_skills: List[str]
    skills_comparison: Optional[Dict[str, Any]]
    optimized_cv: Optional[str]
    agent_logs: List[str]
```

Each node receives the full state, can read any field, and must return the complete state. This ensures data consistency throughout the workflow.

### Tool Implementation Details

All tools use the `@tool` decorator from LangChain:

```python
@tool
def extract_skills_tool(text: str, text_type: str, api_key: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Extract skills from a CV or job description text."""
    # Implementation
```

The decorator automatically:
- Creates tool metadata (name, description, parameters)
- Validates inputs
- Handles errors
- Makes tools discoverable by agents

### Memory Management

The assistant agent uses `ConversationBufferMemory` which:
- Stores conversation history as a list of messages
- Maintains context across multiple requests
- Supports both user and assistant messages
- Can be persisted or cleared as needed

Each session has its own memory instance, allowing multiple users to use the assistant simultaneously without context mixing.

### Error Handling Strategy

Agents handle errors at multiple levels:

1. **Tool Level**: Each tool has try/except blocks and returns error status
2. **Node Level**: Each LangGraph node catches exceptions and updates state with error information
3. **Agent Level**: AgentExecutor has `handle_parsing_errors=True` to recover from tool call parsing issues
4. **Application Level**: Flask endpoints catch exceptions and return user-friendly error messages

This multi-layer approach ensures the system is robust and provides helpful error messages.

## Execution Logs and Visualization

The application provides comprehensive execution logs accessible via the "View Logs" button after CV optimization:

### Log Features

1. **Simplified Log**: Human-readable summary of the optimization process
   - Execution summary (model, temperature, word count)
   - RAG vectorization details (chunk counts, sizes, similarity scores)
   - Skills extraction and matching statistics
   - Clear distinction between:
     - **Match rate**: Percentage of job skills found in CV (e.g., 50% = 8/16 skills)
     - **Average similarity**: How similar the matched skills are (e.g., 92% similarity)
   - Agent execution steps

2. **Graph Visualization**: Interactive LangGraph workflow diagram
   - Visual representation of all 7 nodes in the optimization pipeline
   - Color-coded nodes (green = success, red = error, gray = pending)
   - Shows execution flow with arrows
   - Displays tools used by each node
   - Generated using Mermaid.js

3. **Full Log**: Complete JSON dump of all execution data for debugging

### RAG Metrics in Logs

- **CV/JD Vectorization**: Number of chunks, total characters, average chunk size, size range
- **Semantic Search**: Query used, number of chunks retrieved, cosine similarity scores (0-100%)
- **Skills Matching**: Match rate (X/Y job skills found) and average similarity of matched skills

## Performance Considerations

- **Caching**: Skills extraction results are cached to avoid redundant API calls
- **Debouncing**: Frontend debounces skill extraction requests (3 seconds) to reduce API usage
- **Concurrent Control**: Flags prevent multiple simultaneous extractions
- **Rate Limiting**: The system handles OpenAI rate limits gracefully with user-friendly messages
- **State Persistence**: LangGraph state is maintained throughout the workflow, avoiding redundant processing
- **RAG Optimization**: Vector stores are session-based and can be cleared to free memory
- **Cosine Similarity**: Scores are normalized to 0-1 range for consistent interpretation

## Security Considerations

- **API Key Handling**: User API keys are never stored, only used for the current session
- **File Upload Limits**: Maximum file size of 10MB, only PDF and TXT allowed
- **Input Validation**: All inputs are validated before processing
- **Error Messages**: Error messages don't expose sensitive information

## Observability & Monitoring

### Langfuse Integration

The application uses **Langfuse** for comprehensive observability of the agent workflows. When configured, Langfuse provides:

#### Unified Trace Structure

Each CV optimization creates a **single trace** with the following structure:

```
Trace: "cv_optimization"
├── Input: {cv_text_length, job_description_length, model, temperature, ...}
├── Span: analyze_structure
│   └── Tool: analyze_cv_structure_tool
├── Span: extract_cv_skills
│   └── Tool: extract_skills_tool
│       └── LLM Call: ChatOpenAI
├── Span: index_cv_rag
│   └── RAG: Vectorization and indexing
├── Span: extract_job_skills
│   └── Tool: extract_skills_tool
│       └── LLM Call: ChatOpenAI
├── Span: index_jd_rag
│   └── RAG: Vectorization and indexing
├── Span: compare_skills
│   └── Tool: compare_skills_tool_with_rag
│       └── LLM Call: ChatOpenAI (if needed)
└── Span: generate_cv
    └── LLM Call: ChatOpenAI
    └── Output: {optimized_cv_length, word_count, skills_counts, ...}
```

#### Benefits

- **Single trace view**: All workflow steps are visible in one place
- **Input/Output tracking**: See what went in and what came out
- **Performance metrics**: Latency and cost for each operation
- **Error tracking**: Identify which node failed and why
- **Session correlation**: Track multiple optimizations in the same session

#### Accessing Traces

1. Go to your Langfuse dashboard
2. Navigate to "Tracing" section
3. Filter by trace name "cv_optimization"
4. Click on a trace to see the complete workflow with all spans

## Future Improvements

- Add more sophisticated error recovery in agents
- Add support for more file formats (DOCX, RTF)
- Create agent-specific configuration options
- Implement agent chaining for complex workflows
- Add unit tests for agents and tools
- Implement streaming responses for better UX
- Support for custom tool creation by users
- Multi-language support for agent responses
- Enhanced Langfuse integration with custom metrics