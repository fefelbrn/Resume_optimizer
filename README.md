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
- Implements a 5-node sequential pipeline:
  1. **Analyze Structure**: Uses `analyze_cv_structure_tool` to identify CV sections
  2. **Extract CV Skills**: Uses `extract_skills_tool` to identify candidate skills
  3. **Extract Job Skills**: Uses `extract_skills_tool` to identify required job skills
  4. **Compare Skills**: Uses `compare_skills_tool` to find matches, gaps, and interesting skills
  5. **Generate Optimized CV**: Uses LLM with context from previous steps to create tailored CV

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

#### 4. Skills Matcher (`utils/skills_matcher.py`)

**What it does**: Wrapper module that provides a clean API for skill extraction and matching.

**How it works**: Uses the tools from `tools.py` to provide simplified functions for the frontend.

**Why this approach**: Provides a clean separation between the agent internals and the API layer.

### Application Flow

1. **User uploads CV and job description** → Files are parsed and text is extracted
2. **Skills are automatically extracted** → Both CV and job description skills are identified
3. **Skills are matched** → System identifies matches, gaps, and interesting skills
4. **User requests CV optimization** → CV Optimization Agent runs the 5-step workflow
5. **Optimized CV is generated** → User can review and download
6. **User can request adjustments** → Assistant Agent uses tools to make changes
7. **Conversation history is maintained** → Assistant remembers context across requests

## Technology Stack

- **Backend**: Flask (Python web framework)
- **AI Framework**: LangChain, LangGraph
- **LLM**: OpenAI GPT models (configurable)
- **PDF Processing**: PyPDF2, pdfplumber
- **PDF Generation**: ReportLab
- **Frontend**: Vanilla JavaScript, HTML, CSS

## Project Structure

```
.
├── app.py                      # Flask application and API endpoints
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # Frontend interface
├── static/
│   ├── css/
│   │   └── style.css         # Styling
│   └── js/
│       └── main.js           # Frontend logic
└── utils/
    ├── __init__.py
    ├── cv_optimizer_agent.py  # LangGraph workflow for CV optimization
    ├── assistant_agent.py     # ReAct agent for conversational assistant
    ├── tools.py               # LangChain tools (@tool decorator)
    ├── skills_matcher.py     # Skills extraction and matching API
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

### 5. No Fallbacks
We removed all fallback implementations because:
- Agents should handle errors gracefully themselves
- Fallbacks create code duplication
- They make the system harder to maintain
- They hide architectural issues

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

The application runs on port **5001** (changed from 5000 to avoid conflicts with macOS AirPlay Receiver).

All configuration is done through the web interface:
- OpenAI API key (user-provided, not stored)
- Model selection (GPT-4o-mini, GPT-4, etc.)
- Temperature settings
- Language selection (French, English, Spanish)
- CV optimization parameters (min/max experiences, date filters)

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

4. **Node 3 - Extract Job Skills**:
   - Same `extract_skills_tool` is called with `text_type="job"`
   - The job description is analyzed for required/preferred skills
   - Results stored in `state["job_skills"]`
   - Agent logs: "✓ Extracted X skills from job description"

5. **Node 4 - Compare Skills**:
   - The `compare_skills_tool` performs intelligent matching
   - It identifies: matched skills (green), missing skills (red), CV-only skills (gray), interesting skills (blue)
   - Uses fuzzy matching and AI analysis for skill relevance
   - Results stored in `state["skills_comparison"]`
   - Agent logs: "✓ Compared skills: X matches, Y missing"

6. **Node 5 - Generate Optimized CV**:
   - All previous results are compiled into context
   - An LLM prompt is constructed with:
     - Original CV
     - Job description
     - CV structure information
     - Skills analysis (matches, gaps, interesting skills)
     - Optimization parameters (min/max experiences, date filters)
   - The LLM generates a tailored CV
   - Results stored in `state["optimized_cv"]`
   - Agent logs: "✓ Generated optimized CV (X words)"

7. **Return Results**: The final state is returned with the optimized CV, all intermediate results, and agent logs.

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

## Performance Considerations

- **Caching**: Skills extraction results are cached to avoid redundant API calls
- **Debouncing**: Frontend debounces skill extraction requests (3 seconds) to reduce API usage
- **Concurrent Control**: Flags prevent multiple simultaneous extractions
- **Rate Limiting**: The system handles OpenAI rate limits gracefully with user-friendly messages
- **State Persistence**: LangGraph state is maintained throughout the workflow, avoiding redundant processing

## Security Considerations

- **API Key Handling**: User API keys are never stored, only used for the current session
- **File Upload Limits**: Maximum file size of 10MB, only PDF and TXT allowed
- **Input Validation**: All inputs are validated before processing
- **Error Messages**: Error messages don't expose sensitive information

## Future Improvements

- Add more sophisticated error recovery in agents
- Implement agent observability and logging
- Add support for more file formats (DOCX, RTF)
- Create agent-specific configuration options
- Implement agent chaining for complex workflows
- Add unit tests for agents and tools
- Implement streaming responses for better UX
- Add agent performance metrics and monitoring
- Support for custom tool creation by users
- Multi-language support for agent responses