"""
File parser service for extracting content from various file formats including OCR for images and PDFs
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import mimetypes
import io
import base64

class FileParserService:
    """Service for parsing different file formats and extracting content"""
    
    def __init__(self):
        self.supported_extensions = {
            # Text formats
            'txt': self._parse_text,
            'md': self._parse_markdown,
            'html': self._parse_html,
            'xml': self._parse_xml,
            
            # Code formats
            'py': self._parse_python,
            'js': self._parse_javascript,
            'ts': self._parse_typescript,
            'java': self._parse_java,
            'cpp': self._parse_cpp,
            'c': self._parse_c,
            'sh': self._parse_shell,
            
            # Data formats
            'json': self._parse_json,
            'csv': self._parse_csv,
            'yaml': self._parse_yaml,
            'yml': self._parse_yaml,
            
            # Notebook
            'ipynb': self._parse_jupyter_notebook,
            
            # Config
            'ini': self._parse_ini,
            'conf': self._parse_config,
            'cfg': self._parse_config,
            'toml': self._parse_toml,
            
            # OCR-supported formats
            'pdf': self._parse_pdf_with_ocr,
            'png': self._parse_image_with_ocr,
            'jpg': self._parse_image_with_ocr,
            'jpeg': self._parse_image_with_ocr,
            'gif': self._parse_image_with_ocr,
            'bmp': self._parse_image_with_ocr,
            'tiff': self._parse_image_with_ocr,
            'tif': self._parse_image_with_ocr,
            'webp': self._parse_image_with_ocr
        }
        
        # Initialize OCR capabilities
        self._init_ocr_engines()
    
    def _init_ocr_engines(self):
        """Initialize OCR engines with fallback options"""
        self.ocr_engines = []
        
        # Try to initialize Tesseract OCR
        try:
            import pytesseract
            from PIL import Image
            self.ocr_engines.append({
                'name': 'tesseract',
                'module': pytesseract,
                'image_module': Image,
                'available': True
            })
            print("✅ Tesseract OCR initialized")
        except ImportError:
            print("⚠️  Tesseract OCR not available - install with: pip install pytesseract pillow")
        
        # Try to initialize EasyOCR
        try:
            import easyocr
            self.ocr_engines.append({
                'name': 'easyocr',
                'module': easyocr,
                'available': True
            })
            print("✅ EasyOCR initialized")
        except ImportError:
            print("⚠️  EasyOCR not available - install with: pip install easyocr")
        
        # Try to initialize PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.ocr_engines.append({
                'name': 'paddleocr',
                'module': PaddleOCR,
                'available': True
            })
            print("✅ PaddleOCR initialized")
        except ImportError:
            print("⚠️  PaddleOCR not available - install with: pip install paddlepaddle paddleocr")
        
        if not self.ocr_engines:
            print("❌ No OCR engines available. Install at least one:")
            print("   pip install pytesseract pillow")
            print("   pip install easyocr")
            print("   pip install paddlepaddle paddleocr")
    
    def parse_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Parse file content based on file extension"""
        try:
            # Get file extension
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Check if this is a binary file that needs OCR
            if file_ext in ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp']:
                # Handle binary files with OCR
                parser = self.supported_extensions.get(file_ext, self._parse_generic_binary)
                result = parser(content, filename)
            else:
                # Handle text files
                try:
                    text_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = content.decode('latin-1')
                    except UnicodeDecodeError:
                        return {
                            "content": "",
                            "metadata": {"error": "Unable to decode file content"},
                            "parsing_info": {"success": False, "error": "Encoding error"}
                        }
                
                # Get parser for file type
                parser = self.supported_extensions.get(file_ext, self._parse_generic_text)
                
                # Parse content
                result = parser(text_content, filename)
            
            # Add common metadata
            result["metadata"].update({
                "file_extension": file_ext,
                "file_size": len(content),
                "content_type": mimetypes.guess_type(filename)[0] or "text/plain",
                "line_count": len(text_content.split('\n')),
                "character_count": len(text_content)
            })
            
            result["parsing_info"] = {"success": True, "parser_used": parser.__name__}
            
            return result
            
        except Exception as e:
            return {
                "content": content.decode('utf-8', errors='ignore'),
                "metadata": {"error": f"Parsing failed: {str(e)}"},
                "parsing_info": {"success": False, "error": str(e)}
            }
    
    def _parse_text(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse plain text files"""
        return {
            "content": content,
            "metadata": {
                "format": "plain_text",
                "word_count": len(content.split())
            }
        }
    
    def _parse_markdown(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Markdown files"""
        # Extract headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        
        return {
            "content": content,
            "metadata": {
                "format": "markdown",
                "headers": [{"level": len(level), "text": text} for level, text in headers],
                "links": [{"text": text, "url": url} for text, url in links],
                "code_blocks": [{"language": lang or "unknown", "code": code.strip()} for lang, code in code_blocks],
                "word_count": len(content.split())
            }
        }
    
    def _parse_html(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse HTML files"""
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1) if title_match else ""
        
        # Extract meta tags
        meta_tags = re.findall(r'<meta[^>]+name=["\']([^"\']+)["\'][^>]+content=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            h_tags = re.findall(f'<h{i}[^>]*>([^<]+)</h{i}>', content, re.IGNORECASE)
            headings.extend([{"level": i, "text": text.strip()} for text in h_tags])
        
        # Remove HTML tags for clean text
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return {
            "content": clean_text,
            "metadata": {
                "format": "html",
                "title": title,
                "meta_tags": dict(meta_tags),
                "headings": headings,
                "raw_html": content[:1000] + "..." if len(content) > 1000 else content
            }
        }
    
    def _parse_xml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse XML files"""
        # Extract root element
        root_match = re.search(r'<(\w+)[^>]*>', content)
        root_element = root_match.group(1) if root_match else "unknown"
        
        # Extract all element names
        elements = list(set(re.findall(r'<(\w+)[^>]*>', content)))
        
        # Remove XML tags for clean text
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return {
            "content": clean_text,
            "metadata": {
                "format": "xml",
                "root_element": root_element,
                "elements": elements,
                "raw_xml": content[:1000] + "..." if len(content) > 1000 else content
            }
        }
    
    def _parse_python(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Python files"""
        # Extract imports
        imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+([^\n]+)', content, re.MULTILINE)
        
        # Extract function definitions
        functions = re.findall(r'^def\s+(\w+)\s*\([^)]*\):', content, re.MULTILINE)
        
        # Extract class definitions
        classes = re.findall(r'^class\s+(\w+)(?:\([^)]*\))?:', content, re.MULTILINE)
        
        # Extract docstrings
        docstrings = re.findall(r'"""([^"]+)"""', content, re.DOTALL)
        
        return {
            "content": content,
            "metadata": {
                "format": "python",
                "language": "python",
                "imports": [{"from": from_module, "import": import_items} for from_module, import_items in imports],
                "functions": functions,
                "classes": classes,
                "docstrings": [doc.strip() for doc in docstrings],
                "complexity_indicators": {
                    "function_count": len(functions),
                    "class_count": len(classes),
                    "import_count": len(imports)
                }
            }
        }
    
    def _parse_javascript(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse JavaScript files"""
        # Extract function declarations
        functions = re.findall(r'function\s+(\w+)\s*\([^)]*\)', content)
        
        # Extract arrow functions
        arrow_functions = re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>', content)
        
        # Extract imports/requires
        imports = re.findall(r'(?:import\s+[^;]+from\s+["\']([^"\']+)["\']|require\s*\(\s*["\']([^"\']+)["\']\s*\))', content)
        
        # Extract classes
        classes = re.findall(r'class\s+(\w+)(?:\s+extends\s+\w+)?', content)
        
        return {
            "content": content,
            "metadata": {
                "format": "javascript",
                "language": "javascript",
                "functions": functions + arrow_functions,
                "classes": classes,
                "imports": [imp[0] or imp[1] for imp in imports if imp[0] or imp[1]],
                "complexity_indicators": {
                    "function_count": len(functions) + len(arrow_functions),
                    "class_count": len(classes),
                    "import_count": len(imports)
                }
            }
        }
    
    def _parse_typescript(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse TypeScript files"""
        # Use JavaScript parser as base
        result = self._parse_javascript(content, filename)
        
        # Extract interfaces
        interfaces = re.findall(r'interface\s+(\w+)', content)
        
        # Extract types
        types = re.findall(r'type\s+(\w+)\s*=', content)
        
        result["metadata"].update({
            "format": "typescript",
            "language": "typescript",
            "interfaces": interfaces,
            "types": types
        })
        
        return result
    
    def _parse_java(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Java files"""
        # Extract package
        package_match = re.search(r'package\s+([^;]+);', content)
        package = package_match.group(1) if package_match else ""
        
        # Extract imports
        imports = re.findall(r'import\s+([^;]+);', content)
        
        # Extract classes
        classes = re.findall(r'(?:public\s+)?class\s+(\w+)', content)
        
        # Extract methods
        methods = re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)', content)
        
        return {
            "content": content,
            "metadata": {
                "format": "java",
                "language": "java",
                "package": package,
                "imports": imports,
                "classes": classes,
                "methods": methods,
                "complexity_indicators": {
                    "class_count": len(classes),
                    "method_count": len(methods),
                    "import_count": len(imports)
                }
            }
        }
    
    def _parse_cpp(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse C++ files"""
        # Extract includes
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
        
        # Extract function definitions
        functions = re.findall(r'(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*{', content)
        
        # Extract classes
        classes = re.findall(r'class\s+(\w+)', content)
        
        return {
            "content": content,
            "metadata": {
                "format": "cpp",
                "language": "cpp",
                "includes": includes,
                "functions": functions,
                "classes": classes,
                "complexity_indicators": {
                    "function_count": len(functions),
                    "class_count": len(classes),
                    "include_count": len(includes)
                }
            }
        }
    
    def _parse_c(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse C files"""
        # Extract includes
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
        
        # Extract function definitions
        functions = re.findall(r'(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*{', content)
        
        return {
            "content": content,
            "metadata": {
                "format": "c",
                "language": "c",
                "includes": includes,
                "functions": functions,
                "complexity_indicators": {
                    "function_count": len(functions),
                    "include_count": len(includes)
                }
            }
        }
    
    def _parse_shell(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse shell script files"""
        # Extract functions
        functions = re.findall(r'(\w+)\s*\(\s*\)\s*{', content)
        
        # Extract variables
        variables = re.findall(r'(\w+)=', content)
        
        return {
            "content": content,
            "metadata": {
                "format": "shell",
                "language": "shell",
                "functions": functions,
                "variables": list(set(variables)),
                "complexity_indicators": {
                    "function_count": len(functions),
                    "variable_count": len(set(variables))
                }
            }
        }
    
    def _parse_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse JSON files"""
        try:
            data = json.loads(content)
            
            # Analyze structure
            def analyze_json_structure(obj, path=""):
                if isinstance(obj, dict):
                    return {f"{path}.{k}" if path else k: analyze_json_structure(v, f"{path}.{k}" if path else k) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return f"array[{len(obj)}]"
                else:
                    return type(obj).__name__
            
            structure = analyze_json_structure(data)
            
            return {
                "content": json.dumps(data, indent=2),
                "metadata": {
                    "format": "json",
                    "valid_json": True,
                    "structure": structure,
                    "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
                    "data_preview": str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                }
            }
            
        except json.JSONDecodeError as e:
            return {
                "content": content,
                "metadata": {
                    "format": "json",
                    "valid_json": False,
                    "error": str(e)
                }
            }
    
    def _parse_csv(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse CSV files"""
        lines = content.split('\n')
        if not lines:
            return {"content": content, "metadata": {"format": "csv", "rows": 0, "columns": 0}}
        
        # Detect delimiter
        first_line = lines[0]
        delimiter = ',' if ',' in first_line else '\t' if '\t' in first_line else ';'
        
        # Extract headers
        headers = [h.strip('"') for h in first_line.split(delimiter)]
        
        # Count rows
        data_rows = len([line for line in lines[1:] if line.strip()])
        
        return {
            "content": content,
            "metadata": {
                "format": "csv",
                "delimiter": delimiter,
                "headers": headers,
                "column_count": len(headers),
                "row_count": data_rows,
                "total_rows": len(lines)
            }
        }
    
    def _parse_yaml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse YAML files"""
        try:
            import yaml
            data = yaml.safe_load(content)
            
            return {
                "content": content,
                "metadata": {
                    "format": "yaml",
                    "valid_yaml": True,
                    "top_level_keys": list(data.keys()) if isinstance(data, dict) else [],
                    "data_preview": str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                }
            }
            
        except Exception as e:
            return {
                "content": content,
                "metadata": {
                    "format": "yaml",
                    "valid_yaml": False,
                    "error": str(e)
                }
            }
    
    def _parse_jupyter_notebook(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Jupyter notebook files"""
        try:
            notebook = json.loads(content)
            
            cells = notebook.get('cells', [])
            code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
            markdown_cells = [cell for cell in cells if cell.get('cell_type') == 'markdown']
            
            # Extract all code
            all_code = '\n'.join([''.join(cell.get('source', [])) for cell in code_cells])
            
            # Extract all markdown
            all_markdown = '\n'.join([''.join(cell.get('source', [])) for cell in markdown_cells])
            
            # Combine for searchable content
            combined_content = f"{all_markdown}\n\n{all_code}"
            
            return {
                "content": combined_content,
                "metadata": {
                    "format": "jupyter_notebook",
                    "language": notebook.get('metadata', {}).get('kernelspec', {}).get('language', 'python'),
                    "total_cells": len(cells),
                    "code_cells": len(code_cells),
                    "markdown_cells": len(markdown_cells),
                    "notebook_version": notebook.get('nbformat', 'unknown'),
                    "code_content": all_code,
                    "markdown_content": all_markdown
                }
            }
            
        except json.JSONDecodeError as e:
            return {
                "content": content,
                "metadata": {
                    "format": "jupyter_notebook",
                    "valid_notebook": False,
                    "error": str(e)
                }
            }
    
    def _parse_ini(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse INI configuration files"""
        sections = re.findall(r'^\[([^\]]+)\]', content, re.MULTILINE)
        
        # Extract key-value pairs
        key_values = re.findall(r'^(\w+)\s*=\s*(.+)$', content, re.MULTILINE)
        
        return {
            "content": content,
            "metadata": {
                "format": "ini",
                "sections": sections,
                "key_value_pairs": dict(key_values),
                "section_count": len(sections)
            }
        }
    
    def _parse_config(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse generic configuration files"""
        # Extract key-value pairs
        key_values = re.findall(r'^(\w+)\s*[=:]\s*(.+)$', content, re.MULTILINE)
        
        return {
            "content": content,
            "metadata": {
                "format": "config",
                "key_value_pairs": dict(key_values),
                "setting_count": len(key_values)
            }
        }
    
    def _parse_toml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse TOML files"""
        try:
            import toml
            data = toml.loads(content)
            
            return {
                "content": content,
                "metadata": {
                    "format": "toml",
                    "valid_toml": True,
                    "top_level_keys": list(data.keys()),
                    "data_preview": str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                }
            }
            
        except Exception as e:
            return {
                "content": content,
                "metadata": {
                    "format": "toml",
                    "valid_toml": False,
                    "error": str(e)
                }
            }
    
    def _parse_generic_text(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse generic text files"""
        return {
            "content": content,
            "metadata": {
                "format": "generic_text",
                "word_count": len(content.split()),
                "paragraph_count": len([p for p in content.split('\n\n') if p.strip()])
            }
        }    d
ef _parse_generic_binary(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse generic binary files"""
        return {
            "content": f"Binary file: {filename} ({len(content)} bytes)",
            "metadata": {
                "format": "binary",
                "file_size": len(content),
                "is_binary": True
            }
        }
    
    def _extract_text_with_ocr(self, image_data: bytes, filename: str) -> Dict[str, str]:
        """Extract text from image using available OCR engines"""
        
        if not self.ocr_engines:
            return {
                "text": "",
                "error": "No OCR engines available",
                "engine_used": "none"
            }
        
        # Try each OCR engine until one works
        for engine in self.ocr_engines:
            try:
                if engine['name'] == 'tesseract':
                    return self._ocr_with_tesseract(image_data, filename, engine)
                elif engine['name'] == 'easyocr':
                    return self._ocr_with_easyocr(image_data, filename, engine)
                elif engine['name'] == 'paddleocr':
                    return self._ocr_with_paddleocr(image_data, filename, engine)
            except Exception as e:
                print(f"OCR engine {engine['name']} failed: {str(e)}")
                continue
        
        return {
            "text": "",
            "error": "All OCR engines failed",
            "engine_used": "none"
        }
    
    def _ocr_with_tesseract(self, image_data: bytes, filename: str, engine: Dict) -> Dict[str, str]:
        """Extract text using Tesseract OCR"""
        try:
            from PIL import Image
            import pytesseract
            
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Filter out low-confidence text
            confidences = data['conf']
            texts = data['text']
            
            filtered_text = []
            total_confidence = 0
            valid_words = 0
            
            for i, (text, conf) in enumerate(zip(texts, confidences)):
                if conf > 30 and text.strip():  # Only include text with >30% confidence
                    filtered_text.append(text)
                    total_confidence += conf
                    valid_words += 1
            
            extracted_text = ' '.join(filtered_text)
            avg_confidence = total_confidence / valid_words if valid_words > 0 else 0
            
            return {
                "text": extracted_text,
                "engine_used": "tesseract",
                "confidence": avg_confidence,
                "word_count": valid_words,
                "image_info": {
                    "size": image.size,
                    "mode": image.mode,
                    "format": image.format
                }
            }
            
        except Exception as e:
            raise Exception(f"Tesseract OCR failed: {str(e)}")
    
    def _ocr_with_easyocr(self, image_data: bytes, filename: str, engine: Dict) -> Dict[str, str]:
        """Extract text using EasyOCR"""
        try:
            import easyocr
            import numpy as np
            from PIL import Image
            
            # Initialize EasyOCR reader (English by default, can be extended)
            reader = easyocr.Reader(['en'])
            
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Extract text
            results = reader.readtext(image_array)
            
            # Process results
            extracted_texts = []
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Only include text with >30% confidence
                    extracted_texts.append(text)
                    total_confidence += confidence
            
            extracted_text = ' '.join(extracted_texts)
            avg_confidence = (total_confidence / len(results)) * 100 if results else 0
            
            return {
                "text": extracted_text,
                "engine_used": "easyocr",
                "confidence": avg_confidence,
                "word_count": len(extracted_texts),
                "detection_count": len(results)
            }
            
        except Exception as e:
            raise Exception(f"EasyOCR failed: {str(e)}")
    
    def _ocr_with_paddleocr(self, image_data: bytes, filename: str, engine: Dict) -> Dict[str, str]:
        """Extract text using PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            from PIL import Image
            
            # Initialize PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Extract text
            results = ocr.ocr(image_array, cls=True)
            
            # Process results
            extracted_texts = []
            total_confidence = 0
            detection_count = 0
            
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        if confidence > 0.3:  # Only include text with >30% confidence
                            extracted_texts.append(text)
                            total_confidence += confidence
                            detection_count += 1
            
            extracted_text = ' '.join(extracted_texts)
            avg_confidence = (total_confidence / detection_count) * 100 if detection_count > 0 else 0
            
            return {
                "text": extracted_text,
                "engine_used": "paddleocr",
                "confidence": avg_confidence,
                "word_count": len(extracted_texts),
                "detection_count": detection_count
            }
            
        except Exception as e:
            raise Exception(f"PaddleOCR failed: {str(e)}")
    
    def _parse_image_with_ocr(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse image files using OCR"""
        try:
            # Extract text using OCR
            ocr_result = self._extract_text_with_ocr(content, filename)
            
            # Get image metadata
            try:
                from PIL import Image
                image = Image.open(io.BytesIO(content))
                image_metadata = {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                    "format": image.format,
                    "size_bytes": len(content)
                }
            except Exception:
                image_metadata = {"size_bytes": len(content)}
            
            return {
                "content": ocr_result.get("text", ""),
                "metadata": {
                    "format": "image_with_ocr",
                    "file_type": filename.split('.')[-1].lower(),
                    "ocr_engine": ocr_result.get("engine_used", "none"),
                    "ocr_confidence": ocr_result.get("confidence", 0),
                    "word_count": len(ocr_result.get("text", "").split()),
                    "image_info": image_metadata,
                    "ocr_error": ocr_result.get("error"),
                    "has_text": bool(ocr_result.get("text", "").strip())
                }
            }
            
        except Exception as e:
            return {
                "content": "",
                "metadata": {
                    "format": "image_with_ocr",
                    "file_type": filename.split('.')[-1].lower(),
                    "error": f"Image OCR failed: {str(e)}",
                    "size_bytes": len(content)
                }
            }
    
    def _parse_pdf_with_ocr(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Parse PDF files with text extraction and OCR fallback"""
        try:
            # First try to extract text directly from PDF
            text_content = self._extract_pdf_text(content)
            
            # If no text found, try OCR on PDF pages
            if not text_content.strip():
                text_content = self._extract_pdf_text_with_ocr(content)
                extraction_method = "ocr"
            else:
                extraction_method = "direct_text"
            
            # Get PDF metadata
            pdf_metadata = self._get_pdf_metadata(content)
            
            return {
                "content": text_content,
                "metadata": {
                    "format": "pdf_with_ocr",
                    "extraction_method": extraction_method,
                    "page_count": pdf_metadata.get("page_count", 0),
                    "word_count": len(text_content.split()),
                    "size_bytes": len(content),
                    "pdf_info": pdf_metadata,
                    "has_text": bool(text_content.strip())
                }
            }
            
        except Exception as e:
            return {
                "content": "",
                "metadata": {
                    "format": "pdf_with_ocr",
                    "error": f"PDF processing failed: {str(e)}",
                    "size_bytes": len(content)
                }
            }
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text directly from PDF"""
        try:
            import PyPDF2
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_content = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
            
            return '\n'.join(text_content)
            
        except ImportError:
            print("⚠️  PyPDF2 not available - install with: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"PDF text extraction failed: {str(e)}")
            return ""
    
    def _extract_pdf_text_with_ocr(self, content: bytes) -> str:
        """Extract text from PDF using OCR"""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            
            # Open PDF
            pdf_document = fitz.open(stream=content, filetype="pdf")
            all_text = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Extract text using OCR
                ocr_result = self._extract_text_with_ocr(img_data, f"page_{page_num + 1}")
                if ocr_result.get("text"):
                    all_text.append(f"--- Page {page_num + 1} ---")
                    all_text.append(ocr_result["text"])
            
            pdf_document.close()
            return '\n'.join(all_text)
            
        except ImportError:
            print("⚠️  PyMuPDF not available - install with: pip install PyMuPDF")
            return ""
        except Exception as e:
            print(f"PDF OCR failed: {str(e)}")
            return ""
    
    def _get_pdf_metadata(self, content: bytes) -> Dict[str, Any]:
        """Get PDF metadata"""
        try:
            import PyPDF2
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            metadata = pdf_reader.metadata or {}
            
            return {
                "page_count": len(pdf_reader.pages),
                "title": metadata.get('/Title', ''),
                "author": metadata.get('/Author', ''),
                "subject": metadata.get('/Subject', ''),
                "creator": metadata.get('/Creator', ''),
                "producer": metadata.get('/Producer', ''),
                "creation_date": str(metadata.get('/CreationDate', '')),
                "modification_date": str(metadata.get('/ModDate', ''))
            }
            
        except Exception:
            return {"page_count": 0}