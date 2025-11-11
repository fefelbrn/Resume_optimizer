"""
Skills Matcher - Extracts and matches skills between CV and job description
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List
import json
import re


def parse_openai_error(error: Exception) -> Dict[str, Any]:
    """
    Parse OpenAI API errors and return user-friendly messages.
    """
    error_str = str(error)
    
    error_code = None
    error_message = error_str
    user_message = "Une erreur s'est produite lors de l'appel à l'API OpenAI."
    
    if "401" in error_str or "invalid_api_key" in error_str.lower() or "Incorrect API key" in error_str:
        error_code = 401
        user_message = (
            "Erreur: Clé API OpenAI invalide.\n\n"
            "Votre clé API n'est pas valide ou a expiré. Veuillez:\n"
            "1. Vérifier que vous avez copié la clé complète\n"
            "2. Obtenir une nouvelle clé sur: https://platform.openai.com/account/api-keys\n"
            "3. Vérifier que votre compte OpenAI a des crédits disponibles"
        )
    elif "429" in error_str or "rate_limit" in error_str.lower():
        error_code = 429
        user_message = (
            "Erreur: Limite de taux dépassée.\n\n"
            "Vous avez fait trop de requêtes. Veuillez attendre quelques instants avant de réessayer."
        )
    elif "insufficient_quota" in error_str.lower() or "billing" in error_str.lower():
        error_code = "billing"
        user_message = (
            "Erreur: Crédits insuffisants.\n\n"
            "Votre compte OpenAI n'a plus de crédits disponibles. "
            "Veuillez ajouter des crédits sur: https://platform.openai.com/account/billing"
        )
    
    return {
        "error_code": error_code,
        "error_message": error_message,
        "user_message": user_message
    }


def extract_skills(text: str, api_key: str, text_type: str = "cv", model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Extract skills from CV or job description.
    
    Args:
        text: CV or job description text
        api_key: OpenAI API key
        text_type: "cv" or "job"
        model: Model to use
    
    Returns:
        Dictionary with skills list and metadata
    """
    llm = ChatOpenAI(
        model=model,
        temperature=0.2,
        api_key=api_key
    )
    
    if text_type == "cv":
        system_message = """You are an expert at analyzing CVs and resumes. Extract the main skills, competencies, and technical abilities from the CV.

Return ONLY a JSON array of skills, nothing else. Each skill should be a short, clear term (2-4 words max).
Focus on:
- Technical skills (programming languages, tools, software)
- Soft skills (communication, leadership, etc.)
- Domain expertise (marketing, finance, etc.)
- Certifications and qualifications
- Languages

Format: ["skill1", "skill2", "skill3", ...]"""
        
        prompt_text = f"""Extract all the main skills and competencies from this CV:

{text}

Return a JSON array of skills only, no explanations."""
    else:
        system_message = """You are an expert at analyzing job descriptions. Extract the required and preferred skills, competencies, and qualifications from the job description.

Return ONLY a JSON array of skills, nothing else. Each skill should be a short, clear term (2-4 words max).
Focus on:
- Required technical skills
- Preferred technical skills
- Soft skills mentioned
- Domain expertise required
- Certifications or qualifications needed
- Language requirements

Format: ["skill1", "skill2", "skill3", ...]"""
        
        prompt_text = f"""Extract all the required and preferred skills from this job description:

{text}

Return a JSON array of skills only, no explanations."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", prompt_text)
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        content = response.content.strip()
        
        # Try to extract JSON array from response
        # Remove markdown code blocks if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        # Try to parse as JSON
        try:
            skills = json.loads(content)
            if not isinstance(skills, list):
                skills = [skills]
        except json.JSONDecodeError:
            # Try to extract array from text
            match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if match:
                # Try to parse the array content
                array_content = match.group(1)
                skills = [s.strip().strip('"\'') for s in array_content.split(',')]
                skills = [s for s in skills if s]
            else:
                # Fallback: split by lines or commas
                skills = [s.strip().strip('"\'') for s in content.replace('\n', ',').split(',')]
                skills = [s for s in skills if s and len(s) > 1]
        
        # Clean and normalize skills
        skills = [skill.strip() for skill in skills if skill and len(skill.strip()) > 1]
        skills = list(set(skills))  # Remove duplicates
        skills = sorted(skills)  # Sort alphabetically
        
        return {
            "skills": skills,
            "count": len(skills),
            "text_type": text_type
        }
    except Exception as e:
        error_info = parse_openai_error(e)
        return {
            "error": error_info["user_message"],
            "error_code": error_info["error_code"],
            "skills": [],
            "count": 0
        }


def match_skills(cv_skills: List[str], job_skills: List[str], cv_text: str = "", job_text: str = "", api_key: str = "", model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Match skills between CV and job description.
    
    Args:
        cv_skills: List of skills from CV
        job_skills: List of skills from job description
    
    Returns:
        Dictionary with categorized skills
    """
    # Normalize skills for comparison (lowercase, remove extra spaces)
    cv_normalized = {skill.lower().strip(): skill for skill in cv_skills}
    job_normalized = {skill.lower().strip(): skill for skill in job_skills}
    
    # Find matches (skills in both)
    matched = []
    cv_only = []
    job_only = []
    
    # Check for matches (exact or partial)
    for cv_key, cv_original in cv_normalized.items():
        found_match = False
        for job_key, job_original in job_normalized.items():
            # Exact match
            if cv_key == job_key:
                matched.append({
                    "cv_skill": cv_original,
                    "job_skill": job_original,
                    "match_type": "exact"
                })
                found_match = True
                break
            # Partial match (one contains the other)
            elif cv_key in job_key or job_key in cv_key:
                matched.append({
                    "cv_skill": cv_original,
                    "job_skill": job_original,
                    "match_type": "partial"
                })
                found_match = True
                break
        
        if not found_match:
            cv_only.append(cv_original)
    
    # Find job skills not in CV
    for job_key, job_original in job_normalized.items():
        found_in_cv = False
        for cv_key in cv_normalized.keys():
            if cv_key == job_key or cv_key in job_key or job_key in cv_key:
                found_in_cv = True
                break
        if not found_in_cv:
            job_only.append(job_original)
    
    # Skills in CV that might be interesting for the job (not in job description)
    # Use AI to identify which CV-only skills are relevant for the job
    interesting = []
    if cv_only and api_key and cv_text and job_text:
        try:
            llm = ChatOpenAI(
                model=model,
                temperature=0.3,
                api_key=api_key
            )
            
            prompt_text = f"""Analyze which CV skills from the list below would be valuable or interesting for this job, even though they are not explicitly mentioned in the job description.

Job Description (excerpt):
{job_text[:1000]}

CV Skills that are NOT in the job description:
{', '.join(cv_only[:20])}

Return ONLY a JSON array of skills from the list above that would be valuable for this job. Return an empty array [] if none are relevant.

Format: ["skill1", "skill2", ...]"""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert at matching candidate skills to job requirements. Identify skills that would add value even if not explicitly required."),
                ("human", prompt_text)
            ])
            
            chain = prompt | llm
            response = chain.invoke({})
            content = response.content.strip()
            
            # Parse JSON response
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            content = content.strip()
            
            try:
                interesting_parsed = json.loads(content)
                if isinstance(interesting_parsed, list):
                    # Normalize to match original skill names
                    interesting_normalized = [s.lower().strip() for s in interesting_parsed]
                    for skill in cv_only:
                        if skill.lower().strip() in interesting_normalized:
                            interesting.append(skill)
            except json.JSONDecodeError:
                # Fallback: use all CV-only skills
                interesting = cv_only.copy()
        except Exception:
            # If AI analysis fails, use all CV-only skills as fallback
            interesting = cv_only.copy()
    else:
        # If no API key or context, consider all CV-only skills as potentially interesting
        interesting = cv_only.copy()
    
    return {
        "matched": [m["cv_skill"] for m in matched],  # Green: skills in both
        "cv_only": [s for s in cv_only if s not in interesting],  # Gray: only in CV (not interesting)
        "job_only": job_only,  # Red: only in job (missing)
        "interesting": interesting,  # Blue: CV skills interesting but not in job
        "stats": {
            "total_cv": len(cv_skills),
            "total_job": len(job_skills),
            "matched_count": len(matched),
            "missing_count": len(job_only),
            "cv_only_count": len([s for s in cv_only if s not in interesting]),
            "interesting_count": len(interesting),
            "match_percentage": round((len(matched) / len(job_skills) * 100) if job_skills else 0, 1)
        }
    }

