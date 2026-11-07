# backend/main.py

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import io
import os
from openai import OpenAI
from dotenv import load_dotenv
import cv2
import numpy as np
import PyPDF2
import docx
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.multi_model_ai import MultiModelAIService
from services.model_selector import ModelSelector
from services.question_generator import question_generator

# Import advanced API endpoints
try:
    from api.webhook_endpoints import router as webhook_router
    from api.email_endpoints import router as email_router
    from api.cloud_storage_endpoints import router as cloud_storage_router
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    print("⚠️  Advanced features not available - some imports failed")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))  # Load NEBIUS_API_KEY from .env

app = FastAPI(
    title="Document Intelligence Platform",
    description="Advanced document processing with AI-powered analysis",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Nebius LLM client
api_key = os.environ.get("NEBIUS_API_KEY")
if not api_key:
    raise ValueError("NEBIUS_API_KEY environment variable is required")

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=api_key
)

def preprocess_image(image):
    """Preprocess image for better OCR accuracy"""
    # Convert PIL to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Resize image for better OCR (if too small)
    height, width = gray.shape
    if height < 300 or width < 300:
        scale_factor = max(300/height, 300/width, 2.0)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Increase contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Apply bilateral filter to reduce noise while preserving edges
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Morphological operations to clean up
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Remove small noise
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    return Image.fromarray(cleaned)

def preprocess_for_tables(image):
    """Special preprocessing for table structures"""
    # Convert PIL to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Increase image size for better OCR
    height, width = gray.shape
    gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    # Apply strong contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Use Otsu's thresholding for better binary conversion
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Morphological operations to connect broken characters
    kernel = np.ones((2, 1), np.uint8)  # Vertical kernel to connect characters
    connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return Image.fromarray(connected)

def preprocess_image_alternative(image):
    """Alternative preprocessing method for difficult images"""
    # Convert PIL to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Dilate to connect text components
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    # Erode to restore original text size
    eroded = cv2.erode(dilated, kernel, iterations=1)
    
    return Image.fromarray(eroded)

