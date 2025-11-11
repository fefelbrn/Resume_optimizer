"""
Conversational Assistant for CV adjustments
Allows users to make micro-adjustments to optimized CV and skills through natural language
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List, Optional
import json
import re
from utils.cv_optimizer import parse_openai_error


def process_assistant_request(
    user_request: str,
    original_cv: str,
    optimized_cv: str,
    job_description: str,
    cv_skills: List[str],
    job_skills: List[str],
    matched_skills: Dict[str, Any],
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    language: str = "fr"
) -> Dict[str, Any]:
    """
    Process a conversational request to adjust CV or skills.
    
    Args:
        user_request: User's natural language request
        original_cv: Original CV text
        optimized_cv: Currently optimized CV
        job_description: Job description
        cv_skills: List of CV skills
        job_skills: List of job skills
        matched_skills: Skills matching data (matched, cv_only, job_only, interesting)
        api_key: OpenAI API key
        model: Model to use
        temperature: Temperature for generation
        language: Response language
    
    Returns:
        Dictionary with updated CV/skills and explanation
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Format skills data for context
    skills_context = f"""
Compétences CV: {', '.join(cv_skills) if cv_skills else 'Aucune'}
Compétences Offre: {', '.join(job_skills) if job_skills else 'Aucune'}
Compétences correspondantes: {', '.join(matched_skills.get('matched', [])) if matched_skills.get('matched') else 'Aucune'}
Compétences manquantes: {', '.join(matched_skills.get('job_only', [])) if matched_skills.get('job_only') else 'Aucune'}
Compétences CV uniquement: {', '.join(matched_skills.get('cv_only', [])) if matched_skills.get('cv_only') else 'Aucune'}
"""
    
    # Language mapping
    language_names = {
        "fr": "French (Français)",
        "en": "English",
        "es": "Spanish (Español)"
    }
    target_language = language_names.get(language, "French (Français)")
    
    # Use format() instead of f-string to avoid issues with curly braces
    system_message = """You are a helpful assistant that helps users refine their optimized CV and correct skills detection.

Your task is to:
1. Understand the user's request (they may want to add skills, correct skill names, modify CV content, etc.)
2. Make the appropriate changes to the optimized CV or skills
3. Provide a clear explanation of what you changed

CRITICAL RULES:
- Answer in {target_language}
- If the request is about skills, return ONLY a JSON object with the updated skills
- If the request is about CV content, return the updated CV text
- Always provide an explanation of your changes
- Keep the CV format and structure intact
- Only make the specific changes requested, don't add unnecessary content
- If correcting a skill name, find the similar skill in the list and correct it

Response format (return valid JSON only):
- For skills modification: Include action field with value "update_skills", updated_skills object with cv_skills and job_skills arrays, and explanation string
- For CV modification: Include action field with value "update_cv", updated_cv string, and explanation string  
- For both: Include action field with value "update_both", updated_cv string, updated_skills object, and explanation string

The JSON should have this structure:
- action: one of "update_skills", "update_cv", or "update_both"
- updated_skills: object with cv_skills and job_skills arrays (only if action is update_skills or update_both)
- updated_cv: string with updated CV text (only if action is update_cv or update_both)
- explanation: string describing what was changed
""".format(target_language=target_language)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", """CV Original:
{original_cv}

CV Optimisé Actuel:
{optimized_cv}

Description du Poste:
{job_description}

Compétences Détectées:
{skills_context}

Demande de l'utilisateur: {user_request}

Analysez la demande et effectuez les modifications demandées. Répondez UNIQUEMENT avec un JSON valide selon le format indiqué.""")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "original_cv": original_cv,
            "optimized_cv": optimized_cv,
            "job_description": job_description,
            "skills_context": skills_context,
            "user_request": user_request
        })
        
        content = response.content.strip()
        
        # Try to extract JSON from response
        # Remove markdown code blocks if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                # Fallback: treat as CV update if it looks like CV text
                if len(content) > 200:
                    result = {
                        "action": "update_cv",
                        "updated_cv": content,
                        "explanation": "CV mis à jour selon votre demande"
                    }
                else:
                    raise ValueError("Could not parse response as JSON or CV text")
        
        # Validate and format response
        if result.get("action") == "update_skills":
            return {
                "action": "update_skills",
                "updated_skills": result.get("updated_skills", {}),
                "explanation": result.get("explanation", "Compétences mises à jour"),
                "success": True
            }
        elif result.get("action") == "update_cv":
            return {
                "action": "update_cv",
                "updated_cv": result.get("updated_cv", optimized_cv),
                "explanation": result.get("explanation", "CV mis à jour"),
                "success": True
            }
        elif result.get("action") == "update_both":
            return {
                "action": "update_both",
                "updated_cv": result.get("updated_cv", optimized_cv),
                "updated_skills": result.get("updated_skills", {}),
                "explanation": result.get("explanation", "CV et compétences mis à jour"),
                "success": True
            }
        else:
            return {
                "error": "Format de réponse invalide",
                "success": False
            }
            
    except Exception as e:
        error_info = parse_openai_error(e)
        return {
            "error": error_info["user_message"],
            "error_code": error_info["error_code"],
            "success": False
        }

