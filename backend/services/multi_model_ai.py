# backend/services/multi_model_ai.py

import os
import time
import re
from typing import Dict, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from services.model_selector import ModelSelector
from models.ai_models import get_model_config

# Ensure environment variables are loaded
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class MultiModelAIService:
    """Service for handling multiple AI models with intelligent selection and fallback"""
    
    def __init__(self):
        api_key = os.environ.get("NEBIUS_API_KEY")
        if not api_key:
            print("[WARNING] NEBIUS_API_KEY not found in environment variables")
        else:
            print(f"[API] API key loaded (length: {len(api_key)})")
        
        self.client = OpenAI(
            base_url="https://api.studio.nebius.com/v1/",
            api_key=api_key
        )
        self.model_selector = ModelSelector()
    
    def process_with_model(
        self, 
        content: str, 
        question: str, 
        model: Optional[str] = None, 
        system_prompt: Optional[str] = None,
        filename: str = "",
        max_retries: int = 2,
        show_thinking: bool = False
    ) -> Dict:
        """
        Process content using specified or recommended model with fallback support
        
        Args:
            content: Document content to analyze
            question: User's question about the document
            model: Specific model to use (if None, will recommend)
            system_prompt: Custom system prompt (if None, will use model-specific)
            filename: Original filename for model recommendation
            max_retries: Number of fallback attempts
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        # Get model recommendation if not specified
        if not model:
            model = self.model_selector.recommend_model(filename, content[:1000])
        
        # Get model configuration
        model_config = get_model_config(model)
        if not model_config:
            model = self.model_selector.default_model
            model_config = get_model_config(model)
        
        # Use model-specific system prompt if not provided
        if not system_prompt:
            system_prompt = self._get_model_specific_prompt(model, content, question)
        
        # Try processing with primary model
        try:
            result = self._make_api_call(model, content, question, system_prompt, model_config, show_thinking)
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["attempts"] = 1
            
            # Track performance
            file_ext = filename.split('.')[-1] if '.' in filename else 'unknown'
            self.model_selector.track_model_performance(
                model_id=model,
                file_type=file_ext,
                processing_time=processing_time,
                success=True
            )
            
            return result
            
        except Exception as primary_error:
            print(f"Primary model {model} failed: {str(primary_error)}")
            
            # Track failure
            file_ext = filename.split('.')[-1] if '.' in filename else 'unknown'
            self.model_selector.track_model_performance(
                model_id=model,
                file_type=file_ext,
                processing_time=time.time() - start_time,
                success=False
            )
            
            # Try fallback models
            if max_retries > 0:
                fallback_chain = self.model_selector.get_fallback_chain(model)
                
                for attempt, fallback_model in enumerate(fallback_chain[:max_retries]):
                    try:
                        print(f"Trying fallback model: {fallback_model}")
                        fallback_config = get_model_config(fallback_model)
                        fallback_prompt = self._get_model_specific_prompt(fallback_model, content, question)
                        
                        result = self._make_api_call(
                            fallback_model, content, question, fallback_prompt, fallback_config, show_thinking
                        )
                        result["processing_time"] = time.time() - start_time
                        result["attempts"] = attempt + 2
                        result["fallback_used"] = True
                        result["original_model_error"] = str(primary_error)
                        return result
                        
                    except Exception as fallback_error:
                        print(f"Fallback model {fallback_model} failed: {str(fallback_error)}")
                        continue
            
            # All models failed
            raise Exception(f"All models failed. Primary error: {str(primary_error)}")
    
    def _make_api_call(self, model: str, content: str, question: str, system_prompt: str, model_config, show_thinking: bool = False) -> Dict:
        """Make the actual API call to the AI model with proper format for each model"""
        
        # Check if this is a coding request and modify the user message accordingly
        question_lower = question.lower()
        complex_keywords = ["solve", "implement", "write code", "complete", "all problems"]
        is_coding_request = any(keyword in question_lower for keyword in complex_keywords)
        
        if is_coding_request:
            user_message = f"""Document content:\n\n{content}\n\n{question}

CRITICAL: Provide Python code with PERFECT INDENTATION. Follow this EXACT format:

Problem 1: [name]
def function_name():
    # Function body MUST be indented 4 spaces
    if condition:
        # If body MUST be indented 8 spaces
        return value
    return default

