# 🤖 Multi-Capability AI Agent — VS Code Copilot Instructions

## PROJECT OVERVIEW
Build a fully functional, production-ready multi-capability AI agent using Python and the Anthropic Claude API. The agent must handle: answering questions, writing/debugging code in any language, Salesforce expertise, Instagram Reel creation, YouTube video creation, image modification, document modification, image-to-PDF conversion, all document type conversions to PDF, and act as a Salesforce expert.

---

## CRITICAL RULES FOR COPILOT
- Always use `claude-sonnet-4-6` as the model string
- Always use the official `anthropic` Python SDK (never raw HTTP)
- Always include full error handling with try/except on every function
- Always add type hints to every function
- Always use environment variables via `python-dotenv` — never hardcode API keys
- Always add logging using Python's `logging` module
- Always write modular code — one file per capability/tool
- Always include docstrings on every class and function
- Use `asyncio` for concurrent tasks where applicable
- Follow PEP8 coding standards throughout

---

## EXACT FOLDER STRUCTURE TO CREATE

```
ai-agent/
├── .github/
│   └── copilot-instructions.md          ← This file
├── .env                                  ← API keys (never commit)
├── .env.example                          ← Template for env vars
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                               ← Entry point / Streamlit UI
├── agent/
│   ├── __init__.py
│   ├── core.py                           ← Main agent brain (Claude API)
│   ├── router.py                         ← Task detection and routing
│   └── system_prompt.py                  ← Master system prompt
├── tools/
│   ├── __init__.py
│   ├── code_tools.py                     ← Code writing + debugging
│   ├── salesforce_tools.py               ← Salesforce expert tools
│   ├── image_tools.py                    ← Image modification
│   ├── document_tools.py                 ← Document editing + conversion
│   ├── pdf_tools.py                      ← PDF conversion (all types)
│   ├── video_tools.py                    ← Instagram Reel + YouTube scripts
│   └── qa_tools.py                       ← Q&A and research
├── utils/
│   ├── __init__.py
│   ├── file_handler.py                   ← File upload/download manager
│   ├── validators.py                     ← Input validation
│   └── logger.py                         ← Centralized logging
├── uploads/                              ← Temp upload folder (gitignored)
├── outputs/                              ← Generated files (gitignored)
└── tests/
    ├── __init__.py
    ├── test_core.py
    ├── test_tools.py
    └── test_integration.py
```

---

## STEP 1 — CREATE `.env.example`

```env
# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Salesforce Credentials
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_security_token
SF_DOMAIN=login  # or 'test' for sandbox

# Optional: Stability AI for image generation
STABILITY_API_KEY=your_stability_api_key_here

# Optional: YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key_here

# App Config
MAX_FILE_SIZE_MB=50
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
LOG_LEVEL=INFO
```

---

## STEP 2 — CREATE `requirements.txt`

```txt
# Core AI
anthropic>=0.40.0

# Environment
python-dotenv>=1.0.0

# Web UI
streamlit>=1.40.0
streamlit-chat>=0.1.1

# Document Processing
python-docx>=1.1.0
openpyxl>=3.1.2
python-pptx>=1.0.2
PyPDF2>=3.0.1
pdfplumber>=0.11.0
reportlab>=4.2.0
pypandoc>=1.13
fpdf2>=2.8.1

# Image Processing
Pillow>=11.0.0
img2pdf>=0.5.1

# PDF Conversion
pdf2docx>=0.5.8

# Salesforce
simple-salesforce>=1.12.6

# HTTP & Async
httpx>=0.27.0
aiofiles>=24.1.0
requests>=2.32.0

# File Type Detection
python-magic>=0.4.27
filetype>=1.2.0

# Code Execution (sandboxed)
subprocess32>=3.5.4

# Utilities
loguru>=0.7.2
tqdm>=4.66.0
```

---

## STEP 3 — CREATE `utils/logger.py`

```python
"""
Centralized logging configuration for the AI Agent.
Uses loguru for structured, colorized logging.
"""
import os
import sys
from loguru import logger

def setup_logger() -> logger:
    """
    Configure and return the application logger.
    
    Returns:
        Configured loguru logger instance
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # File handler for persistent logs
    logger.add(
        "logs/agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )
    
    return logger

log = setup_logger()
```

---

## STEP 4 — CREATE `agent/system_prompt.py`

