"""
Utility to extract text from PDF files
"""
import PyPDF2
import pdfplumber
from io import BytesIO
from typing import Optional


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from a PDF file using multiple methods for better accuracy.
    
    Args:
        pdf_file: File-like object or bytes
        
    Returns:
        Extracted text as string
    """
    text = ""
    
    try:
        if isinstance(pdf_file, bytes):
            pdf_file = BytesIO(pdf_file)
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"pdfplumber failed: {e}")
    
    # Fallback to PyPDF2
    try:
        if isinstance(pdf_file, bytes):
            pdf_file = BytesIO(pdf_file)
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
    
    return text.strip() if text else ""