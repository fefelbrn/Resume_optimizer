"""
CV Optimization Agent using LangGraph
Uses a multi-step workflow with tools to optimize CVs
"""
from typing import Dict, Any, List, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from utils.tools import (
    analyze_cv_structure_tool,
    extract_skills_tool,
    compare_skills_tool,
    compare_skills_tool_with_rag
)
from utils.rag_system import RAGSystem


class CVOptimizationState(TypedDict):
    """State for the CV optimization agent"""
    cv_text: str
    job_description: str
    api_key: str
    model: str
    temperature: float
    language: str
    min_experiences: int
    max_experiences: int
    max_date_years: Optional[int]
    
    # Intermediate results
    cv_structure: Optional[Dict[str, Any]]
    cv_skills: List[str]
    job_skills: List[str]
    skills_comparison: Optional[Dict[str, Any]]
    
    # RAG components
    rag_system: Optional[Any]  # RAGSystem instance
    
    # Final result
    optimized_cv: Optional[str]
    sources: Optional[Dict[str, List[str]]]  # Sources used for generation
    rag_details: Optional[Dict[str, Any]]  # NEW: Detailed RAG information for logging
    error: Optional[str]
    agent_logs: List[str]


def analyze_structure(state: CVOptimizationState) -> CVOptimizationState:
    """Node 1: Analyze CV structure"""
    try:
        result = analyze_cv_structure_tool.invoke({"cv_text": state["cv_text"]})
        state["cv_structure"] = result
        state["agent_logs"].append(f"✓ Analyzed CV structure: Found {result.get('section_count', 0)} sections")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error analyzing CV structure: {str(e)}")
        state["error"] = str(e)
        return state


def extract_cv_skills(state: CVOptimizationState) -> CVOptimizationState:
    """Node 2: Extract skills from CV"""
    try:
        result = extract_skills_tool.invoke({
            "text": state["cv_text"],
            "text_type": "cv",
            "api_key": state["api_key"],
            "model": state["model"]
        })
        state["cv_skills"] = result.get("skills", [])
        state["agent_logs"].append(f"✓ Extracted {len(state['cv_skills'])} skills from CV")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error extracting CV skills: {str(e)}")
        state["error"] = str(e)
        return state


def extract_job_skills(state: CVOptimizationState) -> CVOptimizationState:
    """Node 3: Extract skills from job description"""
    try:
        result = extract_skills_tool.invoke({
            "text": state["job_description"],
            "text_type": "job",
            "api_key": state["api_key"],
            "model": state["model"]
        })
        state["job_skills"] = result.get("skills", [])
        state["agent_logs"].append(f"✓ Extracted {len(state['job_skills'])} skills from job description")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error extracting job skills: {str(e)}")
        state["error"] = str(e)
        return state


def index_cv_in_rag(state: CVOptimizationState) -> CVOptimizationState:
    """Node 2.5: Index CV in vector database"""
    try:
        if state.get("rag_system"):
            indexing_info = state["rag_system"].index_cv(state["cv_text"], session_id="cv")
            state["agent_logs"].append(f"✓ Indexed CV in vector database: {indexing_info['chunks_count']} chunks")
            # Store indexing info for detailed logs
            if not state.get("rag_details"):
                state["rag_details"] = {}
            state["rag_details"]["cv_indexing"] = indexing_info
        else:
            state["agent_logs"].append("⚠ RAG system not available, skipping CV indexing")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error indexing CV in RAG: {str(e)}")
        # Don't fail the workflow, just log the error
        return state


def index_jd_in_rag(state: CVOptimizationState) -> CVOptimizationState:
    """Node 3.5: Index Job Description in vector database"""
    try:
        if state.get("rag_system"):
            indexing_info = state["rag_system"].index_jd(state["job_description"], session_id="jd")
            state["agent_logs"].append(f"✓ Indexed job description in vector database: {indexing_info['chunks_count']} chunks")
            # Store indexing info for detailed logs
            if not state.get("rag_details"):
                state["rag_details"] = {}
            state["rag_details"]["jd_indexing"] = indexing_info
        else:
            state["agent_logs"].append("⚠ RAG system not available, skipping JD indexing")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error indexing JD in RAG: {str(e)}")
        # Don't fail the workflow, just log the error
        return state