Problem 2: [name]
def another_function():
    # All code inside function MUST be indented 4 spaces
    for i in range(10):
        # Loop body MUST be indented 8 spaces
        print(i)
    return result

REMEMBER: 4 spaces for function body, 8 spaces for nested blocks!"""
        else:
            user_message = f"""Document content:\n\n{content}\n\nQuestion: {question}"""
        
        # Use standard message format for all models - this is more reliable
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Determine appropriate token limit based on content complexity
            content_length = len(content) + len(question)
            question_lower = question.lower()
            
            # Check for complex requests that need more tokens
            complex_keywords = ["solve", "all", "complete", "implement", "write code", "problems", "exercises"]
            is_complex = any(keyword in question_lower for keyword in complex_keywords) or content_length > 1000
            
            if is_complex:
                # For complex requests, use model's full capacity
                max_tokens = model_config.max_tokens
            else:
                # For simple requests, use conservative limit
                max_tokens = min(model_config.max_tokens, 2048)
            
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=model_config.temperature,
                messages=messages
            )
            
            raw_content = response.choices[0].message.content
            
            # Check if response was truncated
            finish_reason = response.choices[0].finish_reason
            was_truncated = finish_reason == "length"
            
            # Debug logging
            print(f"Model: {model}, Max tokens used: {max_tokens}, Finish reason: {finish_reason}, Content length: {len(raw_content)}")
            
            # Clean the response (remove thinking tags unless user wants to see them)
            if show_thinking:
                # Keep thinking tags but clean other markdown
                cleaned_content = self._clean_markdown_only(raw_content)
            else:
                # Remove thinking tags and clean markdown
                cleaned_content = self._clean_markdown_formatting(raw_content)
            
            # Add truncation warning if needed
            if was_truncated:
                cleaned_content += "\n\n[NOTE] Response was truncated due to length limits. Consider breaking down complex requests into smaller parts for complete answers."
            
            return {
                "answer": cleaned_content,
                "raw_answer": raw_content if show_thinking else None,
                "model_used": model,
                "model_info": {
                    "name": model_config.name,
                    "description": model_config.description,
                    "strengths": model_config.strengths
                },
                "success": True,
                "fallback_used": False,
                "truncated": was_truncated,
                "tokens_used": max_tokens if was_truncated else None
            }
        except Exception as e:
            print(f"API call failed for model {model}: {str(e)}")
            raise e
    
    def _get_model_specific_prompt(self, model: str, content: str, question: str) -> str:
        """Get optimized system prompt for specific model"""
        
        if model in ["Qwen/Qwen3-235B-A22B", "Qwen/Qwen3-235B-A22B-Instruct-2507"]:
            # Check if this is a complex coding request
            question_lower = question.lower()
            complex_keywords = ["solve", "implement", "write code", "complete", "all problems"]
            is_coding_request = any(keyword in question_lower for keyword in complex_keywords)
            
            if is_coding_request:
                return """You are a Python programming expert. Provide complete, working code implementations.

CRITICAL INSTRUCTIONS:
- Provide COMPLETE Python code for each problem requested
- Include actual function implementations, not just explanations
- Use proper Python syntax with def statements
- Keep explanations brief - focus on CODE IMPLEMENTATION
- For multiple problems, solve ALL of them with working code
- Use plain text formatting only - NO markdown
- Structure: Brief explanation + Complete working code for each problem
- Prioritize COMPLETE CODE SOLUTIONS over lengthy analysis"""
            else:
                return """You are an expert code analyst and technical documentation specialist.

Instructions:
- Analyze code structure, functions, classes, and dependencies with precision
- Explain programming concepts clearly and provide actionable insights
- Identify potential issues, optimizations, and best practices
- Provide technical recommendations relevant to the programming language
- When analyzing APIs, focus on endpoints, parameters, and usage patterns
- For configuration files, explain settings and their implications
- Use plain text formatting only - NO markdown, asterisks, or special formatting
- Be precise, technical, and practical in your explanations
- Structure your response clearly with logical flow"""
            
        elif model == "deepseek-ai/DeepSeek-R1-0528":
            # Check if this is a complex coding request
            question_lower = question.lower()
            complex_keywords = ["solve", "implement", "write code", "complete", "all problems"]
            is_coding_request = any(keyword in question_lower for keyword in complex_keywords)
            
            if is_coding_request:
                return """You are a Python programming expert. CRITICAL: You MUST provide properly indented Python code.

