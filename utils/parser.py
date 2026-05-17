import fitz  # PyMuPDF
import docx
import io
import re

def extract_from_pdf(file_bytes: bytes):
    """Extract text and metadata from a PDF file."""
    text = ""
    warnings = []
    has_tables = False
    has_images = False
    
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
            
            # Check for images
            if page.get_images(full=True):
                has_images = True
                
            # Basic table detection (using text blocks layout heuristic in fitz could be complex, 
            # but we can check if get_text("blocks") shows multi-column layouts)
            blocks = page.get_text("blocks")
            # If there are many parallel blocks, it might be a complex layout/table
            # PyMuPDF 1.23+ has find_tables()
            if hasattr(page, "find_tables"):
                if page.find_tables().tables:
                    has_tables = True
                    
        doc.close()
        
        if has_images:
            warnings.append("Images/Graphics detected. ATS systems cannot read images.")
        if has_tables:
            warnings.append("Tables detected. Tables can break ATS parsing.")
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        
    return text, warnings

def extract_from_docx(file_bytes: bytes):
    """Extract text and metadata from a DOCX file."""
    text = ""
    warnings = []
    has_tables = False
    
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
            
        if doc.tables:
            has_tables = True
            
        if has_tables:
            warnings.append("Tables detected. Tables can break ATS parsing.")
            
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        
    return text, warnings

def extract_sections(text: str):
    """Extract standard sections using regex."""
    sections = {
        "summary": "",
        "experience": "",
        "education": "",
        "skills": "",
        "projects": ""
    }
    
    # Very basic regex heuristics to find sections
    text_lower = text.lower()
    
    # Define keywords for sections
    sec_keywords = {
        "experience": [r'\bwork experience\b', r'\bprofessional experience\b', r'\bemployment history\b', r'\bexperience\b'],
        "education": [r'\beducation\b', r'\bacademic background\b', r'\bacademics\b'],
        "skills": [r'\bskills\b', r'\btechnical skills\b', r'\bcore competencies\b'],
        "projects": [r'\bprojects\b', r'\bpersonal projects\b', r'\bacademic projects\b'],
        "summary": [r'\bprofessional summary\b', r'\bsummary\b', r'\bprofile\b', r'\bobjective\b']
    }
    
    # Find all potential section headers and their starting positions
    found_sections = []
    for sec_name, patterns in sec_keywords.items():
        for pat in patterns:
            for match in re.finditer(pat, text_lower):
                # Ensure it looks like a header (e.g. newline before it, or start of line)
                start_idx = match.start()
                if start_idx == 0 or text_lower[start_idx-1] in ['\n', '\r']:
                    found_sections.append((start_idx, sec_name))
                    break # Only need the first reliable match for this section
    
    # Sort by position
    found_sections.sort(key=lambda x: x[0])
    
    # Extract text between headers
    for i, (start_idx, sec_name) in enumerate(found_sections):
        start_content = text[start_idx:].find('\n') + start_idx
        if i + 1 < len(found_sections):
            end_content = found_sections[i+1][0]
        else:
            end_content = len(text)
            
        content = text[start_content:end_content].strip()
        sections[sec_name] = content
        
    return sections

def parse_resume(file_obj):
    """Determine file type, extract text, sections, and metadata."""
    if file_obj is None:
        return None
    
    file_bytes = file_obj.read()
    
    # Flask uses .filename, Streamlit uses .name
    filename = getattr(file_obj, 'filename', None)
    if not filename:
        filename = getattr(file_obj, 'name', '')
    filename = filename.lower()
    
    text = ""
    warnings = []
    
    if filename.endswith(".pdf"):
        text, warnings = extract_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text, warnings = extract_from_docx(file_bytes)
    elif filename.endswith(".txt"):
        text = file_bytes.decode("utf-8")
    else:
        return None
        
    sections = extract_sections(text)
    
    return {
        "text": text,
        "sections": sections,
        "warnings": warnings
    }