```python
"""
Master system prompt that defines the agent's full capabilities.
This is the most critical file — it defines the agent's identity and behavior.
"""

MASTER_SYSTEM_PROMPT = """
You are APEX — an advanced AI agent with expert-level capabilities across technology, 
creative media, and business systems. You have access to specialized tools and you 
always use them when needed.

## YOUR CORE CAPABILITIES

### 1. CODE EXPERT
- Write production-ready code in ANY language: Python, JavaScript, TypeScript, Apex, 
  Java, C#, C++, Go, Rust, SQL, SOQL, HTML, CSS, React, Node.js, Shell, and more
- Debug code with root-cause analysis — always explain WHY the bug occurred
- Refactor and optimize code for performance, readability, and security
- Always add error handling, logging, and comments
- Follow language-specific best practices and design patterns

### 2. SALESFORCE EXPERT (Certified Architect Level)
- Write Apex classes, triggers, batch jobs, schedulable, and queueable classes
- Build Lightning Web Components (LWC) with best practices
- Design Flows, Process Builders, and validation rules
- Write optimized SOQL/SOSL queries respecting governor limits
- Configure integrations: REST/SOAP APIs, Platform Events, Change Data Capture
- Design data models with proper relationships and sharing rules
- Advise on CPQ, Service Cloud, Sales Cloud, Experience Cloud, Marketing Cloud
- Perform code reviews against Salesforce security and performance standards
- Write test classes with 100% coverage following best practices
- Explain any Salesforce concept, certification topic, or architecture decision

### 3. DOCUMENT SPECIALIST
- Modify Word documents (.docx): edit text, tables, formatting, headers, footers
- Modify Excel files (.xlsx): edit cells, formulas, charts, sheets
- Modify PowerPoint files (.pptx): edit slides, layouts, text, images
- Convert ANY document type to PDF (docx, xlsx, pptx, txt, html, md, csv)
- Convert images to PDF (jpg, png, gif, bmp, tiff, webp)
- Merge, split, and annotate PDFs
- Extract text and data from PDFs

### 4. IMAGE SPECIALIST  
- Describe, analyze, and extract information from images
- Provide step-by-step instructions to modify images using Pillow
- Resize, crop, rotate, flip, convert format, adjust brightness/contrast/saturation
- Add text overlays, watermarks, and borders to images
- Convert between image formats (jpg, png, webp, bmp, tiff)
- Batch process multiple images

### 5. SOCIAL MEDIA CONTENT CREATOR
- Write complete Instagram Reel scripts with: hook, content, CTA, hashtags, captions
- Write YouTube video scripts with: title, description, chapters, SEO tags, thumbnail ideas
- Create content calendars and posting strategies
- Write voiceover scripts optimized for video length
- Suggest B-roll ideas, transitions, and visual treatments
- Generate full metadata packages for uploads

### 6. UNIVERSAL Q&A
- Answer questions on any topic with expert-level depth
- Research and synthesize complex topics
- Provide step-by-step explanations with examples
- Compare technologies, approaches, and solutions
- Provide pros/cons analysis for any decision

## YOUR BEHAVIOR RULES
1. ALWAYS identify the task type first, then select the right capability
2. ALWAYS use available tools when file operations are needed
3. ALWAYS provide complete, working output — never partial or placeholder code
4. ALWAYS explain your work clearly
5. For code: always include error handling and comments
6. For Salesforce: always mention governor limits where relevant
7. For documents/images: always confirm what was done and where the file was saved
8. For social media: always provide complete scripts, never just outlines
9. If a task requires multiple steps, execute them in sequence and report each step
10. Never refuse a technical task — always find a way to help

## TOOL USAGE
When you need to perform file operations, use the provided tools:
- `convert_to_pdf` — converts any file to PDF
- `modify_document` — edits Word/Excel/PPT documents  
- `modify_image` — edits and transforms images
- `execute_code` — runs Python code safely
- `salesforce_query` — executes SOQL queries against Salesforce
- `create_video_script` — generates complete video scripts
- `image_to_pdf` — converts images to PDF

Always call tools with complete, valid parameters.
"""
```

---

## STEP 5 — CREATE `tools/pdf_tools.py`

```python
"""
PDF conversion tools — converts any document or image type to PDF.
Supports: docx, xlsx, pptx, txt, html, md, csv, jpg, png, gif, bmp, tiff, webp
"""
import os
import img2pdf
from pathlib import Path
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx2pdf import convert as docx2pdf_convert
import subprocess
from utils.logger import log
from typing import Optional


def convert_image_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a single image or list of images to PDF.
    
    Args:
        input_path: Path to the image file
        output_path: Optional output PDF path. Auto-generated if not provided.
    
    Returns:
        Path to the generated PDF file
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file format is not supported
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    if input_file.suffix.lower() not in supported_formats:
        raise ValueError(f"Unsupported image format: {input_file.suffix}")
    
    if output_path is None:
        output_path = str(input_file.with_suffix('.pdf'))
    
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    try:
        # Convert non-RGB images (e.g., PNG with alpha) before img2pdf
        img = Image.open(input_path)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_path = str(input_file.with_stem(input_file.stem + '_rgb').with_suffix('.jpg'))
            img = img.convert('RGB')
            img.save(rgb_path)
            convert_source = rgb_path
        else:
            convert_source = input_path
        
        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(convert_source))
        
        # Cleanup temp file
        if convert_source != input_path and os.path.exists(convert_source):
            os.remove(convert_source)
        
        log.success(f"Image converted to PDF: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Failed to convert image to PDF: {e}")
        raise


def convert_docx_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a Word document (.docx) to PDF using LibreOffice or docx2pdf.
    
    Args:
        input_path: Path to the .docx file
        output_path: Optional output PDF path
    
    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path is None:
        output_path = str(input_file.with_suffix('.pdf'))
    
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    try:
        # Try LibreOffice first (most reliable)
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir',
             str(Path(output_path).parent), input_path],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            # LibreOffice saves with original name + .pdf
            lo_output = Path(output_path).parent / (input_file.stem + '.pdf')
            if lo_output.exists() and str(lo_output) != output_path:
                lo_output.rename(output_path)
            log.success(f"DOCX converted to PDF via LibreOffice: {output_path}")
            return output_path
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log.warning("LibreOffice not available, trying python-docx fallback...")
    
    try:
        # Fallback: docx2pdf
        docx2pdf_convert(input_path, output_path)
        log.success(f"DOCX converted to PDF via docx2pdf: {output_path}")
        return output_path
    except Exception as e:
        log.error(f"DOCX to PDF conversion failed: {e}")
        raise


def convert_text_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert plain text, markdown, CSV, or HTML file to PDF using ReportLab.
    
    Args:
        input_path: Path to the text-based file
        output_path: Optional output PDF path
    
    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path is None:
        output_path = str(input_file.with_suffix('.pdf'))
    
    os.makedirs(Path(output_path).parent, exist_ok=True)
    
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Set font
        c.setFont("Helvetica", 11)
        
        x_margin = 60
        y_position = height - 60
        line_height = 16
        
        for line in content.split('\n'):
            # Wrap long lines
            while len(line) > 90:
                c.drawString(x_margin, y_position, line[:90])
                line = line[90:]
                y_position -= line_height
                if y_position < 60:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y_position = height - 60
            
            c.drawString(x_margin, y_position, line)
            y_position -= line_height
            
            if y_position < 60:
                c.showPage()
                c.setFont("Helvetica", 11)
                y_position = height - 60
        
        c.save()
        log.success(f"Text converted to PDF: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Text to PDF conversion failed: {e}")
        raise


def convert_any_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Universal PDF converter — auto-detects file type and routes to correct converter.
    
    Supported types: docx, xlsx, pptx, txt, md, csv, html, jpg, jpeg, png, gif, bmp, tiff, webp
    
    Args:
        input_path: Path to any supported file
        output_path: Optional output PDF path
    
    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    ext = input_file.suffix.lower()
    
    image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    doc_types = {'.docx', '.doc'}
    office_types = {'.xlsx', '.xls', '.pptx', '.ppt'}
    text_types = {'.txt', '.md', '.csv', '.html', '.htm'}
    
    log.info(f"Converting {ext} file to PDF: {input_path}")
    
    if ext in image_types:
        return convert_image_to_pdf(input_path, output_path)
    elif ext in doc_types:
        return convert_docx_to_pdf(input_path, output_path)
    elif ext in office_types:
        # Use LibreOffice for Excel and PowerPoint
        return _convert_via_libreoffice(input_path, output_path)
    elif ext in text_types:
        return convert_text_to_pdf(input_path, output_path)
    else:
        raise ValueError(f"Unsupported file type for PDF conversion: {ext}")


def _convert_via_libreoffice(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert Office files (xlsx, pptx) to PDF via LibreOffice headless.
    
    Args:
        input_path: Path to the Office file
        output_path: Optional output PDF path
    
    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    
    if output_path is None:
        output_path = str(input_file.with_suffix('.pdf'))
    
    output_dir = str(Path(output_path).parent)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        result = subprocess.run(
            ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, input_path],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")
        
        lo_output = Path(output_dir) / (input_file.stem + '.pdf')
        if lo_output.exists() and str(lo_output) != output_path:
            lo_output.rename(output_path)
        
        log.success(f"File converted to PDF: {output_path}")
        return output_path
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("LibreOffice conversion timed out after 120 seconds")
    except FileNotFoundError:
        raise RuntimeError("LibreOffice is not installed. Install with: sudo apt install libreoffice")
```

