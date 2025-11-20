"""
RAG System for CV Optimizer
Handles vectorization, storage, and semantic search of CVs and Job Descriptions
"""
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Fallback: simple text splitter
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=500, chunk_overlap=50, **kwargs):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
            
            def split_text(self, text: str) -> List[str]:
                chunks = []
                start = 0
                while start < len(text):
                    end = start + self.chunk_size
                    chunks.append(text[start:end])
                    start = end - self.chunk_overlap
                return chunks

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        # Fallback: simple Document class
        class Document:
            def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
                self.page_content = page_content
                self.metadata = metadata or {}
import os
import tempfile
import shutil


class RAGSystem:
    """
    RAG System for managing vectorized documents (CVs and Job Descriptions)
    """
    
    def __init__(self, api_key: str, persist_directory: Optional[str] = None):
        """
        Initialize RAG system with embeddings and vector store.
        
        Args:
            api_key: OpenAI API key for embeddings
            persist_directory: Optional directory to persist vector store (if None, uses in-memory)
        """
        self.api_key = api_key
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Vector stores for CV and JD
        self.cv_vectorstore: Optional[Chroma] = None
        self.jd_vectorstore: Optional[Chroma] = None
        
        # Temporary directories for persistence (if needed)
        self.cv_persist_dir = None
        self.jd_persist_dir = None
        
        # If persist_directory provided, use it
        if persist_directory:
            self.cv_persist_dir = os.path.join(persist_directory, "cv_vectors")
            self.jd_persist_dir = os.path.join(persist_directory, "jd_vectors")
    
    def index_cv(self, cv_text: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Index CV text in vector database.
        
        Args:
            cv_text: CV text to index
            session_id: Session identifier for isolation
            
        Returns:
            Dictionary with indexing details (chunks_count, total_chars, etc.)
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(cv_text)
            
            # Create documents with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={"session_id": session_id, "chunk_index": i, "type": "cv"}
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Create or update vector store
            if self.cv_persist_dir:
                persist_path = os.path.join(self.cv_persist_dir, session_id)
                os.makedirs(persist_path, exist_ok=True)
                
                # If vectorstore exists, delete and recreate
                if os.path.exists(persist_path):
                    shutil.rmtree(persist_path)
                
                self.cv_vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=persist_path
                )
            else:
                # In-memory vector store
                self.cv_vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=f"cv_{session_id}"
                )
            
            # Return indexing details
            return {
                "chunks_count": len(chunks),
                "total_chars": len(cv_text),
                "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunk_sizes": [len(c) for c in chunks]
            }
        except Exception as e:
            raise Exception(f"Error indexing CV: {str(e)}")
    
    def index_jd(self, jd_text: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Index Job Description text in vector database.
        
        Args:
            jd_text: Job description text to index
            session_id: Session identifier for isolation
            
        Returns:
            Dictionary with indexing details (chunks_count, total_chars, etc.)
        """
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(jd_text)
            
            # Create documents with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={"session_id": session_id, "chunk_index": i, "type": "jd"}
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Create or update vector store
            if self.jd_persist_dir:
                persist_path = os.path.join(self.jd_persist_dir, session_id)
                os.makedirs(persist_path, exist_ok=True)
                
                # If vectorstore exists, delete and recreate
                if os.path.exists(persist_path):
                    shutil.rmtree(persist_path)
                
                self.jd_vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=persist_path
                )
            else:
                # In-memory vector store
                self.jd_vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=f"jd_{session_id}"
                )
            
            # Return indexing details
            return {
                "chunks_count": len(chunks),
                "total_chars": len(jd_text),
                "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "chunk_sizes": [len(c) for c in chunks]
            }
        except Exception as e:
            raise Exception(f"Error indexing JD: {str(e)}")
    
    def retrieve_from_cv(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant chunks from CV vector store using semantic search.
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            
        Returns:
            List of relevant Document chunks
        """
        if self.cv_vectorstore is None:
            return []
        
        try:
            results = self.cv_vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Error retrieving from CV: {str(e)}")
            return []
    
    def retrieve_from_jd(self, query: str, k: int = 3) -> List[Document]:
        """
        Retrieve relevant chunks from Job Description vector store using semantic search.
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            
        Returns:
            List of relevant Document chunks
        """
        if self.jd_vectorstore is None:
            return []
        
        try:
            results = self.jd_vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"Error retrieving from JD: {str(e)}")
            return []
    
    def retrieve_with_scores(self, query: str, k: int = 5, source: str = "cv") -> List[Tuple[Document, float]]:
        """
        Retrieve chunks with similarity scores.
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            source: "cv" or "jd"
            
        Returns:
            List of tuples (Document, similarity_score) where similarity_score is between 0 and 1
        """
        vectorstore = self.cv_vectorstore if source == "cv" else self.jd_vectorstore
        
        if vectorstore is None:
            return []
        
        try:
            results = vectorstore.similarity_search_with_score(query, k=k)
            
            # Chroma returns distances, not similarities
            # For cosine similarity: distance = 1 - similarity, so similarity = 1 - distance
            # But, also happen: similarity = 1 - (distance / 2) for cosine distance
            
            normalized_results = []
            for doc, score in results:
                # -> If normalized: distance in [0, 1] where 0 = identical, 1 = orthogonal
                # -> If not normalized: distance in [0, 2] where 0 = identical, 2 = opposite

                # Convert distance to similarity and ensure it's in [0, 1] range
                if score < 0:
                    # Negative score is unusual, treat as 0 similarity
                    similarity = 0.0
                elif score <= 1.0:
                    # Score in [0, 1] - treat as normalized cosine distance
                    similarity = 1.0 - score
                elif score <= 2.0:
                    # Score in (1, 2] - treat as non-normalized cosine distance
                    similarity = 1.0 - (score / 2.0)
                else:
                    # Normalize using inverse relationship
                    similarity = max(0.0, 1.0 / (1.0 + score))
                
                similarity = max(0.0, min(1.0, similarity))
                normalized_results.append((doc, similarity))
            
            return normalized_results
        except Exception as e:
            print(f"Error retrieving with scores from {source}: {str(e)}")
            return []
    
    def get_context_with_sources(self, query: str, k_cv: int = 5, k_jd: int = 3) -> Dict[str, Any]:
        """
        Get context from both CV and JD with source information.
        
        Args:
            query: Search query
            k_cv: Number of CV chunks to retrieve
            k_jd: Number of JD chunks to retrieve
            
        Returns:
            Dictionary with 'cv_context', 'jd_context', 'cv_sources', 'jd_sources', 'cv_chunks_details', 'jd_chunks_details'
        """
        cv_chunks = self.retrieve_from_cv(query, k=k_cv)
        jd_chunks = self.retrieve_from_jd(query, k=k_jd)
        
        # Get chunks with scores for detailed logging
        cv_chunks_with_scores = self.retrieve_with_scores(query, k=k_cv, source="cv")
        jd_chunks_with_scores = self.retrieve_with_scores(query, k=k_jd, source="jd")
        
        cv_context = "\n\n".join([
            f"[Chunk {i+1}]: {chunk.page_content}"
            for i, chunk in enumerate(cv_chunks)
        ])
        
        jd_context = "\n\n".join([
            f"[Chunk {i+1}]: {chunk.page_content}"
            for i, chunk in enumerate(jd_chunks)
        ])
        
        cv_sources = [chunk.page_content for chunk in cv_chunks]
        jd_sources = [chunk.page_content for chunk in jd_chunks]
        
        # Detailed chunks info with scores
        cv_chunks_details = [
            {
                "index": i + 1,
                "content": chunk.page_content,
                "similarity_score": float(score),
                "metadata": chunk.metadata if hasattr(chunk, 'metadata') else {}
            }
            for i, (chunk, score) in enumerate(cv_chunks_with_scores)
        ]
        
        jd_chunks_details = [
            {
                "index": i + 1,
                "content": chunk.page_content,
                "similarity_score": float(score),
                "metadata": chunk.metadata if hasattr(chunk, 'metadata') else {}
            }
            for i, (chunk, score) in enumerate(jd_chunks_with_scores)
        ]
        
        return {
            "cv_context": cv_context,
            "jd_context": jd_context,
            "cv_sources": cv_sources,
            "jd_sources": jd_sources,
            "cv_chunks": cv_chunks,
            "jd_chunks": jd_chunks,
            "cv_chunks_details": cv_chunks_details,
            "jd_chunks_details": jd_chunks_details,
            "query": query
        }
    
    def clear_cv(self) -> None:
        """Clear CV vector store."""
        self.cv_vectorstore = None
    
    def clear_jd(self) -> None:
        """Clear JD vector store."""
        self.jd_vectorstore = None
    
    def clear_all(self) -> None:
        """Clear all vector stores."""
        self.clear_cv()
        self.clear_jd()