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
    compare_skills_tool
)


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
    
    # Final result
    optimized_cv: Optional[str]
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


def compare_skills(state: CVOptimizationState) -> CVOptimizationState:
    """Node 4: Compare CV skills with job skills"""
    try:
        result = compare_skills_tool.invoke({
            "cv_skills": state["cv_skills"],
            "job_skills": state["job_skills"],
            "api_key": state["api_key"],
            "cv_text": state["cv_text"],
            "job_text": state["job_description"],
            "model": state["model"]
        })
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
    """Node 5: Generate optimized CV using LLM"""
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

Use the skills analysis to emphasize matching skills and address missing skills naturally in the content."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Job Description:
{job_description}

Original CV:
{cv_text}

{cv_structure_info}
{skills_info}

Create an optimized CV tailored to this job description. Maintain all factual information but reorganize and rephrase to maximize relevance and impact.""")
        ])
        
        chain = prompt | llm
        
        response = chain.invoke({
            "job_description": state["job_description"],
            "cv_text": state["cv_text"],
            "cv_structure_info": cv_structure_info,
            "skills_info": skills_info
        })
        
        state["optimized_cv"] = response.content.strip()
        state["agent_logs"].append(f"✓ Generated optimized CV ({len(state['optimized_cv'].split())} words)")
        return state
        
    except Exception as e:
        state["agent_logs"].append(f"✗ Error generating CV: {str(e)}")
        state["error"] = str(e)
        return state


def create_cv_optimization_agent() -> StateGraph:
    """Create the LangGraph workflow for CV optimization"""
    workflow = StateGraph(CVOptimizationState)
    
    # Add nodes
    workflow.add_node("analyze_structure", analyze_structure)
    workflow.add_node("extract_cv_skills", extract_cv_skills)
    workflow.add_node("extract_job_skills", extract_job_skills)
    workflow.add_node("compare_skills", compare_skills)
    workflow.add_node("generate_cv", generate_optimized_cv)
    
    # Set entry point
    workflow.set_entry_point("analyze_structure")
    
    # Add edges (sequential workflow)
    workflow.add_edge("analyze_structure", "extract_cv_skills")
    workflow.add_edge("extract_cv_skills", "extract_job_skills")
    workflow.add_edge("extract_job_skills", "compare_skills")
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
        "optimized_cv": None,
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
        
        return {
            "optimized_cv": final_state.get("optimized_cv"),
            "agent_logs": final_state.get("agent_logs", []),
            "cv_skills": final_state.get("cv_skills", []),
            "job_skills": final_state.get("job_skills", []),
            "skills_comparison": final_state.get("skills_comparison"),
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