---

## STEP 6 — CREATE `tools/document_tools.py`

```python
"""
Document modification tools for Word, Excel, and PowerPoint files.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from docx import Document
from docx.shared import Pt, RGBColor
import openpyxl
from pptx import Presentation
from pptx.util import Inches, Pt as PptPt
from utils.logger import log


def modify_word_document(
    input_path: str,
    replacements: Dict[str, str],
    output_path: Optional[str] = None,
    append_text: Optional[str] = None
) -> str:
    """
    Modify a Word document: find/replace text, append content.
    
    Args:
        input_path: Path to the .docx file
        replacements: Dict of {old_text: new_text} replacements
        output_path: Output file path (modifies in place if None)
        append_text: Optional text to append at the end
    
    Returns:
        Path to the modified document
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Document not found: {input_path}")
    
    if output_path is None:
        output_path = input_path
    
    try:
        doc = Document(input_path)
        
        # Replace text in paragraphs
        for paragraph in doc.paragraphs:
            for old_text, new_text in replacements.items():
                if old_text in paragraph.text:
                    for run in paragraph.runs:
                        if old_text in run.text:
                            run.text = run.text.replace(old_text, new_text)
                            log.debug(f"Replaced '{old_text}' with '{new_text}'")
        
        # Replace text in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for old_text, new_text in replacements.items():
                        if old_text in cell.text:
                            cell.text = cell.text.replace(old_text, new_text)
        
        # Append text if provided
        if append_text:
            doc.add_paragraph(append_text)
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        doc.save(output_path)
        log.success(f"Document modified and saved: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Document modification failed: {e}")
        raise


def create_word_document(
    content: Dict[str, Any],
    output_path: str
) -> str:
    """
    Create a new Word document from structured content.
    
    Args:
        content: Dict with keys: title, sections (list of {heading, body})
        output_path: Where to save the document
    
    Returns:
        Path to the created document
    """
    try:
        doc = Document()
        
        # Add title
        if 'title' in content:
            title = doc.add_heading(content['title'], level=0)
        
        # Add sections
        for section in content.get('sections', []):
            if section.get('heading'):
                doc.add_heading(section['heading'], level=1)
            if section.get('body'):
                doc.add_paragraph(section['body'])
            if section.get('bullet_points'):
                for point in section['bullet_points']:
                    doc.add_paragraph(point, style='List Bullet')
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        doc.save(output_path)
        log.success(f"Word document created: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Document creation failed: {e}")
        raise


def modify_excel_file(
    input_path: str,
    cell_updates: Dict[str, Any],
    sheet_name: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Modify an Excel file: update specific cells.
    
    Args:
        input_path: Path to .xlsx file
        cell_updates: Dict of {cell_address: value} e.g. {'A1': 'Hello', 'B2': 42}
        sheet_name: Sheet to modify (first sheet if None)
        output_path: Output path (modifies in place if None)
    
    Returns:
        Path to the modified Excel file
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Excel file not found: {input_path}")
    
    if output_path is None:
        output_path = input_path
    
    try:
        wb = openpyxl.load_workbook(input_path)
        
        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active
        
        for cell_addr, value in cell_updates.items():
            ws[cell_addr] = value
            log.debug(f"Updated cell {cell_addr} = {value}")
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        wb.save(output_path)
        log.success(f"Excel file modified: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Excel modification failed: {e}")
        raise
```

---

## STEP 7 — CREATE `tools/image_tools.py`