INDENTATION RULES (EXTREMELY IMPORTANT):
- Use EXACTLY 4 spaces for each indentation level
- Function body: 4 spaces from left margin
- If/for/while body: 8 spaces from left margin (4 + 4)
- Nested blocks: 12 spaces from left margin (4 + 4 + 4)

EXAMPLE OF CORRECT INDENTATION:
def example_function(n):
    if n > 0:
        for i in range(n):
            print(i)
        return True
    else:
        return False

CRITICAL: Every line inside a function MUST be indented with 4 spaces.
Every line inside an if/for/while MUST be indented with 8 spaces.
DO NOT provide unindented code - it will not work."""
            else:
                return """You are an advanced reasoning specialist for complex analysis and research.

Instructions:
- Provide deep, analytical insights with step-by-step logical reasoning
- Break down complex concepts into understandable components
- Identify patterns, relationships, and underlying principles
- Support all conclusions with evidence from the document
- Use structured thinking and methodical analysis
- For research papers, focus on methodology, findings, and implications
- For academic content, explain theoretical frameworks and applications
- Use plain text formatting only - NO markdown, asterisks, or special formatting
- Prioritize accuracy and thorough analysis over brevity
- Show your reasoning process clearly"""
            
        else:  # Default Meta-Llama prompt
            return """You are an intelligent assistant helping users understand documents and answer questions.