def compare_skills(state: CVOptimizationState) -> CVOptimizationState:
    """Node 4: Compare CV skills with job skills using RAG + cosine similarity"""
    try:
        rag_system = state.get("rag_system")
        cv_vectorstore = rag_system.cv_vectorstore if rag_system else None
        jd_vectorstore = rag_system.jd_vectorstore if rag_system else None
        
        # Use RAG-based comparison if available, fallback to original
        if rag_system and cv_vectorstore and jd_vectorstore:
            result = compare_skills_tool_with_rag.invoke({
                "cv_skills": state["cv_skills"],
                "job_skills": state["job_skills"],
                "api_key": state["api_key"],
                "cv_vectorstore": cv_vectorstore,
                "jd_vectorstore": jd_vectorstore,
                "similarity_threshold": 0.7
            })
            state["agent_logs"].append("✓ Compared skills using RAG + cosine similarity")
        else:
            # Fallback to original method
            result = compare_skills_tool.invoke({
                "cv_skills": state["cv_skills"],
                "job_skills": state["job_skills"],
                "api_key": state["api_key"],
                "cv_text": state["cv_text"],
                "job_text": state["job_description"],
                "model": state["model"]
            })
            state["agent_logs"].append("✓ Compared skills using traditional method")
        
        state["skills_comparison"] = result
        matched_count = len(result.get("matched", []))
        missing_count = len(result.get("job_only", []))
        state["agent_logs"].append(f"✓ Compared skills: {matched_count} matches, {missing_count} missing")
        return state
    except Exception as e:
        state["agent_logs"].append(f"✗ Error comparing skills: {str(e)}")
        state["error"] = str(e)
        return state


def generate_optimized_cv(state: CVOptimizationState) -> CVOptimizationState:
    """Node 5: Generate optimized CV using LLM with RAG retrieval"""
    try:
        llm = ChatOpenAI(
            model=state["model"],
            temperature=state["temperature"],
            api_key=state["api_key"]
        )
        
        # Build context from previous steps
        cv_structure_info = ""
        if state.get("cv_structure"):
            sections = state["cv_structure"].get("sections", [])
            cv_structure_info = f"CV Structure: {', '.join(sections)}\n"
        
        skills_info = ""
        if state.get("skills_comparison"):
            comp = state["skills_comparison"]
            matched = comp.get("matched", [])
            missing = comp.get("job_only", [])
            skills_info = f"""
Skills Analysis:
- Matching skills: {', '.join(matched[:10]) if matched else 'None'}
- Missing skills: {', '.join(missing[:10]) if missing else 'None'}
"""
        
        date_filter = ""
        if state.get("max_date_years"):
            date_filter = f"\n- Only include experiences from the last {state['max_date_years']} years"
        
        exp_filter = f"\n- Include between {state['min_experiences']} and {state['max_experiences']} professional experiences"
        
        language_names = {
            "fr": "French (Français)",
            "en": "English",
            "es": "Spanish (Español)"
        }
        target_language = language_names.get(state["language"], "French (Français)")
        
        # RAG retrieval if available
        rag_context = ""
        cv_sources = []
        jd_sources = []
        
        rag_system = state.get("rag_system")
        if rag_system:
            try:
                # Retrieve relevant chunks using job description as query
                rag_result = rag_system.get_context_with_sources(
                    query=state["job_description"],
                    k_cv=5,
                    k_jd=3
                )
                
                cv_context = rag_result.get("cv_context", "")
                jd_context = rag_result.get("jd_context", "")
                cv_sources = rag_result.get("cv_sources", [])
                jd_sources = rag_result.get("jd_sources", [])
                
                if cv_context or jd_context:
                    rag_context = f"""
Relevant CV sections (from semantic search):
{cv_context}

Relevant job requirements (from semantic search):
{jd_context}

IMPORTANT: Use information from the chunks above. These are the most relevant parts of the CV and job description for this optimization.
"""
                    state["agent_logs"].append(f"✓ Retrieved {len(cv_sources)} CV chunks and {len(jd_sources)} JD chunks using RAG")
                    
                    # Store detailed RAG info for logging
                    if not state.get("rag_details"):
                        state["rag_details"] = {}
                    state["rag_details"]["retrieval"] = {
                        "query": rag_result.get("query", state["job_description"]),
                        "cv_chunks_details": rag_result.get("cv_chunks_details", []),
                        "jd_chunks_details": rag_result.get("jd_chunks_details", []),
                        "k_cv": 5,
                        "k_jd": 3
                    }
            except Exception as e:
                state["agent_logs"].append(f"⚠ RAG retrieval failed: {str(e)}, using full text")
                rag_context = ""
        
        system_message = f"""You are an expert CV/resume optimizer. Your task is to tailor a candidate's CV to match a specific job description while maintaining authenticity and truthfulness.

CRITICAL: The entire CV must be written in {target_language}. All sections, descriptions, and content must be in this language.

Guidelines:
- Keep all information factual and accurate
- Reorganize and rephrase content to highlight relevant skills and experiences
- Use action verbs and quantify achievements where possible
- Maintain professional formatting with clear sections
- Ensure ATS (Applicant Tracking System) compatibility
- Keep the same structure: Header, Summary, Experience, Education, Skills, etc.{date_filter}{exp_filter}
- Focus on experiences and skills most relevant to the job
- Remove or de-emphasize irrelevant information
- Use industry-standard terminology from the job description where appropriate
- Write everything in {target_language} - section headers, descriptions, and all text
- When RAG context is provided, prioritize information from those chunks as they are the most relevant

Use the skills analysis to emphasize matching skills and address missing skills naturally in the content."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """{rag_context}
Job Description:
{job_description}