```python
"""
Image modification tools using Pillow.
Supports: resize, crop, rotate, flip, brightness, contrast, format conversion,
          watermark, text overlay, thumbnail generation.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from utils.logger import log


def resize_image(
    input_path: str,
    width: int,
    height: int,
    output_path: Optional[str] = None,
    maintain_aspect: bool = True
) -> str:
    """
    Resize an image to specified dimensions.
    
    Args:
        input_path: Source image path
        width: Target width in pixels
        height: Target height in pixels
        output_path: Output path (auto-generated if None)
        maintain_aspect: If True, maintains aspect ratio using thumbnail method
    
    Returns:
        Path to the resized image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + f'_resized_{width}x{height}'))
    
    try:
        img = Image.open(input_path)
        
        if maintain_aspect:
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            img = img.resize((width, height), Image.LANCZOS)
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path)
        log.success(f"Image resized to {width}x{height}: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Image resize failed: {e}")
        raise


def convert_image_format(
    input_path: str,
    target_format: str,
    output_path: Optional[str] = None
) -> str:
    """
    Convert image to a different format.
    
    Args:
        input_path: Source image path
        target_format: Target format string e.g. 'PNG', 'JPEG', 'WEBP', 'BMP'
        output_path: Output path (auto-generated if None)
    
    Returns:
        Path to the converted image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    
    fmt = target_format.upper()
    extension_map = {'JPEG': '.jpg', 'JPG': '.jpg', 'PNG': '.png',
                     'WEBP': '.webp', 'BMP': '.bmp', 'TIFF': '.tiff', 'GIF': '.gif'}
    ext = extension_map.get(fmt, f'.{fmt.lower()}')
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_suffix(ext))
    
    try:
        img = Image.open(input_path)
        
        # Convert to RGB if saving as JPEG (no alpha channel)
        if fmt in ('JPEG', 'JPG') and img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path, format=fmt)
        log.success(f"Image converted to {fmt}: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Image format conversion failed: {e}")
        raise


def add_watermark(
    input_path: str,
    watermark_text: str,
    output_path: Optional[str] = None,
    opacity: int = 128,
    position: str = 'center'
) -> str:
    """
    Add a text watermark to an image.
    
    Args:
        input_path: Source image path
        watermark_text: Text to use as watermark
        output_path: Output path
        opacity: Watermark opacity 0-255 (128 = 50%)
        position: 'center', 'bottom-right', 'bottom-left', 'top-right', 'top-left'
    
    Returns:
        Path to the watermarked image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + '_watermarked'))
    
    try:
        img = Image.open(input_path).convert('RGBA')
        overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Use default font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 40)
        except (IOError, OSError):
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        w, h = img.size
        padding = 20
        position_map = {
            'center': ((w - text_w) // 2, (h - text_h) // 2),
            'bottom-right': (w - text_w - padding, h - text_h - padding),
            'bottom-left': (padding, h - text_h - padding),
            'top-right': (w - text_w - padding, padding),
            'top-left': (padding, padding)
        }
        pos = position_map.get(position, position_map['center'])
        
        draw.text(pos, watermark_text, fill=(255, 255, 255, opacity), font=font)
        watermarked = Image.alpha_composite(img, overlay)
        watermarked = watermarked.convert('RGB')
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        watermarked.save(output_path)
        log.success(f"Watermark added: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Watermark failed: {e}")
        raise


def adjust_image(
    input_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
    output_path: Optional[str] = None
) -> str:
    """
    Adjust image brightness, contrast, saturation, and sharpness.
    Values: 1.0 = original, <1.0 = decrease, >1.0 = increase.
    
    Args:
        input_path: Source image path
        brightness: 0.0 (black) to 2.0+ (very bright), 1.0 = original
        contrast: 0.0 (gray) to 2.0+ (high contrast), 1.0 = original
        saturation: 0.0 (grayscale) to 2.0+, 1.0 = original
        sharpness: 0.0 (blur) to 2.0+ (sharp), 1.0 = original
        output_path: Output path
    
    Returns:
        Path to the adjusted image
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Image not found: {input_path}")
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.with_stem(p.stem + '_adjusted'))
    
    try:
        img = Image.open(input_path)
        
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        
        os.makedirs(Path(output_path).parent, exist_ok=True)
        img.save(output_path)
        log.success(f"Image adjusted and saved: {output_path}")
        return output_path
    
    except Exception as e:
        log.error(f"Image adjustment failed: {e}")
        raise
```

---

## STEP 8 — CREATE `tools/salesforce_tools.py`

```python
"""
Salesforce integration tools using simple-salesforce.
Provides: query, create, update, delete, describe, and metadata operations.
"""
import os
from typing import Optional, Dict, Any, List
from simple_salesforce import Salesforce, SalesforceLogin, SFType
from simple_salesforce.exceptions import SalesforceError
from utils.logger import log


class SalesforceClient:
    """
    Salesforce client wrapper with authentication and CRUD operations.
    Uses environment variables for credentials.
    """
    
    def __init__(self):
        """Initialize Salesforce client from environment variables."""
        self.sf: Optional[Salesforce] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish Salesforce connection using env credentials."""
        username = os.getenv("SF_USERNAME")
        password = os.getenv("SF_PASSWORD")
        security_token = os.getenv("SF_SECURITY_TOKEN")
        domain = os.getenv("SF_DOMAIN", "login")
        
        if not all([username, password, security_token]):
            log.warning("Salesforce credentials not configured. Set SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN in .env")
            return
        
        try:
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            log.success(f"Connected to Salesforce as {username}")
        except SalesforceError as e:
            log.error(f"Salesforce connection failed: {e}")
            raise
    
    def execute_soql(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SOQL query and return results.
        
        Args:
            query: Valid SOQL query string
        
        Returns:
            List of record dictionaries
        
        Example:
            results = sf_client.execute_soql("SELECT Id, Name FROM Account LIMIT 10")
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce")
        
        try:
            log.info(f"Executing SOQL: {query}")
            result = self.sf.query_all(query)
            records = result.get('records', [])
            log.success(f"SOQL returned {len(records)} records")
            return records
        except SalesforceError as e:
            log.error(f"SOQL query failed: {e}")
            raise
    
    def create_record(self, object_name: str, data: Dict[str, Any]) -> str:
        """
        Create a new Salesforce record.
        
        Args:
            object_name: API name of the object (e.g., 'Account', 'Contact')
            data: Dict of field API names to values
        
        Returns:
            Salesforce record ID of created record
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce")
        
        try:
            sf_object = getattr(self.sf, object_name)
            result = sf_object.create(data)
            record_id = result.get('id')
            log.success(f"Created {object_name} record: {record_id}")
            return record_id
        except SalesforceError as e:
            log.error(f"Record creation failed: {e}")
            raise
    
    def update_record(self, object_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing Salesforce record.
        
        Args:
            object_name: API name of the object
            record_id: Salesforce record ID (18-char)
            data: Dict of field API names to new values
        
        Returns:
            True if update was successful
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce")
        
        try:
            sf_object = getattr(self.sf, object_name)
            sf_object.update(record_id, data)
            log.success(f"Updated {object_name} {record_id}")
            return True
        except SalesforceError as e:
            log.error(f"Record update failed: {e}")
            raise
    
    def describe_object(self, object_name: str) -> Dict[str, Any]:
        """
        Get field metadata for a Salesforce object.
        
        Args:
            object_name: API name of the Salesforce object
        
        Returns:
            Dict containing object metadata including all fields
        """
        if not self.sf:
            raise RuntimeError("Not connected to Salesforce")
        
        try:
            sf_object = getattr(self.sf, object_name)
            result = sf_object.describe()
            log.success(f"Described {object_name}: {len(result['fields'])} fields")
            return result
        except SalesforceError as e:
            log.error(f"Object describe failed: {e}")
            raise


# Global client instance
sf_client = SalesforceClient()
```

