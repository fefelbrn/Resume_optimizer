"""
Cover Letter Generator - Creates personalized, natural-sounding cover letters
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
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
    """
    Generate a personalized cover letter that doesn't sound AI-generated.
    
    Args:
        cv_text: Original CV text
        optimized_cv: Optimized CV text
        job_description: Job description
        api_key: OpenAI API key
        model: Model to use
        temperature: Temperature (higher = more creative/natural)
        target_words: Target word count (will be rounded to nearest 10)
        language: Output language code (fr, en, es)
    
    Returns:
        Dictionary with cover_letter and metadata
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Round to nearest 10
    target_words = round(target_words / 10) * 10
    
    # Language mapping
    language_names = {
        "fr": "French (Français)",
        "en": "English",
        "es": "Spanish (Español)"
    }
    target_language = language_names.get(language, "French (Français)")
    
    # Language-specific guidelines
    language_guidelines = {
        "fr": "- Use appropriate French business letter conventions\n- Use 'Madame, Monsieur' or 'Madame, Monsieur le Directeur' for formal openings\n- Use 'Cordialement' or 'Bien cordialement' for closings\n- Avoid anglicisms and use proper French expressions",
        "en": "- Use appropriate English business letter conventions\n- Use 'Dear [Name]' or 'Dear Hiring Manager' for openings\n- Use 'Sincerely' or 'Best regards' for closings\n- Use natural English expressions and idioms",
        "es": "- Use appropriate Spanish business letter conventions\n- Use 'Estimado/a [Nombre]' or 'A quien corresponda' for openings\n- Use 'Atentamente' or 'Saludos cordiales' for closings\n- Use natural Spanish expressions and idioms"
    }
    lang_guidelines = language_guidelines.get(language, language_guidelines["fr"])
    
    system_message = f"""You are a professional writer helping someone write a cover letter. Your goal is to create a letter that sounds completely natural and human-written, NOT AI-generated.

CRITICAL: The entire cover letter must be written in {target_language}. All content, greetings, and closings must be in this language.

CRITICAL GUIDELINES TO AVOID AI DETECTION:
- Use varied sentence lengths (mix short and long sentences)
- Include occasional conversational elements and personal touches
- Avoid overly formal or robotic language
- Use natural transitions, not formulaic connectors
- Include specific details and anecdotes when possible
- Vary your vocabulary - don't repeat the same phrases
- Write in a warm, professional but authentic tone
- Avoid clichés - be more direct and personal
- Use contractions naturally where appropriate (if culturally acceptable in {target_language})
- Include minor imperfections that make it feel human (but keep it professional)
- Don't overuse exclamation points or excessive enthusiasm
- Be specific about why THIS company and THIS role, not generic statements
{lang_guidelines}

Target length: approximately {target_words} words (±20 words is acceptable).

Structure:
- Opening: Engaging, specific hook (not generic openings)
- Body paragraphs: 2-3 paragraphs connecting experience to role
- Closing: Professional but warm sign-off appropriate for {target_language}

Make it sound like a real person wrote this in {target_language}, not an AI assistant."""
    
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

Make it personal, authentic, and engaging while remaining professional. Write everything in {target_language}.""")
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
        
        # Clean up any obvious AI artifacts
        cover_letter = clean_ai_artifacts(cover_letter)
        
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


def clean_ai_artifacts(text: str) -> str:
    """
    Remove obvious AI-generated patterns from text.
    """
    # Remove common AI phrases
    ai_phrases = [
        r"I am writing to express my (?:sincere |genuine )?interest",
        r"I am excited to (?:apply|submit my application)",
        r"Thank you for (?:considering|taking the time)",
        r"I believe I would be a (?:great|excellent|perfect) fit",
    ]
    
    for phrase in ai_phrases:
        text = re.sub(phrase, "", text, flags=re.IGNORECASE)
    
    # Remove excessive formality markers
    text = re.sub(r"\bI am confident that\b", "I'm confident", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI would like to\b", "I'd like to", text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
    
    return text.strip()

