"""
RAG Hot System - Simple text-based retrieval without embeddings
Uses keyword matching and text similarity to find relevant chunks
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List, Tuple
import re
from difflib import SequenceMatcher
from utils.cv_optimizer import parse_openai_error


def split_document_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Split document into chunks with overlap for better context.
    
    Args:
        text: Document text to split
        chunk_size: Target size of each chunk (in words)
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of chunks with metadata
    """
    words = text.split()
    chunks = []
    
    if len(words) <= chunk_size:
        # Document is small enough, return as single chunk
        return [{
            "id": 0,
            "text": text,
            "start_word": 0,
            "end_word": len(words),
            "word_count": len(words)
        }]
    
    start = 0
    chunk_id = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "start_word": start,
            "end_word": end,
            "word_count": len(chunk_words)
        })
        
        # Move start position with overlap
        start = end - overlap
        chunk_id += 1
        
        # Prevent infinite loop
        if start >= len(words) - overlap:
            break
    
    return chunks


def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from text (simple approach).
    
    Args:
        text: Text to extract keywords from
    
    Returns:
        List of significant words (filtered)
    """
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    
    # Filter out common stop words (French and English)
    stop_words = {
        'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'à', 'pour',
        'the', 'a', 'an', 'and', 'or', 'to', 'for', 'of', 'in', 'on', 'at', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those',
        'what', 'which', 'who', 'where', 'when', 'why', 'how'
    }
    
    # Get words that are not stop words and have length > 2
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    
    return unique_keywords


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using SequenceMatcher.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0 and 1
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def find_relevant_chunks(question: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Find most relevant chunks for a question using keyword matching and similarity.
    
    Args:
        question: User's question
        chunks: List of document chunks
        top_k: Number of top chunks to return
    
    Returns:
        List of relevant chunks with relevance scores
    """
    question_keywords = extract_keywords(question)
    question_lower = question.lower()
    
    scored_chunks = []
    
    for chunk in chunks:
        chunk_text = chunk["text"]
        chunk_lower = chunk_text.lower()
        
        # Score 1: Keyword matching (count how many keywords appear)
        keyword_matches = sum(1 for keyword in question_keywords if keyword in chunk_lower)
        keyword_score = keyword_matches / len(question_keywords) if question_keywords else 0
        
        # Score 2: Text similarity
        similarity_score = calculate_text_similarity(question, chunk_text)
        
        # Score 3: Direct phrase matching (bonus)
        phrase_bonus = 0
        question_phrases = [q.strip() for q in question.split('?') if q.strip()]
        for phrase in question_phrases:
            if len(phrase) > 5 and phrase.lower() in chunk_lower:
                phrase_bonus += 0.2
        
        # Combined score (weighted)
        total_score = (keyword_score * 0.5) + (similarity_score * 0.3) + min(phrase_bonus, 0.2)
        
        scored_chunks.append({
            **chunk,
            "relevance_score": total_score,
            "keyword_matches": keyword_matches
        })
    
    # Sort by relevance score (descending)
    scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Return top K chunks
    return scored_chunks[:top_k]


def format_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format chunks for display as sources.
    
    Args:
        chunks: List of relevant chunks with scores
    
    Returns:
        Formatted sources for display
    """
    sources = []
    for chunk in chunks:
        # Extract a preview (first 150 characters)
        preview = chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
        
        sources.append({
            "chunk_id": chunk["id"],
            "preview": preview,
            "relevance_score": round(chunk["relevance_score"], 2),
            "word_range": f"words {chunk['start_word']}-{chunk['end_word']}"
        })
    
    return sources


def generate_chat_response(
    question: str,
    document_text: str,
    relevant_chunks: List[Dict[str, Any]],
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    language: str = "fr"
) -> Dict[str, Any]:
    """
    Generate a chat response using relevant chunks from the document.
    
    Args:
        question: User's question
        document_text: Full document text (for context)
        relevant_chunks: List of relevant chunks
        api_key: OpenAI API key
        model: Model to use
        temperature: Temperature for generation
        language: Response language
    
    Returns:
        Dictionary with answer and metadata
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )
    
    # Build context from relevant chunks
    context_parts = []
    for i, chunk in enumerate(relevant_chunks, 1):
        context_parts.append(f"[Extrait {i}]\n{chunk['text']}")
    
    context = "\n\n".join(context_parts)
    
    # Language mapping
    language_names = {
        "fr": "French (Français)",
        "en": "English",
        "es": "Spanish (Español)"
    }
    target_language = language_names.get(language, "French (Français)")
    
    # Build system message
    system_message = f"""You are a helpful assistant that answers questions based on a document provided by the user.

CRITICAL: You must answer ONLY using information from the document extracts provided. If the information is not in the extracts, say so clearly.

Guidelines:
- Answer in {target_language}
- Be precise and cite which extract(s) you used
- If the question cannot be answered from the document, say so
- Be concise but complete
- Use natural, conversational language"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", """Document Context:
{context}

Question: {question}

Answer the question based on the document extracts above. If you use information from a specific extract, mention it (e.g., "According to Extrait 1...").""")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "context": context,
            "question": question
        })
        
        answer = response.content
        
        return {
            "answer": answer,
            "model_used": model,
            "temperature": temperature,
            "word_count": len(answer.split())
        }
    except Exception as e:
        error_info = parse_openai_error(e)
        return {
            "error": error_info["user_message"],
            "error_code": error_info["error_code"],
            "error_details": error_info["error_message"],
            "answer": None
        }