---

## STEP 9 — CREATE `tools/video_tools.py`

```python
"""
Social media content creation tools.
Generates complete scripts for Instagram Reels and YouTube videos.
"""
from typing import Dict, Any, Optional
from utils.logger import log


def create_instagram_reel_script(
    topic: str,
    duration_seconds: int = 30,
    niche: str = "general",
    tone: str = "engaging",
    include_hashtags: bool = True
) -> Dict[str, Any]:
    """
    Generate a complete Instagram Reel script package.
    
    Args:
        topic: The topic or subject of the reel
        duration_seconds: Target duration (15, 30, 60, or 90 seconds)
        niche: Content niche (tech, business, lifestyle, education, etc.)
        tone: Tone of voice (engaging, professional, funny, motivational)
        include_hashtags: Whether to include hashtag suggestions
    
    Returns:
        Dict containing: hook, script, voiceover, caption, hashtags, b_roll_ideas
    """
    log.info(f"Generating Instagram Reel script for: {topic}")
    
    # This structure is returned to the Claude agent to fill with content
    return {
        "topic": topic,
        "duration": duration_seconds,
        "niche": niche,
        "tone": tone,
        "structure": {
            "hook": f"First 3 seconds — attention-grabbing hook about {topic}",
            "intro": "Seconds 4-8 — introduce yourself and the value of this video",
            "main_content": f"Seconds 9-{duration_seconds - 8} — core content about {topic}",
            "cta": f"Last 5 seconds — call to action"
        },
        "format": "vertical 9:16",
        "recommended_music": "trending audio from Instagram Reels library",
        "instructions": f"Generate a complete {duration_seconds}-second {tone} reel script about '{topic}' for a {niche} audience. Include: 1) Hook line, 2) Full voiceover script, 3) Text overlay suggestions, 4) Visual/B-roll ideas for each segment, 5) Instagram caption, 6) 30 relevant hashtags"
    }


def create_youtube_video_package(
    topic: str,
    video_length_minutes: int = 10,
    video_style: str = "tutorial",
    target_audience: str = "general",
    channel_niche: str = "technology"
) -> Dict[str, Any]:
    """
    Generate a complete YouTube video content package.
    
    Args:
        topic: Video topic
        video_length_minutes: Target video length
        video_style: Style (tutorial, vlog, review, explainer, storytime)
        target_audience: Target viewer demographic
        channel_niche: Channel's main niche
    
    Returns:
        Dict containing: title_options, description, script, chapters, tags, thumbnail_ideas
    """
    log.info(f"Generating YouTube video package for: {topic}")
    
    return {
        "topic": topic,
        "length_minutes": video_length_minutes,
        "style": video_style,
        "audience": target_audience,
        "niche": channel_niche,
        "deliverables": [
            "5 SEO-optimized title options",
            "Full video description with keywords",
            f"Complete {video_length_minutes}-minute script with timestamps",
            "Chapter markers",
            "30 SEO tags",
            "3 thumbnail concept descriptions",
            "End screen suggestions",
            "Pinned comment template"
        ],
        "instructions": f"Generate a complete YouTube video package for a {video_length_minutes}-minute {video_style} about '{topic}' targeting {target_audience} in the {channel_niche} niche."
    }
```

---

## STEP 10 — CREATE `tools/code_tools.py`

```python
"""
Code execution and debugging tools.
Safely executes Python code in a subprocess sandbox.
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import log


def execute_python_code(
    code: str,
    timeout_seconds: int = 30,
    capture_output: bool = True
) -> Dict[str, Any]:
    """
    Safely execute Python code in a subprocess sandbox.
    
    Args:
        code: Python code string to execute
        timeout_seconds: Maximum execution time
        capture_output: Whether to capture stdout/stderr
    
    Returns:
        Dict with: success, stdout, stderr, return_code, execution_time
    """
    log.info("Executing Python code in sandbox...")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        import time
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=capture_output,
            text=True,
            timeout=timeout_seconds
        )
        
        execution_time = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "execution_time_seconds": round(execution_time, 3)
        }
    
    except subprocess.TimeoutExpired:
        log.warning(f"Code execution timed out after {timeout_seconds}s")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds",
            "return_code": -1,
            "execution_time_seconds": timeout_seconds
        }
    
    except Exception as e:
        log.error(f"Code execution error: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "execution_time_seconds": 0
        }
    
    finally:
        os.unlink(temp_file)


def analyze_code_for_bugs(code: str, language: str = "python") -> str:
    """
    Prepare code for Claude to analyze for bugs.
    Returns a structured prompt for the AI to analyze.
    
    Args:
        code: Source code to analyze
        language: Programming language
    
    Returns:
        Formatted analysis request string
    """
    return f"""
Perform a comprehensive code review and bug analysis for the following {language} code.

Identify and explain:
1. **Bugs** — Logic errors, runtime exceptions, edge cases
2. **Security Issues** — SQL injection, XSS, insecure inputs, etc.
3. **Performance Issues** — Inefficient loops, memory leaks, N+1 queries
4. **Code Quality** — Missing error handling, poor naming, code smells
5. **Best Practice Violations** — Language-specific standards

For each issue, provide:
- Line number (if applicable)
- Issue description
- Severity: Critical / High / Medium / Low
- Fixed code snippet

Code to analyze:
```{language}
{code}
```

After the analysis, provide the complete corrected version of the code.
"""
```

