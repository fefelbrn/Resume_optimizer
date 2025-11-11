"""
PDF Generator for CV with Harvard Template
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from io import BytesIO
import re
from typing import Dict, List, Optional


def parse_cv_sections(cv_text: str) -> Dict[str, any]:
    """
    Parse CV text into structured sections for Harvard template.
    """
    sections = {
        'header': {'name': '', 'contact': ''},
        'education': [],
        'experience': [],
        'leadership': [],
        'skills': {'technical': [], 'language': [], 'laboratory': []}
    }
    
    lines = cv_text.split('\n')
    current_section = None
    current_entry = None
    
    # Common section headers (case-insensitive)
    section_patterns = {
        'education': r'education|formation|études|diplôme',
        'experience': r'experience|expérience|emploi|travail|work',
        'leadership': r'leadership|activité|activités|projet|projets|bénévolat',
        'skills': r'skill|compétence|compétences|langue|langues|technique|techniques'
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        line_lower = line.lower()
        if any(re.search(pattern, line_lower) for pattern in section_patterns.values()):
            if re.search(section_patterns['education'], line_lower):
                current_section = 'education'
            elif re.search(section_patterns['experience'], line_lower):
                current_section = 'experience'
            elif re.search(section_patterns['leadership'], line_lower):
                current_section = 'leadership'
            elif re.search(section_patterns['skills'], line_lower):
                current_section = 'skills'
            continue
        
        # Extract header (name and contact)
        if not sections['header']['name'] and len(line) < 100:
            # Try to extract name (usually first line, capitalized)
            if line.isupper() or (len(line.split()) <= 4 and any(c.isupper() for c in line)):
                sections['header']['name'] = line
            elif '@' in line or 'phone' in line.lower() or 'téléphone' in line.lower():
                sections['header']['contact'] = line
        
        # Parse entries based on current section
        if current_section == 'education':
            if line and not line.startswith('-') and not line.startswith('•'):
                # New education entry
                current_entry = {'title': line, 'details': [], 'location': '', 'date': ''}
                sections['education'].append(current_entry)
            elif current_entry and (line.startswith('-') or line.startswith('•')):
                current_entry['details'].append(line.lstrip('- •'))
        
        elif current_section == 'experience':
            if line and not line.startswith('-') and not line.startswith('•'):
                # New experience entry
                current_entry = {'title': line, 'details': [], 'location': '', 'date': ''}
                sections['experience'].append(current_entry)
            elif current_entry and (line.startswith('-') or line.startswith('•')):
                current_entry['details'].append(line.lstrip('- •'))
        
        elif current_section == 'leadership':
            if line and not line.startswith('-') and not line.startswith('•'):
                current_entry = {'title': line, 'details': [], 'location': '', 'date': ''}
                sections['leadership'].append(current_entry)
            elif current_entry and (line.startswith('-') or line.startswith('•')):
                current_entry['details'].append(line.lstrip('- •'))
    
    return sections


def generate_harvard_pdf(cv_text: str) -> BytesIO:
    """
    Generate a PDF CV using Harvard template style.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#000000'),
        spaceAfter=6,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    org_style = ParagraphStyle(
        'Organization',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#000000'),
        spaceAfter=2,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leftIndent=0
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        spaceAfter=4,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leftIndent=18
    )
    
    # Parse CV sections
    sections = parse_cv_sections(cv_text)
    
    # Header (Name and Contact)
    lines = cv_text.split('\n')
    header_lines = []
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if line:
            header_lines.append(line)
    
    # First line is usually the name
    if header_lines:
        story.append(Paragraph(escape_xml(header_lines[0]), title_style))
    
    # Contact info (lines 2-3 usually)
    contact_parts = []
    for line in header_lines[1:3]:
        if line and ('@' in line or any(kw in line.lower() for kw in ['phone', 'téléphone', 'tel', '+'])):
            contact_parts.append(line)
        elif line and len(line) < 60:
            contact_parts.append(line)
    
    if contact_parts:
        story.append(Paragraph(escape_xml(' • '.join(contact_parts[:3])), header_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Process the rest of the CV
    current_section = None
    section_started = False
    
    for i, line in enumerate(lines[3:], start=3):  # Skip header lines
        line = line.strip()
        if not line:
            continue
        
        # Check for section headers
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['education', 'formation', 'études', 'diplôme']):
            if section_started:
                story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("Education", section_style))
            current_section = 'education'
            section_started = True
            continue
        elif any(keyword in line_lower for keyword in ['experience', 'expérience', 'emploi', 'travail']):
            if section_started:
                story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("Experience", section_style))
            current_section = 'experience'
            section_started = True
            continue
        elif any(keyword in line_lower for keyword in ['leadership', 'activité', 'activités', 'projet', 'projets']):
            if section_started:
                story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("Leadership and Activities", section_style))
            current_section = 'leadership'
            section_started = True
            continue
        elif any(keyword in line_lower for keyword in ['skill', 'compétence', 'langue', 'technique']):
            if section_started:
                story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("Skills & Interests", section_style))
            current_section = 'skills'
            section_started = True
            continue
        
        # Format content based on line type
        if line.startswith('-') or line.startswith('•'):
            # Bullet point
            clean_line = line.lstrip('- •').strip()
            if clean_line:
                story.append(Paragraph(f"• {escape_xml(clean_line)}", bullet_style))
        elif len(line) > 0 and not line[0].islower() and len(line.split()) <= 8:
            # Likely a title/organization (short, capitalized)
            story.append(Paragraph(escape_xml(line), org_style))
        else:
            # Regular text
            story.append(Paragraph(escape_xml(line), normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def escape_xml(text: str) -> str:
    """Escape XML special characters for ReportLab."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def format_entry(title: str, location: str, date: str) -> str:
    """Format an entry with title, location, and date."""
    parts = [title]
    if location:
        parts.append(location)
    if date:
        parts.append(date)
    return " • ".join(parts) if len(parts) > 1 else title


def extract_contact_info(text: str) -> str:
    """Extract contact information from CV text."""
    lines = text.split('\n')[:5]  # Check first 5 lines
    contact_parts = []
    
    for line in lines:
        line = line.strip()
        if '@' in line:
            contact_parts.append(line)
        elif any(keyword in line.lower() for keyword in ['phone', 'téléphone', 'tel']):
            contact_parts.append(line)
        elif len(line) > 5 and len(line) < 50 and not line.isupper():
            # Might be address
            if any(char.isdigit() for char in line):
                contact_parts.append(line)
    
    return " • ".join(contact_parts[:3]) if contact_parts else ""


def extract_skills_section(text: str) -> str:
    """Extract skills section from CV text."""
    skills_pattern = r'(?:skill|compétence|compétences|langue|technique)[s]?:?\s*(.*?)(?=\n\n|\n[A-Z]|$)'
    match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        skills_text = match.group(1).strip()
        # Clean up the text
        skills_text = re.sub(r'\n+', ', ', skills_text)
        return skills_text[:200]  # Limit length
    return ""


