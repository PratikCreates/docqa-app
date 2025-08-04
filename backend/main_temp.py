# backend/main_temp.py - Temporary version without pytesseract

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
from openai import OpenAI
from dotenv import load_dotenv
import PyPDF2
import docx
from typing import Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.multi_model_ai import MultiModelAIService
from services.question_generator import question_generator

# Load environment variables
load_dotenv()

app = FastAPI(title="Document Q&A API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service
ai_service = MultiModelAIService()

@app.get("/")
async def root():
    return {"message": "Document Q&A API is running!", "status": "healthy"}

@app.get("/supported-formats")
async def get_supported_formats():
    return {
        "supported_formats": {
            "images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"],
            "documents": ["pdf", "docx", "txt", "md", "html", "xml"],
            "code_files": ["py", "js", "ts", "java", "cpp", "c", "sh", "css", "json"],
            "notebooks": ["ipynb"],
            "data_files": ["csv", "json"]
        },
        "total_formats": 20,
        "new_features": [
            "Jupyter notebook cell extraction",
            "Syntax-aware code analysis", 
            "Enhanced markup parsing",
            "Programming language detection"
        ]
    }

@app.get("/models")
async def get_available_models():
    """Get all available AI models"""
    try:
        models = ai_service.get_available_models()
        default_model = ai_service.get_default_model()
        return {
            "available_models": models,
            "default_model": default_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/recommend-model")
async def recommend_model(file: UploadFile = File(...)):
    """Get model recommendation based on file type and content"""
    try:
        # Read file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        
        # Get recommendation
        recommendation = ai_service.recommend_model(
            file_type=file_extension,
            file_size=len(content),
            content_preview=content[:1000].decode('utf-8', errors='ignore')
        )
        
        return {
            "recommended_model": recommendation["model_id"],
            "explanation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")

def _process_jupyter_notebook(file_content: bytes, filename: str) -> str:
    """Enhanced Jupyter notebook processing with comprehensive output extraction"""
    try:
        import json
        
        # Parse the notebook JSON
        notebook_data = json.loads(file_content.decode('utf-8', errors='ignore'))
        
        # Extract metadata
        cells = notebook_data.get('cells', [])
        kernel_info = notebook_data.get('metadata', {}).get('kernelspec', {})
        language = kernel_info.get('language', 'python')
        
        # Process cells with enhanced output handling
        code_cells = []
        markdown_cells = []
        output_cells = []
        image_count = 0
        plot_count = 0
        
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', 'unknown')
            source = ''.join(cell.get('source', []))
            
            if cell_type == 'code':
                code_cells.append(f"# Cell {i+1} (Code)\n{source}")
                
                # Enhanced output extraction
                outputs = cell.get('outputs', [])
                for j, output in enumerate(outputs):
                    output_type = output.get('output_type', 'unknown')
                    
                    # Text outputs
                    if 'text' in output:
                        output_text = ''.join(output['text'])
                        output_cells.append(f"# Cell {i+1} Output {j+1} (Text)\n{output_text}")
                    
                    # Display data (plots, images, HTML)
                    elif 'data' in output:
                        data = output['data']
                        
                        # Text representations
                        if 'text/plain' in data:
                            text_output = ''.join(data['text/plain'])
                            output_cells.append(f"# Cell {i+1} Output {j+1} (Display)\n{text_output}")
                        
                        # HTML content
                        if 'text/html' in data:
                            html_content = ''.join(data['text/html'])
                            # Extract text from HTML (basic)
                            import re
                            text_from_html = re.sub(r'<[^>]+>', '', html_content)
                            if text_from_html.strip():
                                output_cells.append(f"# Cell {i+1} Output {j+1} (HTML Content)\n{text_from_html}")
                        
                        # Images and plots
                        if any(key.startswith('image/') for key in data.keys()):
                            image_count += 1
                            output_cells.append(f"# Cell {i+1} Output {j+1} (Image)\n[Image {image_count}: Contains visual content - graphs, plots, or images]")
                        
                        if 'application/vnd.plotly.v1+json' in data:
                            plot_count += 1
                            output_cells.append(f"# Cell {i+1} Output {j+1} (Interactive Plot)\n[Interactive Plot {plot_count}: Plotly visualization]")
                    
                    # Error outputs
                    elif output_type == 'error':
                        error_name = output.get('ename', 'Error')
                        error_value = output.get('evalue', 'Unknown error')
                        traceback = '\n'.join(output.get('traceback', []))
                        output_cells.append(f"# Cell {i+1} Error Output\n{error_name}: {error_value}\n{traceback}")
                    
                    # Stream outputs (stdout, stderr)
                    elif output_type == 'stream':
                        stream_name = output.get('name', 'output')
                        stream_text = ''.join(output.get('text', []))
                        output_cells.append(f"# Cell {i+1} {stream_name.title()} Output\n{stream_text}")
                        
            elif cell_type == 'markdown':
                markdown_cells.append(f"# Cell {i+1} (Markdown)\n{source}")
            
            elif cell_type == 'raw':
                # Raw cells contain unformatted text
                output_cells.append(f"# Cell {i+1} (Raw)\n{source}")
        
        # Build comprehensive context with statistics
        context = f"[Enhanced Jupyter Notebook Analysis: {filename}]\n"
        context += f"Language: {language.title()}\n"
        context += f"Total cells: {len(cells)}\n"
        context += f"Code cells: {len(code_cells)}\n"
        context += f"Markdown cells: {len(markdown_cells)}\n"
        context += f"Output sections: {len(output_cells)}\n"
        context += f"Images/Plots detected: {image_count + plot_count}\n"
        context += f"Original file size: {len(file_content)} bytes\n"
        
        # Combine all content
        result = context + "\n\n"
        
        if markdown_cells:
            result += "=== MARKDOWN CONTENT ===\n\n"
            result += "\n\n".join(markdown_cells) + "\n\n"
        
        if code_cells:
            result += "=== CODE CONTENT ===\n\n"
            result += "\n\n".join(code_cells) + "\n\n"
        
        if output_cells:
            result += "=== OUTPUTS & RESULTS ===\n\n"
            result += "\n\n".join(output_cells)
        
        # Add extraction summary
        result += f"\n\n=== EXTRACTION SUMMARY ===\n"
        result += f"Extracted text length: {len(result)} characters\n"
        result += f"Extraction ratio: {len(result)/len(file_content)*100:.1f}%\n"
        result += f"Content types found: Code, Markdown"
        if image_count > 0:
            result += f", Images ({image_count})"
        if plot_count > 0:
            result += f", Interactive Plots ({plot_count})"
        
        return result
        
    except json.JSONDecodeError:
        return f"[Error: Invalid Jupyter notebook format in {filename}]\nFile size: {len(file_content)} bytes"
    except Exception as e:
        return f"[Error processing Jupyter notebook {filename}: {str(e)}]\nFile size: {len(file_content)} bytes"

def _process_text_and_code_files(file_content: bytes, file_extension: str, filename: str) -> str:
    """Enhanced processing for text and code files with syntax awareness"""
    try:
        text_content = file_content.decode('utf-8', errors='ignore').strip()
        
        # Add file type context for better AI analysis
        if file_extension in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'sh']:
            # Code files - add syntax context
            language_map = {
                'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 
                'java': 'Java', 'cpp': 'C++', 'c': 'C', 'sh': 'Shell/Bash'
            }
            language = language_map.get(file_extension, file_extension.upper())
            
            # Analyze code structure
            lines = text_content.split('\n')
            functions = [line.strip() for line in lines if any(keyword in line for keyword in ['def ', 'function ', 'class ', 'public ', 'private '])]
            imports = [line.strip() for line in lines if any(keyword in line for keyword in ['import ', 'from ', '#include', 'require('])]
            
            context = f"[{language} Code File: {filename}]\n"
            if functions:
                context += f"Functions/Classes found: {len(functions)}\n"
            if imports:
                context += f"Dependencies/Imports: {len(imports)}\n"
            context += f"Total lines: {len(lines)}\n\n"
            
            return context + text_content
            
        elif file_extension in ['html', 'xml']:
            # Markup files - add structure context
            import re
            tags = re.findall(r'<(\w+)', text_content)
            unique_tags = list(set(tags))
            
            context = f"[{file_extension.upper()} File: {filename}]\n"
            context += f"HTML/XML Tags found: {', '.join(unique_tags[:10])}\n"
            context += f"Total elements: {len(tags)}\n\n"
            
            return context + text_content
            
        elif file_extension == 'md':
            # Markdown files - add structure context
            import re
            headers = re.findall(r'^#+\s+(.+)$', text_content, re.MULTILINE)
            
            context = f"[Markdown File: {filename}]\n"
            if headers:
                context += f"Headers found: {len(headers)}\n"
                context += f"Main sections: {', '.join(headers[:5])}\n"
            context += f"Document length: {len(text_content)} characters\n\n"
            
            return context + text_content
            
        else:
            # Plain text files
            lines = text_content.split('\n')
            context = f"[Text File: {filename}]\n"
            context += f"Lines: {len(lines)}, Characters: {len(text_content)}\n\n"
            
            return context + text_content
            
    except Exception as e:
        return f"[Error processing {filename}: {str(e)}]\n\n{file_content.decode('utf-8', errors='ignore')}"

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from various file formats (without OCR for now)"""
    file_extension = filename.split('.')[-1].lower() if filename else ""
    
    try:
        if file_extension == 'pdf':
            # Extract text from PDF
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        
        elif file_extension == 'docx':
            # Extract text from DOCX
            doc_file = io.BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        elif file_extension == 'ipynb':
            # Jupyter notebook processing
            return _process_jupyter_notebook(file_content, filename)
            
        elif file_extension in ['txt', 'md', 'html', 'xml', 'py', 'js', 'ts', 'java', 'cpp', 'c', 'sh', 'css', 'json', 'csv']:
            # Enhanced text and code file processing
            return _process_text_and_code_files(file_content, file_extension, filename)
        
        elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']:
            # For images, return a placeholder (OCR would go here)
            return f"[Image file: {filename}] - OCR functionality temporarily disabled"
        
        else:
            return f"[Unsupported file type: {file_extension}]"
    
    except Exception as e:
        return f"[Error extracting text: {str(e)}]"

@app.post("/ask")
async def ask_question(
    file: UploadFile = File(...),
    question: str = Form(...),
    model: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
    show_thinking: Optional[bool] = Form(False)
):
    """Process document and answer question"""
    try:
        print(f"Processing request: file={file.filename}, question={question[:50]}...")
        
        # Read file content
        file_content = await file.read()
        print(f"File content length: {len(file_content)}")
        
        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename)
        print(f"Extracted text length: {len(extracted_text)}")
        
        # Get AI response
        print(f"Calling AI service with model: {model}, show_thinking: {show_thinking}")
        response = await ai_service.process_document_question(
            extracted_text=extracted_text,
            question=question,
            file_type=file.filename.split('.')[-1].lower() if file.filename else "",
            model_id=model,
            system_prompt=system_prompt,
            show_thinking=show_thinking
        )
        print("AI service call successful")
        
        return {
            "answer": response["answer"],
            "extracted_text": extracted_text,
            "file_type": file.filename.split('.')[-1].lower() if file.filename else "",
            "model_used": response["model_used"],
            "model_info": response["model_info"],
            "processing_time": response["processing_time"],
            "fallback_used": response.get("fallback_used", False),
            "recommendation_explanation": response.get("recommendation_explanation")
        }
    
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/compare-models")
async def compare_models(
    file: UploadFile = File(...),
    question: str = Form(...),
    models: str = Form(...)  # Comma-separated model IDs
):
    """Compare responses from multiple models"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text from file
        extracted_text = extract_text_from_file(file_content, file.filename)
        
        # Parse model list
        model_list = [m.strip() for m in models.split(",")]
        
        # Get comparison results
        comparison = await ai_service.compare_models(
            extracted_text=extracted_text,
            question=question,
            model_ids=model_list,
            file_type=file.filename.split('.')[-1].lower() if file.filename else ""
        )
        
        return comparison
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@app.get("/model-performance")
async def get_model_performance():
    """Get comprehensive model performance statistics"""
    try:
        stats = ai_service.model_selector.get_model_performance_stats()
        return {
            "performance_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@app.post("/model-feedback")
async def submit_model_feedback(
    model_id: str = Form(...),
    file_type: str = Form(...),
    satisfaction: int = Form(...),  # 1-5 scale
    processing_time: float = Form(...),
    success: bool = Form(True)
):
    """Submit user feedback for model performance"""
    try:
        if not (1 <= satisfaction <= 5):
            raise HTTPException(status_code=400, detail="Satisfaction must be between 1 and 5")
        
        # Track the feedback
        ai_service.model_selector.track_model_performance(
            model_id=model_id,
            file_type=file_type,
            processing_time=processing_time,
            success=success,
            user_satisfaction=satisfaction
        )
        
        return {
            "message": "Feedback recorded successfully",
            "model_id": model_id,
            "satisfaction": satisfaction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@app.post("/enhanced-recommend-model")
async def enhanced_recommend_model(
    file: UploadFile = File(...),
    user_id: str = Form("default")
):
    """Get enhanced model recommendation with performance data and user preferences"""
    try:
        # Read file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        
        # Get enhanced recommendation
        recommendation = ai_service.model_selector.get_enhanced_recommendation(
            filename=file.filename,
            content_preview=content[:1000].decode('utf-8', errors='ignore'),
            user_id=user_id
        )
        
        return {
            "enhanced_recommendation": recommendation,
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "type": file_extension
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced recommendation failed: {str(e)}")

@app.post("/recommend-model")
async def recommend_model(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    complexity_level: Optional[str] = Form(None)
):
    """Get advanced model recommendation based on multiple factors"""
    try:
        # Read file content
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        content_preview = content[:2000].decode('utf-8', errors='ignore')
        
        # Get advanced recommendation
        recommendation = ai_service.get_advanced_recommendation(
            filename=file.filename or "unknown",
            content_preview=content_preview,
            question_type=question,
            complexity_level=complexity_level
        )
        
        return {
            "recommended_model": recommendation["model_id"],
            "explanation": {
                "model_name": recommendation["model_name"],
                "reasons": recommendation["reasoning"],
                "confidence": recommendation["confidence"]
            },
            "confidence_score": recommendation["confidence"],
            "alternative_models": recommendation["alternatives"],
            "reasoning_factors": recommendation["factors"],
            "model_details": recommendation["model_details"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation: {str(e)}")

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
        
        # Extract text from document using existing function
        extracted_text = extract_text_from_file(await file.read(), file.filename)
        
        if not extracted_text.strip() or extracted_text.startswith("[Error"):
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
    
    # Check for code content patterns (but be more strict for non-code files)
    code_patterns = [
        'def ', 'function ', 'class ', 'import ', 'from ', '#include',
        'public class', 'private ', 'protected ', 'void ', 'int main',
        'console.log', 'print(', 'System.out', 'std::', '<?php'
    ]
    
    # For PDF files, require more code patterns to classify as code
    code_threshold = 3 if filename_lower.endswith('.pdf') else 1
    code_count = sum(1 for pattern in code_patterns if pattern in text_lower)
    
    if code_count >= code_threshold:
        return "code"
    
    # Check for business document patterns first (common for PDFs)
    business_patterns = [
        'invoice', 'receipt', 'contract', 'agreement', 'proposal',
        'report', 'summary', 'analysis', 'financial', 'budget',
        'quarterly', 'annual', 'revenue', 'profit', 'loss',
        'company', 'corporation', 'business', 'client', 'customer'
    ]
    business_count = sum(1 for pattern in business_patterns if pattern in text_lower)
    if business_count >= 2:
        return "general"  # Business documents are general category
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)