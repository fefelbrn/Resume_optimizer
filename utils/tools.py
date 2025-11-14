"""
Tools for the agents - Functions that can be called by agents
"""
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional
import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


@tool
def extract_skills_tool(text: str, text_type: str, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.2) -> Dict[str, Any]:
    """
    Extract skills from a CV or job description text.
    
    Args:
        text: The text to analyze (CV or job description)
        text_type: Either "cv" or "job" to specify the type
        api_key: OpenAI API key
        model: Model to use
        temperature: Temperature for skill extraction (0.0-2.0, default 0.2 for precision)
    
    Returns:
        Dictionary with 'skills' (list of strings) and 'count' (number of skills)
    """
    try:
        llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
        
        if text_type == "cv":
            system_message = """You are an expert at analyzing CVs. Extract the main skills, competencies, and technical abilities from the CV.

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
        response = chain.invoke({})
        content = response.content.strip()
        
        # Parse JSON
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()
        
        try:
            skills = json.loads(content)
            if not isinstance(skills, list):
                skills = [skills]
        except json.JSONDecodeError:
            match = re.search(r'\[(.*?)\]', content, re.DOTALL)
            if match:
                array_content = match.group(1)
                skills = [s.strip().strip('"\'') for s in array_content.split(',')]
                skills = [s for s in skills if s]
            else:
                skills = [s.strip().strip('"\'') for s in content.replace('\n', ',').split(',')]
                skills = [s for s in skills if s and len(s) > 1]
        
        skills = [skill.strip() for skill in skills if skill and len(skill.strip()) > 1]
        skills = list(set(skills))
        skills = sorted(skills)
        
        return {
            "skills": skills,
            "count": len(skills),
            "status": "success"
        }
    except Exception as e:
        return {
            "skills": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }


@tool
def compare_skills_tool(cv_skills: List[str], job_skills: List[str], api_key: str, cv_text: str = "", job_text: str = "", model: str = "gpt-4o-mini", temperature: float = 0.3) -> Dict[str, Any]:
    """
    Compare CV skills with job description skills to find matches, missing skills, and CV-only skills.
    
    Args:
        cv_skills: List of skills from the CV
        job_skills: List of skills from the job description
        api_key: OpenAI API key
        cv_text: CV text (optional, for context)
        job_text: Job description text (optional, for context)
        model: Model to use
        temperature: Temperature for skill comparison (0.0-2.0, default 0.3 for balanced analysis)
    
    Returns:
        Dictionary with 'matched' (matching skills), 'job_only' (missing skills), 
        'cv_only' (CV-only skills), and 'interesting' (interesting CV skills)
    """
    try:
        # Normalize skills for comparison
        cv_normalized = {skill.lower().strip(): skill for skill in cv_skills}
        job_normalized = {skill.lower().strip(): skill for skill in job_skills}
        
        matched = []
        cv_only = []
        job_only = []
        
        # Find matches
        for cv_key, cv_original in cv_normalized.items():
            found_match = False
            for job_key, job_original in job_normalized.items():
                if cv_key == job_key or cv_key in job_key or job_key in cv_key:
                    matched.append({
                        "cv_skill": cv_original,
                        "job_skill": job_original,
                        "match_type": "exact" if cv_key == job_key else "partial"
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
        
        # Use AI to identify interesting CV skills
        interesting = []
        if cv_only and api_key and cv_text and job_text:
            try:
                llm = ChatOpenAI(
                    model=model,
                    temperature=temperature,
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
                
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                content = content.strip()
                
                try:
                    interesting_parsed = json.loads(content)
                    if isinstance(interesting_parsed, list):
                        interesting_normalized = [s.lower().strip() for s in interesting_parsed]
                        for skill in cv_only:
                            if skill.lower().strip() in interesting_normalized:
                                interesting.append(skill)
                except json.JSONDecodeError:
                    interesting = cv_only.copy()
            except Exception:
                interesting = cv_only.copy()
        else:
            interesting = cv_only.copy()
        
        return {
            "matched": [m["cv_skill"] for m in matched],
            "cv_only": [s for s in cv_only if s not in interesting],
            "job_only": job_only,
            "interesting": interesting,
            "stats": {
                "total_cv": len(cv_skills),
                "total_job": len(job_skills),
                "matched_count": len(matched),
                "missing_count": len(job_only),
                "cv_only_count": len([s for s in cv_only if s not in interesting]),
                "interesting_count": len(interesting),
                "match_percentage": round((len(matched) / len(job_skills) * 100) if job_skills else 0, 1)
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "matched": [],
            "cv_only": [],
            "job_only": [],
            "interesting": [],
            "stats": {},
            "status": "error",
            "error": str(e)
        }


@tool
def compare_skills_tool_with_rag(
    cv_skills: List[str], 
    job_skills: List[str], 
    api_key: str,
    cv_vectorstore: Optional[Any] = None,
    jd_vectorstore: Optional[Any] = None,
    similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Compare CV skills with job description skills using RAG and cosine similarity.
    Uses embeddings and semantic search for more accurate matching.
    
    Args:
        cv_skills: List of skills from the CV
        job_skills: List of skills from the job description
        api_key: OpenAI API key for embeddings
        cv_vectorstore: Optional CV vector store for semantic search
        jd_vectorstore: Optional JD vector store for semantic search
        similarity_threshold: Threshold for cosine similarity (default 0.7)
    
    Returns:
        Dictionary with 'matched' (matching skills with similarity scores), 
        'job_only' (missing skills), 'cv_only' (CV-only skills), 
        and 'interesting' (interesting CV skills)
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )
        
        # Vectorize skills
        if not cv_skills or not job_skills:
            return {
                "matched": [],
                "cv_only": cv_skills.copy() if cv_skills else [],
                "job_only": job_skills.copy() if job_skills else [],
                "interesting": [],
                "stats": {},
                "status": "error",
                "error": "Empty skills list"
            }
        
        # Generate embeddings for skills
        cv_skill_vectors = embeddings.embed_documents(cv_skills)
        jd_skill_vectors = embeddings.embed_documents(job_skills)
        
        # Convert to numpy arrays
        cv_vectors = np.array(cv_skill_vectors)
        jd_vectors = np.array(jd_skill_vectors)
        
        # Calculate cosine similarity matrix
        similarity_matrix = cosine_similarity(cv_vectors, jd_vectors)
        
        # Find matches above threshold
        matched = []
        matched_cv_indices = set()
        matched_jd_indices = set()
        
        for i, cv_skill in enumerate(cv_skills):
            for j, jd_skill in enumerate(job_skills):
                similarity = float(similarity_matrix[i][j])
                if similarity >= similarity_threshold:
                    matched.append({
                        "cv_skill": cv_skill,
                        "job_skill": jd_skill,
                        "similarity": round(similarity, 3),
                        "match_type": "semantic"
                    })
                    matched_cv_indices.add(i)
                    matched_jd_indices.add(j)
        
        # Find CV-only skills (not matched)
        cv_only = [
            cv_skills[i] for i in range(len(cv_skills)) 
            if i not in matched_cv_indices
        ]
        
        # Find job-only skills (missing from CV)
        # Use semantic search in CV vectorstore if available
        job_only = []
        if cv_vectorstore:
            for j, jd_skill in enumerate(job_skills):
                if j not in matched_jd_indices:
                    # Search in CV vectorstore
                    results = cv_vectorstore.similarity_search_with_score(jd_skill, k=1)
                    if not results or results[0][1] < similarity_threshold:
                        job_only.append(jd_skill)
        else:
            # Fallback: skills not matched
            job_only = [
                job_skills[j] for j in range(len(job_skills))
                if j not in matched_jd_indices
            ]
        
        # Identify interesting CV skills using semantic search in JD vectorstore
        interesting = []
        if cv_only and jd_vectorstore:
            for cv_skill in cv_only[:20]:  # Limit to avoid too many API calls
                results = jd_vectorstore.similarity_search_with_score(cv_skill, k=1)
                if results and results[0][1] >= similarity_threshold:
                    interesting.append(cv_skill)
        
        return {
            "matched": [m["cv_skill"] for m in matched],
            "matched_details": matched,  # Includes similarity scores
            "cv_only": [s for s in cv_only if s not in interesting],
            "job_only": job_only,
            "interesting": interesting,
            "stats": {
                "total_cv": len(cv_skills),
                "total_job": len(job_skills),
                "matched_count": len(matched),
                "missing_count": len(job_only),
                "cv_only_count": len([s for s in cv_only if s not in interesting]),
                "interesting_count": len(interesting),
                "match_percentage": round((len(matched) / len(job_skills) * 100) if job_skills else 0, 1),
                "avg_similarity": round(np.mean([m["similarity"] for m in matched]), 3) if matched else 0.0
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "matched": [],
            "matched_details": [],
            "cv_only": [],
            "job_only": [],
            "interesting": [],
            "stats": {},
            "status": "error",
            "error": str(e)
        }


@tool
def analyze_cv_structure_tool(cv_text: str) -> Dict[str, Any]:
    """
    Analyze the structure of a CV to identify sections and their content.
    
    Args:
        cv_text: The CV text to analyze
    
    Returns:
        Dictionary with 'sections' (list of section names), 'has_experience' (bool),
        'has_education' (bool), 'has_skills' (bool), and 'section_count' (number)
    """
    sections = []
    has_experience = False
    has_education = False
    has_skills = False
    
    section_patterns = {
        "experience": ["experience", "work experience", "professional experience", "employment", "career"],
        "education": ["education", "academic", "qualifications", "degrees"],
        "skills": ["skills", "competencies", "technical skills", "abilities"],
        "summary": ["summary", "profile", "objective", "about"],
        "projects": ["projects", "portfolio", "work samples"],
        "certifications": ["certifications", "certificates", "credentials"],
        "languages": ["languages", "language skills"]
    }
    
    lines = cv_text.split('\n')
    for line in lines:
        line_lower = line.lower().strip()
        if len(line.strip()) < 50 and (line.isupper() or line.istitle()):
            for section_name, patterns in section_patterns.items():
                if any(pattern in line_lower for pattern in patterns):
                    if section_name not in sections:
                        sections.append(section_name)
                    if section_name == "experience":
                        has_experience = True
                    elif section_name == "education":
                        has_education = True
                    elif section_name == "skills":
                        has_skills = True
                    break
    
    return {
        "sections": sections,
        "has_experience": has_experience,
        "has_education": has_education,
        "has_skills": has_skills,
        "section_count": len(sections),
        "status": "success"
    }


@tool
def update_cv_section_tool(cv_text: str, section_name: str, new_content: str) -> Dict[str, Any]:
    """
    Update a specific section in the CV text.
    
    Args:
        cv_text: The current CV text
        section_name: Name of the section to update (e.g., "Experience", "Skills")
        new_content: The new content for this section
    
    Returns:
        Dictionary with 'updated_cv' (the updated CV text) and 'status'
    """
    try:
        lines = cv_text.split('\n')
        updated_lines = []
        in_section = False
        section_found = False
        
        section_patterns = {
            "experience": ["experience", "work experience", "professional experience"],
            "education": ["education", "academic", "qualifications"],
            "skills": ["skills", "competencies", "technical skills"],
            "summary": ["summary", "profile", "objective"]
        }
        
        patterns = section_patterns.get(section_name.lower(), [section_name.lower()])
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            if not in_section and any(pattern in line_lower for pattern in patterns):
                if len(line.strip()) < 50:
                    in_section = True
                    section_found = True
                    updated_lines.append(line)
                    updated_lines.append(new_content)
                    continue
            
            if in_section:
                if i < len(lines) - 1:
                    next_line = lines[i + 1].lower().strip()
                    if len(next_line) < 50 and (next_line.isupper() or next_line.istitle()):
                        in_section = False
                continue
            
            updated_lines.append(line)
        
        if not section_found:
            updated_lines.append(f"\n{section_name.upper()}")
            updated_lines.append(new_content)
        
        updated_cv = '\n'.join(updated_lines)
        
        return {
            "updated_cv": updated_cv,
            "status": "success",
            "section_found": section_found
        }
    except Exception as e:
        return {
            "updated_cv": cv_text,
            "status": "error",
            "error": str(e)
        }


@tool
def search_cv_content_tool(cv_text: str, search_term: str) -> Dict[str, Any]:
    """
    Search for specific content in the CV text.
    
    Args:
        cv_text: The CV text to search
        search_term: The term or phrase to search for
    
    Returns:
        Dictionary with 'found' (bool), 'matches' (list of matching lines), and 'count' (number of matches)
    """
    try:
        lines = cv_text.split('\n')
        matches = []
        search_lower = search_term.lower()
        
        for i, line in enumerate(lines):
            if search_lower in line.lower():
                matches.append({
                    "line_number": i + 1,
                    "content": line.strip()
                })
        
        return {
            "found": len(matches) > 0,
            "matches": matches[:50],
            "count": len(matches),
            "status": "success"
        }
    except Exception as e:
        return {
            "found": False,
            "matches": [],
            "count": 0,
            "status": "error",
            "error": str(e)
        }