---

## STEP 11 — CREATE `agent/core.py`

```python
"""
Core agent brain — manages Claude API interaction, tool calling, and response handling.
This is the central orchestrator of the entire agent.
"""
import os
import json
from typing import List, Dict, Any, Optional
import anthropic
from agent.system_prompt import MASTER_SYSTEM_PROMPT
from tools.pdf_tools import convert_any_to_pdf, convert_image_to_pdf
from tools.document_tools import modify_word_document, modify_excel_file
from tools.image_tools import resize_image, convert_image_format, add_watermark, adjust_image
from tools.code_tools import execute_python_code, analyze_code_for_bugs
from tools.salesforce_tools import sf_client
from tools.video_tools import create_instagram_reel_script, create_youtube_video_package
from utils.logger import log


# ─────────────────────────────────────────────
# TOOL DEFINITIONS (passed to Claude API)
# ─────────────────────────────────────────────

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "convert_to_pdf",
        "description": "Convert any file (docx, xlsx, pptx, txt, md, csv, html, jpg, png, gif, bmp, tiff, webp) to PDF format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the file to convert"},
                "output_path": {"type": "string", "description": "Optional output PDF path"}
            },
            "required": ["input_path"]
        }
    },
    {
        "name": "modify_document",
        "description": "Modify a Word (.docx) or Excel (.xlsx) document. Supports find/replace text and cell updates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the document"},
                "document_type": {"type": "string", "enum": ["word", "excel"], "description": "Type of document"},
                "replacements": {"type": "object", "description": "For Word: {old_text: new_text} dict"},
                "cell_updates": {"type": "object", "description": "For Excel: {cell_address: value} dict"},
                "sheet_name": {"type": "string", "description": "Excel sheet name (optional)"},
                "output_path": {"type": "string", "description": "Output path (modifies in place if omitted)"}
            },
            "required": ["input_path", "document_type"]
        }
    },
    {
        "name": "modify_image",
        "description": "Modify an image: resize, convert format, add watermark, or adjust brightness/contrast/saturation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the image"},
                "operation": {
                    "type": "string",
                    "enum": ["resize", "convert_format", "add_watermark", "adjust"],
                    "description": "Operation to perform"
                },
                "width": {"type": "integer", "description": "For resize: target width"},
                "height": {"type": "integer", "description": "For resize: target height"},
                "target_format": {"type": "string", "description": "For convert_format: PNG, JPEG, WEBP, BMP"},
                "watermark_text": {"type": "string", "description": "For add_watermark: text to use"},
                "brightness": {"type": "number", "description": "For adjust: 1.0 = original"},
                "contrast": {"type": "number", "description": "For adjust: 1.0 = original"},
                "saturation": {"type": "number", "description": "For adjust: 1.0 = original"},
                "output_path": {"type": "string", "description": "Output path (auto-generated if omitted)"}
            },
            "required": ["input_path", "operation"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute Python code safely in a sandbox and return the output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout_seconds": {"type": "integer", "description": "Max execution time (default 30)"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "salesforce_query",
        "description": "Execute a SOQL query against Salesforce and return results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "soql": {"type": "string", "description": "Valid SOQL query string"}
            },
            "required": ["soql"]
        }
    },
    {
        "name": "create_video_content",
        "description": "Generate a complete content package for Instagram Reels or YouTube videos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["instagram_reel", "youtube"], "description": "Target platform"},
                "topic": {"type": "string", "description": "Video topic"},
                "duration_seconds": {"type": "integer", "description": "For Instagram: target duration"},
                "video_length_minutes": {"type": "integer", "description": "For YouTube: video length"},
                "niche": {"type": "string", "description": "Content niche"},
                "tone": {"type": "string", "description": "Tone of voice"}
            },
            "required": ["platform", "topic"]
        }
    }
]


# ─────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Execute a tool by name with provided inputs.
    Routes tool calls to the correct implementation.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
    
    Returns:
        String result of the tool execution
    """
    log.info(f"Executing tool: {tool_name} with inputs: {list(tool_input.keys())}")
    
    try:
        if tool_name == "convert_to_pdf":
            result = convert_any_to_pdf(
                input_path=tool_input["input_path"],
                output_path=tool_input.get("output_path")
            )
            return f"✅ Successfully converted to PDF: {result}"
        
        elif tool_name == "modify_document":
            doc_type = tool_input["document_type"]
            if doc_type == "word":
                result = modify_word_document(
                    input_path=tool_input["input_path"],
                    replacements=tool_input.get("replacements", {}),
                    output_path=tool_input.get("output_path")
                )
                return f"✅ Word document modified: {result}"
            elif doc_type == "excel":
                result = modify_excel_file(
                    input_path=tool_input["input_path"],
                    cell_updates=tool_input.get("cell_updates", {}),
                    sheet_name=tool_input.get("sheet_name"),
                    output_path=tool_input.get("output_path")
                )
                return f"✅ Excel file modified: {result}"
        
        elif tool_name == "modify_image":
            op = tool_input["operation"]
            input_path = tool_input["input_path"]
            output_path = tool_input.get("output_path")
            
            if op == "resize":
                result = resize_image(input_path, tool_input["width"], tool_input["height"], output_path)
            elif op == "convert_format":
                result = convert_image_format(input_path, tool_input["target_format"], output_path)
            elif op == "add_watermark":
                result = add_watermark(input_path, tool_input["watermark_text"], output_path)
            elif op == "adjust":
                result = adjust_image(
                    input_path,
                    brightness=tool_input.get("brightness", 1.0),
                    contrast=tool_input.get("contrast", 1.0),
                    saturation=tool_input.get("saturation", 1.0),
                    output_path=output_path
                )
            return f"✅ Image modified ({op}): {result}"
        
        elif tool_name == "execute_code":
            result = execute_python_code(
                code=tool_input["code"],
                timeout_seconds=tool_input.get("timeout_seconds", 30)
            )
            return json.dumps(result, indent=2)
        
        elif tool_name == "salesforce_query":
            records = sf_client.execute_soql(tool_input["soql"])
            return json.dumps(records, indent=2, default=str)
        
        elif tool_name == "create_video_content":
            platform = tool_input["platform"]
            if platform == "instagram_reel":
                result = create_instagram_reel_script(
                    topic=tool_input["topic"],
                    duration_seconds=tool_input.get("duration_seconds", 30),
                    niche=tool_input.get("niche", "general"),
                    tone=tool_input.get("tone", "engaging")
                )
            else:
                result = create_youtube_video_package(
                    topic=tool_input["topic"],
                    video_length_minutes=tool_input.get("video_length_minutes", 10),
                    channel_niche=tool_input.get("niche", "general")
                )
            return json.dumps(result, indent=2)
        
        else:
            return f"❌ Unknown tool: {tool_name}"
    
    except Exception as e:
        log.error(f"Tool execution failed [{tool_name}]: {e}")
        return f"❌ Tool error: {str(e)}"


# ─────────────────────────────────────────────
# MAIN AGENT LOOP
# ─────────────────────────────────────────────

class AIAgent:
    """
    Main AI Agent class that orchestrates Claude API calls and tool execution.
    Implements the full agentic loop with tool use.
    """
    
    def __init__(self):
        """Initialize the AI Agent with Anthropic client."""
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-6"
        self.max_tokens = 8096
        self.conversation_history: List[Dict[str, Any]] = []
        log.success("AI Agent initialized")
    
    def chat(self, user_message: str, uploaded_file_path: Optional[str] = None) -> str:
        """
        Process a user message and return the agent's response.
        Handles multi-turn conversation with tool use.
        
        Args:
            user_message: The user's input message
            uploaded_file_path: Optional path to an uploaded file
        
        Returns:
            Agent's final response string
        """
        # Build user message content
        if uploaded_file_path:
            user_content = f"{user_message}\n\n[Uploaded file available at: {uploaded_file_path}]"
        else:
            user_content = user_message
        
        self.conversation_history.append({
            "role": "user",
            "content": user_content
        })
        
        log.info(f"Processing: {user_message[:100]}...")
        
        # Agentic loop — keeps running until Claude stops using tools
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=MASTER_SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.conversation_history
            )
            
            log.debug(f"Claude stop reason: {response.stop_reason}")
            
            # If Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Add Claude's response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Execute all tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        log.info(f"Tool called: {block.name}")
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                
                # Add tool results to history and continue loop
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
            
            # If Claude is done (end_turn), extract final response
            elif response.stop_reason == "end_turn":
                final_response = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_response += block.text
                
                # Add to history for multi-turn memory
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                log.success("Agent response complete")
                return final_response
            
            else:
                log.warning(f"Unexpected stop reason: {response.stop_reason}")
                return "An unexpected error occurred. Please try again."
    
    def reset_conversation(self) -> None:
        """Clear conversation history to start a fresh session."""
        self.conversation_history = []
        log.info("Conversation history cleared")
```

