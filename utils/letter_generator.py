"""
Cover Letter Generator - Creates personalized, natural-sounding cover letters
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any
import re
from utils.langfuse_config import create_langfuse_callback


def parse_openai_error(error: Exception) -> Dict[str, Any]:
    """Parse OpenAI API errors and return user-friendly messages."""
    error_str = str(error)
    error_code = None
    user_message = "An error occurred while calling your OpenAI API."
    
    if "401" in error_str or "invalid_api_key" in error_str.lower() or "Incorrect API key" in error_str:
        error_code = 401
        user_message = (
            "Error: Invalid OpenAI API key.\n\n"
            "Your API key is invalid or has expired. Please:\n"
            "1. Verify that you have copied the entire key\n"
            "2. Obtain a new key at: https://platform.openai.com/account/api-keys\n"
            "3. Verify that your OpenAI account has available credits"
        )
    elif "429" in error_str or "rate_limit" in error_str.lower():
        error_code = 429
        user_message = (
            "Error: Rate limit exceeded.\n\n"
            "You have made too many requests. Please wait a few moments before trying again."
        )
    elif "insufficient_quota" in error_str.lower() or "billing" in error_str.lower():
        error_code = "billing"
        user_message = (
            "Error: Insufficient credits.\n\n"
            "Your OpenAI account has no credits left."
            "Please add credits at: https://platform.openai.com/account/billing"
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
    # Creat a Langfuse callback for the cover letter generation
    langfuse_callback = create_langfuse_callback(
        trace_name="cover_letter_generation",
        metadata={
            "model": model,
            "temperature": temperature,
            "language": language,
            "target_words": target_words
        }
    )
    
    callbacks = [langfuse_callback] if langfuse_callback else None
    
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
        callbacks=callbacks
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