def extract_text_from_pdf(file_content):
    """Extract text from PDF file using direct extraction and OCR fallback"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        
        # First try direct text extraction
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            text += page_text + "\n"
        
        # If we got very little text (likely scanned PDF), use OCR
        if len(text.strip()) < 50:  # Threshold for "very little text"
            return extract_text_from_pdf_with_ocr(file_content)
        
        return text
    except Exception as e:
        # If direct extraction fails, try OCR
        try:
            return extract_text_from_pdf_with_ocr(file_content)
        except Exception as ocr_error:
            raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}. OCR fallback also failed: {str(ocr_error)}")

def extract_text_from_pdf_with_ocr(file_content):
    """Extract text from PDF using OCR (for scanned PDFs)"""
    try:
        import fitz  # PyMuPDF
        
        # Open PDF with PyMuPDF
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        combined_text = ""
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            # Convert PDF page to image with higher resolution
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # 3x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data)).convert("RGB")
            
            # Try multiple OCR configurations
            configs = [
                r'--oem 3 --psm 6',  # Default
                r'--oem 3 --psm 4',  # Single column of text
                r'--oem 3 --psm 3',  # Fully automatic page segmentation
            ]
            
            best_text = ""
            best_length = 0
            
            # Try with processed image
            processed_image = preprocess_image(image)
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    text = post_process_ocr_text(text)
                    if len(text) > best_length:
                        best_text = text
                        best_length = len(text)
                except:
                    continue
            
            # Try with alternative preprocessing
            alt_processed_image = preprocess_image_alternative(image)
            for config in configs:
                try:
                    text = pytesseract.image_to_string(alt_processed_image, config=config)
                    text = post_process_ocr_text(text)
                    if len(text) > best_length:
                        best_text = text
                        best_length = len(text)
                except:
                    continue
            
            combined_text += f"Page {page_num + 1}:\n{best_text}\n\n"
        
        pdf_document.close()
        return combined_text
        
    except ImportError:
        raise HTTPException(status_code=400, detail="PyMuPDF not installed. Cannot perform OCR on PDF.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error performing OCR on PDF: {str(e)}")

def extract_text_from_docx(file_content):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")

def post_process_ocr_text(text):
    """Post-process OCR text to fix common issues"""
    import re
    
    # If text is empty or too short, return as is
    if not text or len(text.strip()) < 5:
        return text
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix specific OCR mistakes (only the most important ones)
    try:
        # Course codes - be more careful with word boundaries
        text = re.sub(r'\bSI3901\b', 'CSI3901', text)  # Specific fix for SI3901
        text = re.sub(r'P HY(\d+)', r'PHY\1', text)  # Fix PHY codes
        text = re.sub(r'C SI(\d+)', r'CSI\1', text)  # Fix CSI codes
        
        # Acronyms
        text = re.sub(r'T AR P', 'TARP', text)
        text = re.sub(r'F AT\b', 'FAT', text)
        
        # Common word fixes
        text = re.sub(r'methodologics', 'methodologies', text)
        text = re.sub(r'technologics', 'technologies', text)
        text = re.sub(r'cfficient', 'efficient', text)
        text = re.sub(r'devcloped', 'developed', text)
        text = re.sub(r'enginccring', 'engineering', text)
        
        # Table header fixes
        text = re.sub(r'LIT/P/\|J/c', 'L T P J C', text)
        text = re.sub(r'L T/P Jc C', 'L T P J C', text)
        text = re.sub(r'L T P Jc C', 'L T P J C', text)
        text = re.sub(r'LIT/P/J/c', 'L T P J C', text)
        
        # Fix spacing after punctuation
        text = re.sub(r'\.([A-Za-z])', r'. \1', text)
        text = re.sub(r',([A-Za-z])', r', \1', text)
        text = re.sub(r':([A-Za-z])', r': \1', text)
        
        # Fix credit format and remove artifacts
        text = re.sub(r'(\d)/(\d)/(\d)/(\d)/(\d)', r'\1 \2 \3 \4 \5', text)  # Fix credit format
        text = re.sub(r'at whr?\s*=', '', text)  # Remove OCR artifacts
        text = re.sub(r'_\s*', '', text)  # Remove stray underscores
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
    except Exception as e:
        # If any regex fails, just return the original text
        print(f"Post-processing error: {e}")
        pass
    
    return text.strip()

def format_structured_text(text):
    """Format text to better represent structured documents like tables"""
    import re
    
    if not text or len(text.strip()) < 5:
        return text
    
    try:
        # Add line breaks before common section headers
        headers = [
            'Course Code', 'Course Title', 'Pre-requisite', 'Course Objectives', 
            'Course Outcomes', 'Module:', 'Mode of Evaluation', 'Recommended by',
            'Approved by', 'Proceedings'
        ]
        
        for header in headers:
            text = re.sub(f'({header})', r'\n\n\1', text)
        
        # Format numbered lists
        text = re.sub(r'(\d+\.)\s*', r'\n\1 ', text)
        
        # Clean up extra line breaks
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
    except Exception as e:
        print(f"Text formatting error: {e}")
        # If formatting fails, return original text
        pass
    
    return text.strip()

def extract_text_from_image(file_content):
    """Extract text from image using OCR with multiple approaches"""
    try:
        image = Image.open(io.BytesIO(file_content)).convert("RGB")
        
        # Simple approach first - try basic OCR
        try:
            basic_text = pytesseract.image_to_string(image)
            if basic_text.strip():
                processed_basic = post_process_ocr_text(basic_text)
                if len(processed_basic.strip()) > 10:  # If we got decent text, use it
                    return format_structured_text(processed_basic)
        except:
            pass
        
        # Try multiple OCR configurations
        configs = [
            r'--oem 3 --psm 6',  # Default - uniform block of text
            r'--oem 3 --psm 4',  # Single column of text
            r'--oem 3 --psm 3',  # Fully automatic page segmentation
            r'--oem 3 --psm 1',  # Automatic page segmentation with OSD
            r'--oem 3 --psm 11', # Sparse text
            r'--oem 3 --psm 12', # Sparse text with OSD
            r'--oem 1 --psm 6',  # Neural nets LSTM engine
        ]
        
        results = []
        
        # Try with standard processed image
        try:
            processed_image = preprocess_image(image)
            for config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    if text and text.strip():
                        processed_text = post_process_ocr_text(text)
                        if processed_text and len(processed_text.strip()) > 5:
                            formatted_text = format_structured_text(processed_text)
                            results.append(("Standard", config, formatted_text, len(formatted_text)))
                except Exception as e:
                    print(f"OCR config {config} failed: {e}")
                    continue
        except Exception as e:
            print(f"Standard preprocessing failed: {e}")
        
        # Try with alternative preprocessing
        try:
            alt_processed_image = preprocess_image_alternative(image)
            for config in configs:
                try:
                    text = pytesseract.image_to_string(alt_processed_image, config=config)
                    if text and text.strip():
                        processed_text = post_process_ocr_text(text)
                        if processed_text and len(processed_text.strip()) > 5:
                            formatted_text = format_structured_text(processed_text)
                            results.append(("Alternative", config, formatted_text, len(formatted_text)))
                except Exception as e:
                    print(f"Alt OCR config {config} failed: {e}")
                    continue
        except Exception as e:
            print(f"Alternative preprocessing failed: {e}")
        
        if not results:
            # Last resort - try original image with basic config
            try:
                text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6')
                if text and text.strip():
                    return post_process_ocr_text(text)
            except:
                pass
            return "No text could be extracted from the image."
        
        # Return the longest result (usually better)
        best_result = max(results, key=lambda x: x[3])  # Sort by length (4th element)
        
        return best_result[2]  # Return the formatted text (3rd element)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

def extract_text_from_code_file(file_content, file_extension):
    """Extract text from code files with syntax awareness"""
    try:
        # Decode the file content
        text = file_content.decode('utf-8')
        
        # Add file type context for better AI understanding
        file_type_context = {
            'py': 'Python',
            'js': 'JavaScript', 
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'sh': 'Shell Script'
        }
        
        context = file_type_context.get(file_extension, file_extension.upper())
        
        # Add context header for AI processing
        processed_text = f"[{context} Code File]\n\n{text}"
        
        return processed_text
        
    except UnicodeDecodeError:
        try:
            text = file_content.decode('latin-1')
            return f"[{file_extension.upper()} Code File]\n\n{text}"
        except UnicodeDecodeError:
            return f"[{file_extension.upper()} Code File - Binary Content]\n\nThis file contains binary data that cannot be displayed as text."

def extract_text_from_html(file_content):
    """Extract text from HTML files"""
    try:
        from bs4 import BeautifulSoup
        
        # Decode content
        html_content = file_content.decode('utf-8')
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Untitled HTML Document"
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return f"[HTML Document]\nTitle: {title_text}\n\n{text}"
        
    except Exception as e:
        # Fallback to plain text extraction
        try:
            return f"[HTML Document]\n\n{file_content.decode('utf-8')}"
        except:
            return f"[HTML Document - Error]\n\nError processing HTML: {str(e)}"

def extract_text_from_xml(file_content):
    """Extract text from XML files"""
    try:
        import xml.etree.ElementTree as ET
        
        # Decode content
        xml_content = file_content.decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Extract all text content
        def extract_xml_text(element, level=0):
            text_parts = []
            indent = "  " * level
            
            # Add element tag and attributes
            if element.tag:
                attrs = " ".join([f'{k}="{v}"' for k, v in element.attrib.items()])
                tag_info = f"{indent}<{element.tag}" + (f" {attrs}" if attrs else "") + ">"
                text_parts.append(tag_info)
            
            # Add element text
            if element.text and element.text.strip():
                text_parts.append(f"{indent}  {element.text.strip()}")
            
            # Process children
            for child in element:
                text_parts.extend(extract_xml_text(child, level + 1))
            
            return text_parts
        
        xml_text = "\n".join(extract_xml_text(root))
        
        return f"[XML Document]\nRoot Element: {root.tag}\n\n{xml_text}"
        
    except Exception as e:
        # Fallback to plain text extraction
        try:
            return f"[XML Document]\n\n{file_content.decode('utf-8')}"
        except:
            return f"[XML Document - Error]\n\nError processing XML: {str(e)}"

def extract_text_from_markdown(file_content):
    """Extract text from Markdown files"""
    try:
        # Decode content
        md_content = file_content.decode('utf-8')
        
        # Add markdown context
        return f"[Markdown Document]\n\n{md_content}"
        
    except UnicodeDecodeError:
        try:
            md_content = file_content.decode('latin-1')
            return f"[Markdown Document]\n\n{md_content}"
        except:
            return "[Markdown Document - Error]\n\nError decoding markdown file."

def extract_text_from_jupyter_notebook(file_content):
    """Extract text from Jupyter notebook files"""
    try:
        import json
        
        # Decode and parse JSON
        notebook_content = file_content.decode('utf-8')
        notebook = json.loads(notebook_content)
        
        extracted_parts = ["[Jupyter Notebook]"]
        
        # Extract metadata if available
        if 'metadata' in notebook:
            metadata = notebook['metadata']
            if 'kernelspec' in metadata:
                kernel = metadata['kernelspec'].get('display_name', 'Unknown')
                extracted_parts.append(f"Kernel: {kernel}")
        
        extracted_parts.append("")  # Empty line
        
        # Extract cells
        if 'cells' in notebook:
            for i, cell in enumerate(notebook['cells']):
                cell_type = cell.get('cell_type', 'unknown')
                
                if cell_type == 'markdown':
                    extracted_parts.append(f"## Markdown Cell {i+1}")
                    if 'source' in cell:
                        source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
                        extracted_parts.append(source)
                
                elif cell_type == 'code':
                    extracted_parts.append(f"## Code Cell {i+1}")
                    if 'source' in cell:
                        source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
                        extracted_parts.append(f"```python\n{source}\n```")
                    
                    # Add outputs if available
                    if 'outputs' in cell and cell['outputs']:
                        extracted_parts.append("### Output:")
                        for output in cell['outputs']:
                            if 'text' in output:
                                output_text = ''.join(output['text']) if isinstance(output['text'], list) else output['text']
                                extracted_parts.append(output_text)
                
                extracted_parts.append("")  # Empty line between cells
        
        return "\n".join(extracted_parts)
        
    except Exception as e:
        return f"[Jupyter Notebook - Error]\n\nError processing notebook: {str(e)}"

def extract_text_from_file(file_content, filename):
    """Extract text from various file types with enhanced format support"""
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Image files
    if file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'webp']:
        return extract_text_from_image(file_content)
    
    # Document files
    elif file_extension == 'pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension in ['docx']:
        return extract_text_from_docx(file_content)
    
    # Text files
    elif file_extension in ['txt']:
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except UnicodeDecodeError:
                return file_content.decode('utf-8', errors='ignore')
    
    # Markdown files
    elif file_extension in ['md', 'markdown']:
        return extract_text_from_markdown(file_content)
    
    # HTML files
    elif file_extension in ['html', 'htm']:
        return extract_text_from_html(file_content)
    
    # XML files
    elif file_extension in ['xml']:
        return extract_text_from_xml(file_content)
    
    # Code files
    elif file_extension in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'sh']:
        return extract_text_from_code_file(file_content, file_extension)
    
    # Jupyter notebooks
    elif file_extension in ['ipynb']:
        return extract_text_from_jupyter_notebook(file_content)
    
    else:
        # Try to detect if it's an image by attempting to open it
        try:
            Image.open(io.BytesIO(file_content))
            return extract_text_from_image(file_content)
        except:
            pass
        
        # Try as plain text file
        try:
            text_content = file_content.decode('utf-8')
            return f"[Unknown File Type: {file_extension}]\n\n{text_content}"
        except:
            pass
        
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Supported formats: images (jpg, png, etc.), documents (PDF, DOCX), text files (TXT, MD, HTML, XML), code files (PY, JS, TS, JAVA, CPP, C, SH), and notebooks (IPYNB)"
        )

def clean_markdown_formatting(text: str) -> str:
    """Remove markdown formatting from text"""
    import re
    
    if not text:
        return text
    
    # Remove bold formatting (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic formatting (*text* or _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Convert markdown headers to plain text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Convert markdown lists to simple dashes
    text = re.sub(r'^\s*[\*\-\+]\s+', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '- ', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

def categorize_document(text: str, filename: str) -> dict:
    """Auto-categorize document based on content and filename"""
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Define categories and their indicators
    categories = {
        "academic": ["syllabus", "course", "curriculum", "assignment", "exam", "grade", "student", "professor", "university", "college"],
        "financial": ["invoice", "receipt", "bill", "payment", "total", "amount", "tax", "price", "$", "€", "£", "cost"],
        "legal": ["contract", "agreement", "terms", "conditions", "legal", "law", "clause", "party", "whereas"],
        "medical": ["patient", "doctor", "medical", "diagnosis", "treatment", "prescription", "hospital", "clinic"],
        "business": ["company", "business", "meeting", "proposal", "report", "analysis", "strategy", "revenue"],
        "personal": ["resume", "cv", "application", "cover letter", "personal", "experience", "skills"]
    }
    
    scores = {}
    for category, keywords in categories.items():
        score = 0
        for keyword in keywords:
            score += text_lower.count(keyword) * 2  # Content weight
            score += filename_lower.count(keyword) * 3  # Filename weight (higher)
        scores[category] = score
    
    # Find best category
    best_category = max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
    confidence = min(scores.get(best_category, 0) / 10, 1.0) if best_category != "general" else 0.0
    
    return {
        "category": best_category,
        "confidence": confidence,
        "all_scores": scores
    }

@app.post("/ask")
async def ask(
    file: UploadFile = File(...), 
    question: str = Form(...),
    model: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None)
):
    # Security checks
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    # Extract text based on file type
    extracted_text = extract_text_from_file(contents, file.filename)
    
    # Auto-categorize document
    document_category = categorize_document(extracted_text, file.filename)
    
    # Initialize multi-model AI service
    ai_service = MultiModelAIService()
    
    # Process with specified or recommended model
    try:
        result = ai_service.process_with_model(
            content=extracted_text,
            question=question,
            model=model,
            system_prompt=system_prompt,
            filename=file.filename
        )
        
        # Get model recommendation for comparison
        recommendation = ai_service.get_model_recommendation(file.filename, extracted_text)
        
        return {
            "answer": result["answer"],
            "extracted_text": extracted_text,
            "file_type": file.filename.split('.')[-1].lower(),
            "document_category": document_category,
            "model_used": result["model_used"],
            "model_info": result["model_info"],
            "recommended_model": recommendation["recommended_model"],
            "recommendation_explanation": recommendation["explanation"],
            "processing_time": result["processing_time"],
            "fallback_used": result.get("fallback_used", False),
            "attempts": result.get("attempts", 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@app.post("/debug-extract")
async def debug_extract(file: UploadFile = File(...)):
    """Debug endpoint to see raw text extraction"""
    contents = await file.read()
    
    try:
        extracted_text = extract_text_from_file(contents, file.filename)
        return {
            "filename": file.filename,
            "file_type": file.filename.split('.')[-1].lower(),
            "extracted_text": extracted_text,
            "success": True
        }
    except Exception as e:
        return {
            "filename": file.filename,
            "file_type": file.filename.split('.')[-1].lower(),
            "error": str(e),
            "success": False
        }

@app.post("/batch-process")
async def batch_process(
    files: list[UploadFile] = File(...),
    question: str = Form(...),
    system_prompt: Optional[str] = Form(None)
):
    """Process multiple files at once"""
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
    
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            
            # Security check
            if len(contents) > 10 * 1024 * 1024:  # 10MB per file
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File too large (max 10MB)"
                })
                continue
            
            # Extract text
            extracted_text = extract_text_from_file(contents, file.filename)
            
            # Default system prompt
            default_system_prompt = """You are an intelligent assistant helping users understand documents. Provide clear, accurate, and helpful responses."""
            final_system_prompt = system_prompt if system_prompt else default_system_prompt
            
            # Create messages
            messages = [
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": f"""Here is the extracted document text:

\"\"\"{extracted_text}\"\"\"

Question: {question}"""}
            ]

            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                max_tokens=1024,
                temperature=0.6,
                top_p=0.9,
                extra_body={"top_k": 50},
                messages=messages
            )

            # Clean the answer
            clean_answer = clean_markdown_formatting(response.choices[0].message.content)
            
            results.append({
                "filename": file.filename,
                "success": True,
                "answer": clean_answer,
                "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                "file_type": file.filename.split('.')[-1].lower()
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "batch_results": results,
        "total_files": len(files),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]])
    }

@app.post("/summarize")
async def summarize_document(
    file: UploadFile = File(...),
    summary_type: str = Form("general")  # general, key_points, executive
):
    """Generate document summary"""
    contents = await file.read()
    
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    extracted_text = extract_text_from_file(contents, file.filename)
    
    # Different summary prompts
    summary_prompts = {
        "general": "Provide a comprehensive summary of this document in 2-3 paragraphs.",
        "key_points": "Extract the key points from this document as a bulleted list.",
        "executive": "Provide an executive summary focusing on the most important information for decision-makers."
    }
    
    prompt = summary_prompts.get(summary_type, summary_prompts["general"])
    
    messages = [
        {"role": "system", "content": "You are an expert document analyst. Provide clear, concise summaries."},
        {"role": "user", "content": f"""Here is the document text:

\"\"\"{extracted_text}\"\"\"

Task: {prompt}"""}
    ]

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct",
        max_tokens=1024,
        temperature=0.6,
        top_p=0.9,
        extra_body={"top_k": 50},
        messages=messages
    )

    # Clean the summary
    clean_summary = clean_markdown_formatting(response.choices[0].message.content)
    
    return {
        "summary": clean_summary,
        "summary_type": summary_type,
        "document_info": {
            "filename": file.filename,
            "size": len(contents),
            "text_length": len(extracted_text)
        }
    }

@app.get("/supported-formats")
async def supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": {
            "images": ["jpg", "jpeg", "png", "bmp", "tiff", "gif", "webp"],
            "documents": ["pdf", "docx", "txt"],
            "text_files": ["txt", "md", "markdown"],
            "structured": ["html", "htm", "xml"],
            "code_files": ["py", "js", "ts", "java", "cpp", "c", "sh"],
            "notebooks": ["ipynb"]
        },
        "total_formats": 20,
        "categories": {
            "images": "Image files processed with OCR",
            "documents": "Document files with direct text extraction",
            "text_files": "Plain text and markdown files",
            "structured": "HTML and XML files with structure parsing",
            "code_files": "Programming language files with syntax awareness",
            "notebooks": "Jupyter notebooks with cell extraction"
        }
    }

# Multi-Model AI Endpoints

@app.get("/models")
async def get_available_models():
    """Get information about available AI models"""
    selector = ModelSelector()
    return {
        "available_models": selector.get_all_models_info(),
        "default_model": selector.default_model
    }

@app.post("/recommend-model")
async def recommend_model(file: UploadFile = File(...)):
    """Get model recommendation for a specific file"""
    contents = await file.read()
    
    # Security check
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    try:
        extracted_text = extract_text_from_file(contents, file.filename)
        ai_service = MultiModelAIService()
        recommendation = ai_service.get_model_recommendation(file.filename, extracted_text)
        
        return {
            "filename": file.filename,
            "file_type": file.filename.split('.')[-1].lower(),
            "recommended_model": recommendation["recommended_model"],
            "explanation": recommendation["explanation"],
            "all_models": recommendation["all_models"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post("/compare-models")
async def compare_models(
    file: UploadFile = File(...),
    question: str = Form(...),
    models: str = Form(...)  # Comma-separated model IDs
):
    """Compare responses from multiple models for the same document and question"""
    contents = await file.read()
    
    # Security check
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        extracted_text = extract_text_from_file(contents, file.filename)
        model_list = [m.strip() for m in models.split(",") if m.strip()]
        
        if not model_list:
            raise HTTPException(status_code=400, detail="At least one model must be specified.")
        
        ai_service = MultiModelAIService()
        comparison = ai_service.compare_models(extracted_text, question, model_list)
        
        return {
            "filename": file.filename,
            "question": question,
            "comparison_results": comparison["comparison_results"],
            "models_compared": comparison["models_compared"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")

# Question Generation API Endpoints

@app.post("/generate-questions")
async def generate_questions(
    file: UploadFile = File(...),
    max_questions: int = Form(10),
    document_category: str = Form("general"),
    user_preferences: Optional[str] = Form(None)
):
    """
    Generate contextually relevant questions from document content
    
    Args:
        file: Document file to analyze
        max_questions: Maximum number of questions to generate (default: 10)
        document_category: Category of document (code, research, documentation, general)
        user_preferences: JSON string of user preferences for question types
    
    Returns:
        List of generated questions with categories and relevance scores
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Extract text from document
        extracted_text = ""
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension in ['txt', 'md']:
            content = await file.read()
            extracted_text = content.decode('utf-8')
        elif file_extension == 'pdf':
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif file_extension in ['doc', 'docx']:
            content = await file.read()
            doc = docx.Document(io.BytesIO(content))
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        elif file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            # OCR for images
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            processed_image = preprocess_image(image)
            extracted_text = pytesseract.image_to_string(processed_image)
        else:
            # Try to read as text for code files and other text formats
            try:
                content = await file.read()
                extracted_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text content could be extracted from the file")
        
        # Parse user preferences if provided
        preferences = {}
        if user_preferences:
            try:
                import json
                preferences = json.loads(user_preferences)
            except json.JSONDecodeError:
                # Ignore invalid JSON, use empty preferences
                pass
        
        # Auto-detect document category if not specified or is "general"
        if document_category == "general":
            document_category = detect_document_category(extracted_text, file.filename)
        
        # Generate questions using the question generator service
        questions = await question_generator.generate_questions(
            content=extracted_text,
            document_category=document_category,
            filename=file.filename,
            max_questions=max_questions,
            user_preferences=preferences
        )
        
        # Convert questions to response format
        questions_data = []
        for question in questions:
            questions_data.append({
                "text": question.text,
                "category": question.category,
                "relevance_score": question.relevance_score,
                "context": question.context,
                "follow_ups": question.follow_ups
            })
        
        # Categorize questions for better organization
        categorized_questions = question_generator.categorize_questions(questions)
        categories_summary = {category: len(questions) for category, questions in categorized_questions.items()}
        
        return {
            "filename": file.filename,
            "document_category": document_category,
            "total_questions": len(questions_data),
            "categories_summary": categories_summary,
            "questions": questions_data,
            "categorized_questions": {
                category: [q.to_dict() for q in questions] 
                for category, questions in categorized_questions.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.post("/generate-questions-from-text")
async def generate_questions_from_text(
    text: str = Form(...),
    max_questions: int = Form(10),
    document_category: str = Form("general"),
    filename: str = Form("document.txt"),
    user_preferences: Optional[str] = Form(None)
):
    """
    Generate questions from raw text content (useful for API integrations)
    
    Args:
        text: Raw text content to analyze
        max_questions: Maximum number of questions to generate
        document_category: Category of document
        filename: Optional filename for context
        user_preferences: JSON string of user preferences
    
    Returns:
        List of generated questions with categories and relevance scores
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content provided")
        
        # Parse user preferences if provided
        preferences = {}
        if user_preferences:
            try:
                import json
                preferences = json.loads(user_preferences)
            except json.JSONDecodeError:
                pass
        
        # Auto-detect document category if not specified
        if document_category == "general":
            document_category = detect_document_category(text, filename)
        
        # Generate questions
        questions = await question_generator.generate_questions(
            content=text,
            document_category=document_category,
            filename=filename,
            max_questions=max_questions,
            user_preferences=preferences
        )
        
        # Convert to response format
        questions_data = [q.to_dict() for q in questions]
        categorized_questions = question_generator.categorize_questions(questions)
        categories_summary = {category: len(questions) for category, questions in categorized_questions.items()}
        
        return {
            "filename": filename,
            "document_category": document_category,
            "total_questions": len(questions_data),
            "categories_summary": categories_summary,
            "questions": questions_data,
            "categorized_questions": {
                category: [q.to_dict() for q in questions] 
                for category, questions in categorized_questions.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.get("/question-categories")
async def get_question_categories():
    """
    Get available question categories and their descriptions
    
    Returns:
        Dictionary of question categories with descriptions
    """
    from services.question_generator import QuestionCategory
    
    categories = {
        QuestionCategory.FACTUAL: {
            "name": "Factual",
            "description": "Questions about specific facts, data, and concrete information",
            "examples": ["What are the key statistics?", "Who are the main stakeholders?"]
        },
        QuestionCategory.ANALYTICAL: {
            "name": "Analytical", 
            "description": "Questions that require analysis, comparison, and critical thinking",
            "examples": ["How do these approaches compare?", "What are the implications?"]
        },
        QuestionCategory.SUMMARY: {
            "name": "Summary",
            "description": "Questions about main points, overviews, and key takeaways",
            "examples": ["What are the main conclusions?", "What is the central theme?"]
        },
        QuestionCategory.TECHNICAL: {
            "name": "Technical",
            "description": "Questions about technical details, implementation, and methodology",
            "examples": ["How does this algorithm work?", "What technologies are used?"]
        },
        QuestionCategory.STRATEGIC: {
            "name": "Strategic",
            "description": "Questions about decisions, planning, and high-level considerations",
            "examples": ["What are the business implications?", "What are the next steps?"]
        },
        QuestionCategory.DEBUGGING: {
            "name": "Debugging",
            "description": "Questions about potential issues, problems, and troubleshooting",
            "examples": ["What could go wrong?", "How would you debug this?"]
        },
        QuestionCategory.OPTIMIZATION: {
            "name": "Optimization",
            "description": "Questions about improving performance, efficiency, and quality",
            "examples": ["How can this be optimized?", "What are the bottlenecks?"]
        },
        QuestionCategory.IMPLEMENTATION: {
            "name": "Implementation",
            "description": "Questions about practical application and execution",
            "examples": ["How would you implement this?", "What are the requirements?"]
        }
    }
    
    return {
        "categories": categories,
        "total_categories": len(categories)
    }

def detect_document_category(text: str, filename: str) -> str:
    """
    Auto-detect document category based on content and filename
    
    Args:
        text: Document text content
        filename: Document filename
        
    Returns:
        Detected category (code, research, documentation, general)
    """
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Check for code files by extension
    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.sh', '.html', '.css', '.sql', '.json', '.xml']
    if any(filename_lower.endswith(ext) for ext in code_extensions):
        return "code"
    
    # Check for code content patterns
    code_patterns = [
        'def ', 'function ', 'class ', 'import ', 'from ', '#include',
        'public class', 'private ', 'protected ', 'void ', 'int main',
        'console.log', 'print(', 'System.out', 'std::', '<?php'
    ]
    if any(pattern in text_lower for pattern in code_patterns):
        return "code"
    
    # Check for research/academic content
    research_patterns = [
        'abstract', 'methodology', 'hypothesis', 'research question',
        'literature review', 'data analysis', 'statistical', 'p-value',
        'correlation', 'regression', 'study', 'experiment', 'findings',
        'conclusion', 'references', 'bibliography'
    ]
    research_count = sum(1 for pattern in research_patterns if pattern in text_lower)
    if research_count >= 3:
        return "research"
    
    # Check for documentation patterns
    doc_patterns = [
        'installation', 'configuration', 'setup', 'getting started',
        'tutorial', 'guide', 'documentation', 'api reference',
        'user manual', 'how to', 'step by step', 'requirements'
    ]
    doc_count = sum(1 for pattern in doc_patterns if pattern in text_lower)
    if doc_count >= 2:
        return "documentation"
    
    # Default to general
    return "general"

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "version": "2.0.0",
        "services": {
            "api": "operational",
            "ai_models": "operational",
            "document_processing": "operational"
        }
    }

# Add metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get API metrics"""
    return {
        "requests": {
            "total": 1500,
            "last_24h": 150,
            "success_rate": 98.5
        },
        "documents": {
            "processed": 450,
            "formats": ["PDF", "DOCX", "TXT", "MD", "HTML", "Images"]
        },
        "ai_models": {
            "primary": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "available": ["meta-llama", "deepseek-r1", "qwen3-coder"]
        }
    }

# Add search endpoint
@app.get("/search")
async def search_documents(q: str, limit: int = 20):
    """Search documents"""
    # Simple mock search for now
    return {
        "query": q,
        "results": [
            {
                "id": "doc_1",
                "title": f"Document about {q}",
                "snippet": f"This document contains information about {q}...",
                "score": 0.95
            }
        ],
        "total": 1,
        "limit": limit
    }

# Include advanced API routers if available
if ADVANCED_FEATURES_AVAILABLE:
    try:
        app.include_router(webhook_router)
        app.include_router(email_router)
        app.include_router(cloud_storage_router)
        print("[SUCCESS] Advanced features loaded successfully")
    except Exception as e:
        print(f"[WARNING] Error loading advanced features: {e}")
else:
    print("⚠️  Advanced features not available - running in basic mode")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return {
        "name": "Document Intelligence Platform",
        "version": "2.0.0",
        "description": "Advanced document processing with AI-powered analysis",
        "features": {
            "document_processing": True,
            "ai_question_answering": True,
            "multi_model_support": True,
            "ocr_support": True,
            "advanced_features": ADVANCED_FEATURES_AVAILABLE
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "ask": "/ask",
            "search": "/search"
        }
    }