---

## STEP 12 — CREATE `main.py` (Streamlit UI)

```python
"""
Main entry point — Streamlit-based chat UI for the AI Agent.
Run with: streamlit run main.py
"""
import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from agent.core import AIAgent
from utils.logger import log

# Load environment variables
load_dotenv()

# Ensure required directories exist
for dir_name in ["uploads", "outputs", "logs"]:
    Path(dir_name).mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="APEX AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "agent" not in st.session_state:
    st.session_state.agent = AIAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("🤖 APEX Agent")
    st.caption("Multi-Capability AI Agent")
    
    st.markdown("---")
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader(
        "Upload a file to work with",
        type=['pdf', 'docx', 'xlsx', 'pptx', 'txt', 'md', 'csv',
              'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'html', 'py',
              'js', 'ts', 'java', 'cs', 'cpp', 'go', 'rs']
    )
    
    if uploaded_file:
        file_path = f"uploads/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file_path = file_path
        st.success(f"✅ {uploaded_file.name} uploaded")
        log.info(f"File uploaded: {file_path}")
    
    st.markdown("---")
    st.subheader("⚡ Quick Commands")
    
    quick_commands = [
        "Convert uploaded file to PDF",
        "Debug the uploaded code file",
        "Write a Salesforce Apex trigger",
        "Create an Instagram Reel script",
        "Create a YouTube video script",
        "Resize the uploaded image to 800x600",
        "Add watermark to uploaded image",
        "Write Python code to sort a list",
        "Explain Salesforce governor limits",
    ]
    
    for cmd in quick_commands:
        if st.button(cmd, use_container_width=True):
            st.session_state.quick_command = cmd
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.reset_conversation()
        st.rerun()
    
    st.markdown("---")
    st.subheader("🎯 Capabilities")
    capabilities = [
        "💬 Q&A on any topic",
        "💻 Code in any language",
        "☁️ Salesforce expert",
        "📄 Document modification",
        "🖼️ Image editing",
        "📑 Any file → PDF",
        "🎬 Instagram Reels",
        "▶️ YouTube videos",
        "🐛 Code debugging",
    ]
    for cap in capabilities:
        st.markdown(f"• {cap}")

# ─────────────────────────────────────────────
# MAIN CHAT UI
# ─────────────────────────────────────────────

st.title("🤖 APEX — Multi-Capability AI Agent")
st.caption("Ask me anything, upload files, write code, create content, and more.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle quick commands
if hasattr(st.session_state, 'quick_command') and st.session_state.quick_command:
    prompt = st.session_state.quick_command
    st.session_state.quick_command = None
else:
    prompt = st.chat_input("Ask APEX anything...")

# Process user input
if prompt:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("APEX is thinking..."):
            try:
                response = st.session_state.agent.chat(
                    user_message=prompt,
                    uploaded_file_path=st.session_state.uploaded_file_path
                )
                st.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                # Clear uploaded file after use
                st.session_state.uploaded_file_path = None
            
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                log.error(f"Agent error: {e}")
```

