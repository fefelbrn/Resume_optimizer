"""
Skills Matcher - Extract and match skills between CV and job description
Uses the tools from tools.py
"""
from typing import Dict, Any, List
from utils.tools import extract_skills_tool, compare_skills_tool


def extract_skills(text: str, text_type: str, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.2) -> Dict[str, Any]:
    """
    Extract skills from text (CV or job description).
    
    Args:
        text: The text to analyze
        text_type: "cv" or "job"
        api_key: OpenAI API key
        model: Model to use
        temperature: Temperature for skill extraction (default 0.2)
    
    Returns:
        Dictionary with 'skills' (list) and 'count' (int)
    """
    result = extract_skills_tool.invoke({
        "text": text,
        "text_type": text_type,
        "api_key": api_key,
        "model": model,
        "temperature": temperature
    })
    
    return {
        "skills": result.get("skills", []),
        "count": result.get("count", 0),
        "status": result.get("status", "success")
    }


def match_skills(
    cv_skills: List[str],
    job_skills: List[str],
    api_key: str,
    cv_text: str = "",
    job_text: str = "",
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Match CV skills with job description skills.
    
    Args:
        cv_skills: List of skills from CV
        job_skills: List of skills from job description
        api_key: OpenAI API key
        cv_text: CV text (optional, for context)
        job_text: Job description text (optional, for context)
        model: Model to use
        temperature: Temperature for skill comparison (default 0.3)
    
    Returns:
        Dictionary with matched, cv_only, job_only, interesting, and stats
    """
    result = compare_skills_tool.invoke({
        "cv_skills": cv_skills,
        "job_skills": job_skills,
        "api_key": api_key,
        "cv_text": cv_text,
        "job_text": job_text,
        "model": model,
        "temperature": temperature
    })
    
    return result