Instructions:
- Provide clear, accurate, and helpful responses based on the document content
- Look carefully for specific details, numbers, dates, and key information
- If calculating totals or analyzing data, show your work step by step
- Be precise with monetary amounts, measurements, and technical specifications
- If information seems incomplete or unclear, mention what might be missing
- Adapt your response style to match the document type and user's question
- Use plain text formatting only - NO markdown, asterisks, or special formatting
- Use simple bullet points with dashes (-) if lists are needed
- Focus on being helpful and informative"""
    
    def _clean_markdown_formatting(self, text: str) -> str:
        """Remove markdown formatting and model-specific tags from AI response"""
        import re
        
        if not text:
            return text
        
        # CRITICAL: Remove DeepSeek and Qwen thinking tags first (these can be very long)
        # Remove <think>...</think> tags completely (DeepSeek R1 reasoning)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove <thinking>...</thinking> tags (alternative format)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove any other reasoning tags that might appear
        text = re.sub(r'<reason>.*?</reason>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<analysis>.*?</analysis>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Apply smart formatting for better user experience
        text = self._apply_smart_formatting(text)
        
        return text
    
    def _apply_smart_formatting(self, text: str) -> str:
        """Apply intelligent formatting to make responses look like professional chatbot output"""
        import re
        
        # Check if this looks like a coding response
        has_code = 'def ' in text and ('Problem' in text or 'problem' in text)
        
        if has_code:
            return self._format_coding_response(text)
        else:
            return self._format_general_response(text)
    
    def _format_coding_response(self, text: str) -> str:
        """Format coding responses with proper structure and indentation"""
        import re
        
        # Split by problems but preserve original formatting
        problems = re.split(r'Problem \d+:', text)
        
        formatted_parts = []
        
        for i, problem in enumerate(problems):
            if not problem.strip():
                continue
                
            problem = problem.strip()
            lines = problem.split('\n')
            
            # Extract title (first meaningful line)
            title = "Solution"
            for line in lines:
                if line.strip() and not line.strip().startswith('def'):
                    title = line.strip()
                    break
            
            # Find and preserve original code blocks
            code_lines = self._extract_original_code(problem)
            
            if code_lines and i > 0:  # Skip empty first split
                formatted_parts.append(f"## 🔹 {title}")
                formatted_parts.append("")
                formatted_parts.append("```python")
                # Apply auto-indentation to fix formatting issues
                properly_indented = self._auto_indent_python(code_lines)
                formatted_parts.extend(properly_indented)
                formatted_parts.append("```")
                formatted_parts.append("")
        
        if not formatted_parts:
            # Fallback: preserve any code we can find
            code_blocks = re.findall(r'def \w+.*?(?=def \w+|$)', text, re.DOTALL | re.MULTILINE)
            for i, code_block in enumerate(code_blocks):
                if code_block.strip():
                    # Extract function name for title
                    first_line = code_block.strip().split('\n')[0]
                    func_name = first_line.replace('def ', '').split('(')[0]
                    title = func_name.replace('_', ' ').title()
                    
                    formatted_parts.append(f"## 🔹 {title}")
                    formatted_parts.append("")
                    formatted_parts.append("```python")
                    # Apply auto-indentation for better formatting
                    code_lines = code_block.strip().split('\n')
                    properly_indented = self._auto_indent_python(code_lines)
                    formatted_parts.extend(properly_indented)
                    formatted_parts.append("```")
                    formatted_parts.append("")
        
        if not formatted_parts:
            return self._format_general_response(text)
        
        # Add friendly header
        result = "I've solved all the programming problems for you! Here are the complete Python implementations:\n\n"
        result += "💡 **Tip**: You can copy each code block and run it directly in Python!\n\n"
        result += "\n".join(formatted_parts)
        result += "\n\n🎯 **Ready to use**: All functions are properly formatted and ready to run!"
        
        return result
    
    def _extract_original_code(self, text: str) -> list:
        """Extract code while preserving original spacing and indentation"""
        import re
        
        # Find all function definitions and their bodies
        # Use a more permissive approach to capture indented code
        lines = text.split('\n')
        code_lines = []
        
        # Look for function definitions and capture everything until the next function or end
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # If we find a function definition, capture it and its body
            if stripped.startswith('def '):
                code_lines.append(stripped)
                i += 1
                
                # Capture the function body (indented lines)
                while i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    
                    # Stop if we hit another function or problem
                    if (next_stripped.startswith('def ') or 
                        next_stripped.startswith('Problem') or
                        next_stripped.startswith('class ')):
                        break
                    
                    # Include the line if it's part of the function (indented or empty)
                    if (not next_stripped or  # empty line
                        next_line.startswith('    ') or  # indented line
                        next_stripped.startswith('#') or  # comment
                        any(kw in next_stripped for kw in ['if ', 'for ', 'while ', 'return', 'print', 'else:', 'elif ', 'try:', 'except:', 'import ', 'from '])):
                        code_lines.append(next_stripped)
                    
                    i += 1
            else:
                i += 1
        
        return code_lines
    
    def _auto_indent_python(self, code_lines: list) -> list:
        """Fix Python indentation using a robust algorithm"""
        if not code_lines:
            return []
        
        # Join all lines and clean them
        code_text = '\n'.join(line.strip() for line in code_lines if line.strip())
        lines = code_text.split('\n')
        fixed_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                if stripped:
                    fixed_lines.append(stripped)
                continue
            
            # Handle dedent keywords first
            if any(stripped.startswith(kw) for kw in ['else:', 'elif ', 'except:', 'finally:']):
                indent_level = max(0, indent_level - 1)
            
            # Add line with proper indentation
            fixed_lines.append('    ' * indent_level + stripped)
            
            # Increase indent after colon
            if stripped.endswith(':'):
                indent_level += 1
            
            # Reset indent level for top-level definitions
            if stripped.startswith('def ') or stripped.startswith('class '):
                if indent_level == 0:
                    indent_level = 1
        
        return fixed_lines
    
    def _format_general_response(self, text: str) -> str:
        """Format general responses with better structure"""
        import re
        
        # Remove bold formatting (**text** or __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Remove italic formatting (*text* or _text_)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Convert markdown headers to clean headers
        text = re.sub(r'^#{1,6}\s*(.+)$', r'🔹 \1', text, flags=re.MULTILINE)
        
        # Convert markdown lists to clean bullet points
        text = re.sub(r'^\s*[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '• ', text, flags=re.MULTILINE)
        
        # Handle code blocks better
        text = re.sub(r'```(\w+)?\n(.*?)\n```', r'```\1\n\2\n```', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'`\1`', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        return text
    
    def _clean_markdown_only(self, text: str) -> str:
        """Clean only markdown formatting but keep thinking tags for debugging"""
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
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = text.strip()
        
        return text
    
    def get_model_recommendation(self, filename: str, content: str) -> Dict:
        """Get model recommendation with explanation"""
        recommended_model = self.model_selector.recommend_model(filename, content[:1000])
        explanation = self.model_selector.explain_recommendation(filename, content[:1000], recommended_model)
        
        return {
            "recommended_model": recommended_model,
            "explanation": explanation,
            "all_models": self.model_selector.get_all_models_info()
        }
    
    async def process_document_question(
        self, 
        extracted_text: str, 
        question: str, 
        file_type: str = "", 
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        show_thinking: bool = False
    ) -> Dict:
        """Process a document question - async wrapper for the main processing method"""
        try:
            result = self.process_with_model(
                content=extracted_text,
                question=question,
                model=model_id,
                system_prompt=system_prompt,
                filename=f"document.{file_type}" if file_type else "document.txt",
                show_thinking=show_thinking
            )
            return result
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")
    
    async def compare_models(
        self, 
        extracted_text: str, 
        question: str, 
        model_ids: List[str], 
        file_type: str = ""
    ) -> Dict:
        """Compare responses from multiple models for the same query - async version"""
        results = {}
        
        for model in model_ids:
            try:
                result = self.process_with_model(
                    content=extracted_text,
                    question=question,
                    model=model,
                    max_retries=0,  # No fallback for comparison
                    filename=f"document.{file_type}" if file_type else "document.txt"
                )
                results[model] = {
                    "answer": result["answer"],
                    "model_info": result["model_info"],
                    "processing_time": result["processing_time"],
                    "success": True
                }
            except Exception as e:
                results[model] = {
                    "error": str(e),
                    "success": False
                }
        
        return {
            "comparison_results": results,
            "models_compared": model_ids,
            "question": question
        }
    
    def get_available_models(self) -> Dict:
        """Get all available models with their configurations"""
        return self.model_selector.get_all_models_info()
    
    def get_default_model(self) -> str:
        """Get the default model ID"""
        return self.model_selector.default_model
    
    def recommend_model(self, file_type: str, file_size: int, content_preview: str) -> Dict:
        """Get enhanced model recommendation based on file characteristics and performance data"""
        filename = f"document.{file_type}" if file_type else "document.txt"
        
        # Use enhanced recommendation system
        enhanced_recommendation = self.model_selector.get_enhanced_recommendation(filename, content_preview)
        
        return {
            "model_id": enhanced_recommendation["recommended_model"],
            "model_name": enhanced_recommendation["model_name"],
            "reasons": enhanced_recommendation["reasons"],
            "confidence": enhanced_recommendation["confidence"],
            "score": enhanced_recommendation["score"],
            "alternatives": enhanced_recommendation["alternatives"]
        }
    
    def get_advanced_recommendation(
        self, 
        filename: str, 
        content_preview: str, 
        question_type: str = None, 
        complexity_level: str = None,
        user_preference: str = None
    ) -> Dict:
        """Get advanced model recommendation with detailed multi-factor analysis"""
        
        # Get advanced recommendation from model selector
        recommendation = self.model_selector.get_advanced_recommendation(
            filename=filename,
            content_preview=content_preview,
            question_type=question_type,
            complexity_level=complexity_level,
            user_preference=user_preference
        )
        
        # Get model configuration for additional details
        model_config = get_model_config(recommendation["model_id"])
        
        return {
            "model_id": recommendation["model_id"],
            "model_name": recommendation["model_name"],
            "confidence": recommendation["confidence"],
            "alternatives": recommendation["alternatives"],
            "factors": recommendation["factors"],
            "reasoning": recommendation["reasoning"],
            "model_details": {
                "description": model_config.description if model_config else "",
                "strengths": model_config.strengths if model_config else [],
                "max_tokens": model_config.max_tokens if model_config else 4096,
                "temperature": model_config.temperature if model_config else 0.7
            }
        }
    
    def record_model_performance(self, model_id: str, success: bool, processing_time: float = 0.0, user_satisfaction: int = None):
        """Record model performance for learning and optimization"""
        self.model_selector.track_model_performance(
            model_id=model_id,
            file_type="general",
            processing_time=processing_time,
            success=success,
            user_satisfaction=user_satisfaction
        )
    
    def get_model_performance_stats(self) -> Dict:
        """Get comprehensive model performance statistics"""
        return self.model_selector.get_model_performance_stats()