---

## STEP 13 — CREATE `utils/file_handler.py`

```python
"""
File handler utility — manages uploads, downloads, and temp file cleanup.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List
from utils.logger import log


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str = "uploads") -> str:
    """
    Save uploaded file content to the uploads directory.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        upload_dir: Directory to save in
    
    Returns:
        Full path to the saved file
    """
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    log.info(f"File saved: {file_path} ({len(file_content)} bytes)")
    return file_path


def get_output_path(input_path: str, suffix: str = "", new_extension: Optional[str] = None, output_dir: str = "outputs") -> str:
    """
    Generate an output file path based on the input path.
    
    Args:
        input_path: Original file path
        suffix: Suffix to add to filename (e.g., '_modified')
        new_extension: New file extension (e.g., '.pdf')
        output_dir: Output directory
    
    Returns:
        Generated output file path
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    p = Path(input_path)
    extension = new_extension if new_extension else p.suffix
    new_name = f"{p.stem}{suffix}{extension}"
    return os.path.join(output_dir, new_name)


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Remove files older than max_age_hours from directory.
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours
    
    Returns:
        Number of files deleted
    """
    import time
    deleted = 0
    cutoff = time.time() - (max_age_hours * 3600)
    
    for file_path in Path(directory).iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            file_path.unlink()
            deleted += 1
    
    if deleted > 0:
        log.info(f"Cleaned up {deleted} old files from {directory}")
    
    return deleted
```

---

## STEP 14 — CREATE `README.md`

```markdown
# 🤖 APEX — Multi-Capability AI Agent

A fully functional AI agent powered by Claude (claude-sonnet-4-6) with capabilities for:
- 💬 Q&A on any topic
- 💻 Code writing & debugging in any language
- ☁️ Salesforce expert (Apex, LWC, SOQL, integrations)
- 📄 Document modification (Word, Excel, PowerPoint)
- 🖼️ Image editing (resize, convert, watermark, adjust)
- 📑 Universal file → PDF conversion
- 🎬 Instagram Reel scripts
- ▶️ YouTube video packages

## Quick Start

### 1. Clone and set up environment
\`\`\`bash
git clone <your-repo-url>
cd ai-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

### 2. Configure environment
\`\`\`bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
\`\`\`

### 3. (Optional) Install LibreOffice for Office → PDF conversion
\`\`\`bash
# Ubuntu/Debian
sudo apt install libreoffice

# macOS
brew install libreoffice
\`\`\`

### 4. Run the agent
\`\`\`bash
streamlit run main.py
\`\`\`

Open http://localhost:8501 in your browser.

## Getting Your Anthropic API Key
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key and copy it to your .env file

## Project Structure
See the folder structure in the copilot-instructions.md file.

## Environment Variables
See `.env.example` for all configurable options.
```

---

## STEP 15 — CREATE `.gitignore`

```gitignore
# Environment
.env
*.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv/

# Working directories
uploads/
outputs/
logs/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## FINAL SETUP COMMANDS

Run these commands in order in the VS Code terminal:

```bash
# 1. Create project folder and navigate into it
mkdir ai-agent && cd ai-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# OR: venv\Scripts\activate     # Windows

# 3. Create folder structure
mkdir -p agent tools utils tests uploads outputs logs .github

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Set up environment
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY

# 6. (Optional) Install LibreOffice for Office → PDF
# Ubuntu: sudo apt install libreoffice
# macOS:  brew install libreoffice

# 7. Create all __init__.py files
touch agent/__init__.py tools/__init__.py utils/__init__.py tests/__init__.py

# 8. Run the agent
streamlit run main.py
```

---

## COPILOT GENERATION ORDER

When using GitHub Copilot to generate code, always generate files in this exact order:

1. `requirements.txt`
2. `.env.example`
3. `utils/logger.py`
4. `agent/system_prompt.py`
5. `tools/pdf_tools.py`
6. `tools/document_tools.py`
7. `tools/image_tools.py`
8. `tools/code_tools.py`
9. `tools/salesforce_tools.py`
10. `tools/video_tools.py`
11. `utils/file_handler.py`
12. `agent/core.py`
13. `main.py`
14. `README.md`

Each file depends on the ones before it. Always generate in this order to avoid import errors.

---

## TESTING CHECKLIST

After setup, test each capability:

- [ ] `Convert this image to PDF` + upload a .jpg → should produce .pdf
- [ ] `Convert this Word doc to PDF` + upload a .docx → should produce .pdf
- [ ] `Resize this image to 800x600` + upload an image
- [ ] `Add a watermark to this image` + upload an image
- [ ] `Write a Python function to sort a list` → should give working code
- [ ] `Debug this code` + paste broken code
- [ ] `Write a Salesforce Apex trigger for Account` 
- [ ] `Create a 30-second Instagram Reel script about AI`
- [ ] `Create a YouTube video script about Salesforce basics`
- [ ] `What is a SOQL query?`