"""
Cover Letter Generator - Creates personalized, natural-sounding cover letters
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
import re


def parse_openai_error(error: Exception) -> Dict[str, Any]:
    """Parse OpenAI API errors and return user-friendly messages."""
    error_str = str(error)
    error_code = None
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
        "error_message": error_str,
        "user_message": user_message
    }


def generate_cover_letter(
    cv_text: str,
    optimized_cv: str,
    job_description: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    target_words: int = 300,
    language: str = "fr",
) -> Dict[str, Any]:
    """Generate a personalized cover letter."""
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    target_words = round(target_words / 10) * 10
    
    language_names = {
        "fr": "French (Français)",
        "en": "English",
        "es": "Spanish (Español)"
    }
    target_language = language_names.get(language, "French (Français)")
    
    language_guidelines = {
        "fr": "- Use appropriate French business letter conventions\n- Use 'Madame, Monsieur' or 'Madame, Monsieur le Directeur' for formal openings\n- Use 'Cordialement' or 'Bien cordialement' for closings",
        "en": "- Use appropriate English business letter conventions\n- Use 'Dear [Name]' or 'Dear Hiring Manager' for openings\n- Use 'Sincerely' or 'Best regards' for closings",
        "es": "- Use appropriate Spanish business letter conventions\n- Use 'Estimado/a [Nombre]' or 'A quien corresponda' for openings\n- Use 'Atentamente' or 'Saludos cordiales' for closings"
    }
    lang_guidelines = language_guidelines.get(language, language_guidelines["fr"])
    
    system_message = f"""You are a professional writer helping someone write a cover letter. Your goal is to create a letter that sounds completely natural and human-written, NOT AI-generated.

CRITICAL: The entire cover letter must be written in {target_language}.

GUIDELINES TO AVOID AI DETECTION:
- Use varied sentence lengths
- Include personal touches
- Avoid overly formal or robotic language
- Use natural transitions
- Include specific details
- Vary your vocabulary
- Write in a warm, professional but authentic tone
{lang_guidelines}

Target length: approximately {target_words} words."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", """Job Description:
{job_description}

Candidate's Original CV:
{cv_text}

Candidate's Optimized CV (for reference):
{optimized_cv}

Write a compelling, natural-sounding cover letter in {target_language} that:
1. Shows genuine interest in this specific role and company
2. Highlights relevant experience from the CV
3. Connects the candidate's background to the job requirements
4. Sounds completely human-written (no AI patterns)
5. Is approximately {target_words} words
6. Uses appropriate business letter conventions for {target_language}

Write everything in {target_language}.""")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "job_description": job_description,
            "cv_text": cv_text,
            "optimized_cv": optimized_cv,
            "target_words": target_words,
            "target_language": target_language
        })
        
        cover_letter = response.content.strip()
        word_count = len(cover_letter.split())
        
        return {
            "cover_letter": cover_letter,
            "word_count": word_count,
            "target_words": target_words,
            "model_used": model,
            "temperature": temperature
        }
    except Exception as e:
        error_info = parse_openai_error(e)
        return {
            "error": error_info["user_message"],
            "error_code": error_info["error_code"],
            "error_details": error_info["error_message"],
            "cover_letter": None
        }