Original CV:
{cv_text}

{cv_structure_info}
{skills_info}

Create an optimized CV tailored to this job description. Maintain all factual information but reorganize and rephrase to maximize relevance and impact. If RAG context is provided, use it as the primary source of information.""")
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({
            "rag_context": rag_context,
            "job_description": state["job_description"],
            "cv_text": state["cv_text"],
            "cv_structure_info": cv_structure_info,
            "skills_info": skills_info
        })
        
        state["optimized_cv"] = response.content.strip()
        state["sources"] = {
            "cv_sources": cv_sources,
            "jd_sources": jd_sources
        }
        state["agent_logs"].append(f"✓ Generated optimized CV ({len(state['optimized_cv'].split())} words) with RAG context")
        return state
        
    except Exception as e:
        state["agent_logs"].append(f"✗ Error generating CV: {str(e)}")
        state["error"] = str(e)
        return state


def create_cv_optimization_agent() -> StateGraph:
    """Create the LangGraph workflow for CV optimization with RAG"""
    workflow = StateGraph(CVOptimizationState)
    
    # Add nodes
    workflow.add_node("analyze_structure", analyze_structure)
    workflow.add_node("extract_cv_skills", extract_cv_skills)
    workflow.add_node("index_cv_rag", index_cv_in_rag)  # NEW: Index CV in RAG
    workflow.add_node("extract_job_skills", extract_job_skills)
    workflow.add_node("index_jd_rag", index_jd_in_rag)  # NEW: Index JD in RAG
    workflow.add_node("compare_skills", compare_skills)
    workflow.add_node("generate_cv", generate_optimized_cv)
    
    # Set entry point
    workflow.set_entry_point("analyze_structure")
    
    # Add edges (sequential workflow with RAG nodes)
    workflow.add_edge("analyze_structure", "extract_cv_skills")
    workflow.add_edge("extract_cv_skills", "index_cv_rag")  # NEW: After CV skills extraction
    workflow.add_edge("index_cv_rag", "extract_job_skills")
    workflow.add_edge("extract_job_skills", "index_jd_rag")  # NEW: After JD skills extraction
    workflow.add_edge("index_jd_rag", "compare_skills")
    workflow.add_edge("compare_skills", "generate_cv")
    workflow.add_edge("generate_cv", END)
    
    return workflow.compile()


def optimize_cv_with_agent(
    cv_text: str,
    job_description: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    min_experiences: int = 3,
    max_experiences: int = 8,
    max_date_years: Optional[int] = None,
    language: str = "fr",
    rag_system: Optional[Any] = None,  # NEW: RAG system parameter
) -> Dict[str, Any]:
    """
    Optimize CV using the agent-based workflow.
    
    Returns:
        Dictionary with optimized_cv, agent_logs, and metadata
    """
    initial_state: CVOptimizationState = {
        "cv_text": cv_text,
        "job_description": job_description,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "language": language,
        "min_experiences": min_experiences,
        "max_experiences": max_experiences,
        "max_date_years": max_date_years,
        "cv_structure": None,
        "cv_skills": [],
        "job_skills": [],
        "skills_comparison": None,
        "rag_system": rag_system,  # NEW: Include RAG system in state
        "optimized_cv": None,
        "sources": None,  # NEW: Sources will be populated by generate_optimized_cv
        "rag_details": None,  # NEW: Detailed RAG information
        "error": None,
        "agent_logs": []
    }
    
    agent = create_cv_optimization_agent()
    
    try:
        final_state = agent.invoke(initial_state)
        
        if final_state.get("error"):
            return {
                "error": final_state["error"],
                "optimized_cv": None,
                "agent_logs": final_state.get("agent_logs", [])
            }
        
        # Build graph structure information
        graph_structure = {
            "nodes": [
                {
                    "id": "analyze_structure",
                    "name": "Analyze Structure",
                    "description": "Analyzes CV structure and identifies sections",
                    "tools": ["analyze_cv_structure_tool"]
                },
                {
                    "id": "extract_cv_skills",
                    "name": "Extract CV Skills",
                    "description": "Extracts skills from the CV text",
                    "tools": ["extract_skills_tool"]
                },
                {
                    "id": "index_cv_rag",
                    "name": "Index CV in RAG",
                    "description": "Indexes CV chunks in vector database",
                    "tools": []
                },
                {
                    "id": "extract_job_skills",
                    "name": "Extract Job Skills",
                    "description": "Extracts required skills from job description",
                    "tools": ["extract_skills_tool"]
                },
                {
                    "id": "index_jd_rag",
                    "name": "Index JD in RAG",
                    "description": "Indexes job description chunks in vector database",
                    "tools": []
                },
                {
                    "id": "compare_skills",
                    "name": "Compare Skills",
                    "description": "Compares CV and job skills, identifies matches and gaps",
                    "tools": ["compare_skills_tool", "compare_skills_tool_with_rag"]
                },
                {
                    "id": "generate_cv",
                    "name": "Generate Optimized CV",
                    "description": "Generates the final optimized CV using LLM",
                    "tools": []
                }
            ],
            "edges": [
                {"from": "analyze_structure", "to": "extract_cv_skills"},
                {"from": "extract_cv_skills", "to": "index_cv_rag"},
                {"from": "index_cv_rag", "to": "extract_job_skills"},
                {"from": "extract_job_skills", "to": "index_jd_rag"},
                {"from": "index_jd_rag", "to": "compare_skills"},
                {"from": "compare_skills", "to": "generate_cv"}
            ],
            "execution_order": ["analyze_structure", "extract_cv_skills", "index_cv_rag", "extract_job_skills", "index_jd_rag", "compare_skills", "generate_cv"]
        }
        
        return {
            "optimized_cv": final_state.get("optimized_cv"),
            "agent_logs": final_state.get("agent_logs", []),
            "cv_skills": final_state.get("cv_skills", []),
            "job_skills": final_state.get("job_skills", []),
            "skills_comparison": final_state.get("skills_comparison"),
            "sources": final_state.get("sources"),  # NEW: Return sources
            "rag_details": final_state.get("rag_details"),  # NEW: Return detailed RAG info
            "graph_structure": graph_structure,  # NEW: Return graph structure
            "model_used": model,
            "temperature": temperature,
            "word_count": len(final_state.get("optimized_cv", "").split()) if final_state.get("optimized_cv") else 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "optimized_cv": None,
            "agent_logs": ["✗ Agent execution failed"]
        }

