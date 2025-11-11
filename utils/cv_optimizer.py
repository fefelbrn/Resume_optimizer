"""
CV Optimizer using OpenAI to tailor CV for specific job descriptions
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, Optional, List
import re
import json


def parse_openai_error(error: Exception) -> Dict[str, Any]:
    """
    Parse OpenAI API errors and return user-friendly messages.
    
    Args:
        error: The exception from OpenAI API
        
    Returns:
        Dictionary with error_code, error_message, and user_message
    """
    error_str = str(error)
    
    # Try to extract error information from the error string
    error_code = None
    error_message = error_str
    user_message = "Une erreur s'est produite lors de l'appel à l'API OpenAI."
    
    # Check for 401 (Invalid API Key)
    if "401" in error_str or "invalid_api_key" in error_str.lower() or "Incorrect API key" in error_str:
        error_code = 401
        user_message = (
            "Erreur: Clé API OpenAI invalide.\n\n"
            "Votre clé API n'est pas valide ou a expiré. Veuillez:\n"
            "1. Vérifier que vous avez copié la clé complète\n"
            "2. Obtenir une nouvelle clé sur: https://platform.openai.com/account/api-keys\n"
            "3. Vérifier que votre compte OpenAI a des crédits disponibles"
        )
    # Check for 429 (Rate Limit)
    elif "429" in error_str or "rate_limit" in error_str.lower():
        error_code = 429
        user_message = (
            "Erreur: Limite de taux dépassée.\n\n"
            "Vous avez fait trop de requêtes. Veuillez attendre quelques instants avant de réessayer."
        )
    # Check for 500 (Server Error)
    elif "500" in error_str or "internal_error" in error_str.lower():
        error_code = 500
        user_message = (
            "Erreur: Problème serveur OpenAI.\n\n"
            "Le serveur OpenAI rencontre des difficultés. Veuillez réessayer dans quelques instants."
        )
    # Check for insufficient credits
    elif "insufficient_quota" in error_str.lower() or "billing" in error_str.lower():
        error_code = "billing"
        user_message = (
            "Erreur: Crédits insuffisants.\n\n"
            "Votre compte OpenAI n'a plus de crédits disponibles. "
            "Veuillez ajouter des crédits sur: https://platform.openai.com/account/billing"
        )
    # Check for invalid model
    elif "model" in error_str.lower() and ("not found" in error_str.lower() or "invalid" in error_str.lower()):
        error_code = "model"
        user_message = (
            "Erreur: Modèle invalide.\n\n"
            "Le modèle sélectionné n'est pas disponible. Veuillez choisir un autre modèle."
        )
    
    return {
        "error_code": error_code,
        "error_message": error_message,
        "user_message": user_message
    }


def optimize_cv(
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
    Optimize a CV for a specific job description.
    
    Args:
        cv_text: Original CV text
        job_description: Job description text
        api_key: OpenAI API key
        model: Model to use (gpt-4o-mini, gpt-4, etc.)
        temperature: Temperature for generation
        min_experiences: Minimum number of experiences to include
        max_experiences: Maximum number of experiences to include
        max_date_years: Maximum years back to keep experiences (e.g., 5 = last 5 years)
        language: Output language code (fr, en, es)
    
    Returns:
        Dictionary with optimized_cv and metadata
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Build date filter instruction
    date_filter = ""
    if max_date_years:
        date_filter = f"\n- Only include experiences from the last {max_date_years} years (filter out older experiences)"
    
    # Build experience count instruction
    exp_filter = f"\n- Include between {min_experiences} and {max_experiences} professional experiences"
    
    # Language mapping
    language_names = {
        "fr": "French (Français)",
        "en": "English",
        "es": "Spanish (Español)"
    }
    target_language = language_names.get(language, "French (Français)")
    
    # Build system message with filters
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
- Write everything in {target_language} - section headers, descriptions, and all text"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", """Job Description:
{job_description}

Original CV:
{cv_text}

Create an optimized CV tailored to this job description. Maintain all factual information but reorganize and rephrase to maximize relevance and impact.""")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "job_description": job_description,
            "cv_text": cv_text
        })
        
        optimized_cv = response.content
        
        return {
            "optimized_cv": optimized_cv,
            "model_used": model,
            "temperature": temperature,
            "word_count": len(optimized_cv.split())
        }
    except Exception as e:
        error_info = parse_openai_error(e)
        return {
            "error": error_info["user_message"],
            "error_code": error_info["error_code"],
            "error_details": error_info["error_message"],
            "optimized_cv": None
        }

