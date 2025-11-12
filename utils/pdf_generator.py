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


def escape_xml(text: str) -> str:
    """Escape XML special characters for ReportLab."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def generate_harvard_pdf(cv_text: str) -> BytesIO:
    """
    Generate a PDF CV using Harvard template style.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
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
    lines = cv_text.split('\n')
    header_lines = []
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if line:
            header_lines.append(line)
    
    # First line is usually the name
    if header_lines:
        story.append(Paragraph(escape_xml(header_lines[0]), title_style))
    
    # Contact info
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
    
    for i, line in enumerate(lines[3:], start=3):
        line = line.strip()
        if not line:
            continue
        
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
        
        # Format content
        if line.startswith('-') or line.startswith('•'):
            clean_line = line.lstrip('- •').strip()
            if clean_line:
                story.append(Paragraph(f"• {escape_xml(clean_line)}", bullet_style))
        elif len(line) > 0 and not line[0].islower() and len(line.split()) <= 8:
            story.append(Paragraph(escape_xml(line), org_style))
        else:
            story.append(Paragraph(escape_xml(line), normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

