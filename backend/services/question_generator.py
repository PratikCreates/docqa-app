"""
AI Question Generation Service for creating contextually relevant questions from document content
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from services.multi_model_ai import MultiModelAIService
from services.cache_service import cache_service
import json
import hashlib

class QuestionCategory:
    """Question category constants"""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    SUMMARY = "summary"
    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"
    IMPLEMENTATION = "implementation"

class Question:
    """Question data structure"""
    def __init__(self, text: str, category: str, relevance_score: float, 
                 context: str = "", follow_ups: List[str] = None):
        self.text = text
        self.category = category
        self.relevance_score = relevance_score
        self.context = context
        self.follow_ups = follow_ups or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "category": self.category,
            "relevance_score": self.relevance_score,
            "context": self.context,
            "follow_ups": self.follow_ups
        }

class QuestionGeneratorService:
    """Service for generating contextually relevant questions from document content"""
    
    def __init__(self):
        self.ai_service = None  # Initialize lazily
        self.cache_prefix = "questions:"
        self.cache_expire_seconds = 3600  # 1 hour
        
        # Question templates by document category
        self.question_templates = {
            "code": {
                QuestionCategory.TECHNICAL: [
                    "What is the main purpose of this code?",
                    "How does the {main_function} function work?",
                    "What design patterns are used in this implementation?",
                    "What are the key dependencies and imports?",
                    "How is error handling implemented?"
                ],
                QuestionCategory.DEBUGGING: [
                    "What potential bugs or issues could arise in this code?",
                    "Are there any security vulnerabilities to consider?",
                    "What edge cases might not be handled properly?",
                    "How could this code fail under high load?"
                ],
                QuestionCategory.OPTIMIZATION: [
                    "How can this code be optimized for better performance?",
                    "What are the time and space complexity considerations?",
                    "Are there any redundant operations that can be eliminated?",
                    "How can memory usage be reduced?"
                ],
                QuestionCategory.IMPLEMENTATION: [
                    "How would you extend this code to handle {new_feature}?",
                    "What tests should be written for this code?",
                    "How would you refactor this for better maintainability?",
                    "What documentation is needed for this implementation?"
                ]
            },
            "research": {
                QuestionCategory.ANALYTICAL: [
                    "What is the main research question or hypothesis?",
                    "What methodology was used in this study?",
                    "What are the key findings and conclusions?",
                    "What are the limitations of this research?",
                    "How do these findings compare to previous work?"
                ],
                QuestionCategory.SUMMARY: [
                    "What are the main points covered in this document?",
                    "What is the significance of this research?",
                    "What are the practical implications of these findings?",
                    "What future research directions are suggested?"
                ],
                QuestionCategory.FACTUAL: [
                    "What data sources were used in this study?",
                    "What statistical methods were employed?",
                    "What is the sample size and population?",
                    "What are the key metrics and measurements?"
                ]
            },
            "documentation": {
                QuestionCategory.SUMMARY: [
                    "What is the main topic of this documentation?",
                    "What are the key concepts explained?",
                    "What procedures or processes are described?",
                    "What are the main sections and their purposes?"
                ],
                QuestionCategory.FACTUAL: [
                    "What specific steps are outlined in this guide?",
                    "What tools or technologies are mentioned?",
                    "What are the system requirements?",
                    "What configuration options are available?"
                ],
                QuestionCategory.IMPLEMENTATION: [
                    "How would you implement the described solution?",
                    "What are the best practices mentioned?",
                    "What common pitfalls should be avoided?",
                    "How can this be customized for different use cases?"
                ]
            },
            "general": {
                QuestionCategory.SUMMARY: [
                    "What are the main points of this document?",
                    "What is the central theme or message?",
                    "What key information is presented?",
                    "What conclusions can be drawn?"
                ],
                QuestionCategory.ANALYTICAL: [
                    "What are the strengths and weaknesses discussed?",
                    "What relationships or patterns are evident?",
                    "What causes and effects are identified?",
                    "What comparisons are made?"
                ],
                QuestionCategory.FACTUAL: [
                    "What specific facts or data are presented?",
                    "What dates, numbers, or statistics are mentioned?",
                    "Who are the key people or organizations involved?",
                    "What locations or places are referenced?"
                ]
            }
        }
    
    async def generate_questions(self, content: str, document_category: str = "general", 
                               filename: str = "", max_questions: int = 10,
                               user_preferences: Dict[str, Any] = None) -> List[Question]:
        """
        Generate contextually relevant questions from document content
        
        Args:
            content: Document text content
            document_category: Category of document (code, research, documentation, etc.)
            filename: Original filename for context
            max_questions: Maximum number of questions to generate
            user_preferences: User preferences for question types
            
        Returns:
            List of Question objects ranked by relevance
        """
        
        # Check cache first
        cache_key = self._generate_cache_key(content, document_category, max_questions)
        cached_questions = cache_service.get(cache_key)
        if cached_questions:
            return [Question(**q) for q in cached_questions]
        
        try:
            # Analyze document content
            content_analysis = self._analyze_content(content, document_category, filename)
            
            # Generate questions using multiple approaches
            ai_questions = await self._generate_ai_questions(content, content_analysis, max_questions)
            
            # If AI questions failed or returned few results, generate more template questions
            template_count = max_questions // 2 if len(ai_questions) > 0 else max_questions
            template_questions = self._generate_template_questions(content_analysis, template_count)
            
            # Combine and deduplicate questions
            all_questions = ai_questions + template_questions
            unique_questions = self._deduplicate_questions(all_questions)
            
            # Rank questions by relevance
            ranked_questions = self._rank_questions(unique_questions, content_analysis, user_preferences)
            
            # Limit to max_questions
            final_questions = ranked_questions[:max_questions]
            
            # Cache results
            cache_data = [q.to_dict() for q in final_questions]
            cache_service.set(cache_key, cache_data, self.cache_expire_seconds)
            
            return final_questions
            
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            # Fallback to template questions only
            content_analysis = self._analyze_content(content, document_category, filename)
            return self._generate_template_questions(content_analysis, max_questions)
    
    def _analyze_content(self, content: str, document_category: str, filename: str) -> Dict[str, Any]:
        """Analyze document content to extract key information for question generation"""
        
        analysis = {
            "category": document_category,
            "filename": filename,
            "content_length": len(content),
            "word_count": len(content.split()),
            "complexity": "medium",
            "key_entities": [],
            "main_topics": [],
            "technical_terms": [],
            "programming_languages": [],
            "frameworks": [],
            "functions": [],
            "classes": [],
            "concepts": []
        }
        
        content_lower = content.lower()
        
        # Determine complexity based on content characteristics
        if document_category == "code":
            # Count functions, classes, imports
            function_count = len(re.findall(r'\b(def|function|func)\s+\w+', content, re.IGNORECASE))
            class_count = len(re.findall(r'\b(class|interface|struct)\s+\w+', content, re.IGNORECASE))
            import_count = len(re.findall(r'\b(import|from|#include|require)\s+', content, re.IGNORECASE))
            
            complexity_score = function_count * 2 + class_count * 3 + import_count
            if complexity_score > 20:
                analysis["complexity"] = "high"
            elif complexity_score > 10:
                analysis["complexity"] = "medium"
            else:
                analysis["complexity"] = "low"
            
            # Extract programming elements
            analysis["functions"] = re.findall(r'\b(?:def|function|func)\s+(\w+)', content, re.IGNORECASE)
            analysis["classes"] = re.findall(r'\b(?:class|interface|struct)\s+(\w+)', content, re.IGNORECASE)
            
            # Detect programming languages
            language_indicators = {
                "python": ["def ", "import ", "print(", "__init__"],
                "javascript": ["function ", "const ", "let ", "console.log"],
                "java": ["public class", "public static", "System.out"],
                "cpp": ["#include", "std::", "int main"],
                "html": ["<html", "<div", "<script"],
                "css": ["{", "}", "@media"]
            }
            
            for lang, indicators in language_indicators.items():
                if any(indicator in content_lower for indicator in indicators):
                    analysis["programming_languages"].append(lang)
        
        elif document_category == "research":
            # Look for research-specific terms
            research_terms = ["methodology", "hypothesis", "analysis", "results", "conclusion", 
                            "study", "research", "data", "findings", "experiment"]
            analysis["concepts"] = [term for term in research_terms if term in content_lower]
            
            # Complexity based on academic language
            academic_indicators = ["furthermore", "however", "therefore", "consequently", 
                                 "methodology", "hypothesis", "statistical"]
            academic_score = sum(1 for indicator in academic_indicators if indicator in content_lower)
            
            if academic_score > 5:
                analysis["complexity"] = "high"
            elif academic_score > 2:
                analysis["complexity"] = "medium"
        
        # Extract key entities (simple approach)
        # Look for capitalized words that might be important terms
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        # Filter out common words
        common_words = {"The", "This", "That", "These", "Those", "And", "But", "Or", "For", "In", "On", "At", "To", "From"}
        analysis["key_entities"] = [word for word in set(capitalized_words) if word not in common_words][:10]
        
        # Extract main topics using simple keyword frequency
        words = re.findall(r'\b\w+\b', content_lower)
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only consider words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top frequent words as main topics
        analysis["main_topics"] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        analysis["main_topics"] = [topic[0] for topic in analysis["main_topics"]]
        
        return analysis
    
    async def _generate_ai_questions(self, content: str, content_analysis: Dict[str, Any], 
                                   max_questions: int) -> List[Question]:
        """Generate questions using AI models"""
        
        questions = []
        
        try:
            # Initialize AI service lazily
            if self.ai_service is None:
                try:
                    self.ai_service = MultiModelAIService()
                except Exception as e:
                    print(f"AI service initialization failed: {str(e)}")
                    return questions  # Return empty list if AI service fails
            
            # Choose appropriate model based on content
            model_id = self._select_model_for_questions(content_analysis)
            
            # Create prompt for question generation
            prompt = self._create_question_prompt(content, content_analysis, max_questions)
            
            # Get AI response
            response = await self.ai_service.process_with_model(
                content=content,
                question=prompt,
                model_id=model_id
            )
            
            # Parse AI response to extract questions
            ai_questions = self._parse_ai_questions(response.get("answer", ""), content_analysis)
            questions.extend(ai_questions)
            
        except Exception as e:
            print(f"Error generating AI questions: {str(e)}")
        
        return questions
    
    def _generate_template_questions(self, content_analysis: Dict[str, Any], 
                                   max_questions: int) -> List[Question]:
        """Generate questions using predefined templates"""
        
        questions = []
        category = content_analysis.get("category", "general")
        
        # Get templates for this category
        category_templates = self.question_templates.get(category, self.question_templates["general"])
        
        # Generate questions from each question type
        for question_type, templates in category_templates.items():
            for template in templates[:max_questions // len(category_templates)]:
                try:
                    # Fill in template placeholders
                    question_text = self._fill_template(template, content_analysis)
                    
                    # Calculate relevance score based on content match
                    relevance_score = self._calculate_template_relevance(question_text, content_analysis)
                    
                    question = Question(
                        text=question_text,
                        category=question_type,
                        relevance_score=relevance_score,
                        context=f"Generated from {category} template"
                    )
                    
                    questions.append(question)
                    
                except Exception as e:
                    print(f"Error generating template question: {str(e)}")
                    continue
        
        return questions
    
    def _fill_template(self, template: str, content_analysis: Dict[str, Any]) -> str:
        """Fill template placeholders with content-specific information"""
        
        filled_template = template
        
        # Replace common placeholders
        if "{main_function}" in template:
            if content_analysis.get("functions"):
                main_function = content_analysis["functions"][0]
                filled_template = filled_template.replace("{main_function}", main_function)
            else:
                # If no functions found, replace with generic term or skip this template
                filled_template = filled_template.replace("{main_function}", "main component")
        
        if "{new_feature}" in template:
            # Use a generic placeholder or main topic
            new_feature = content_analysis.get("main_topics", ["new functionality"])[0]
            filled_template = filled_template.replace("{new_feature}", new_feature)
        
        # Remove any remaining unfilled placeholders
        import re
        filled_template = re.sub(r'\{[^}]+\}', 'this content', filled_template)
        
        return filled_template
    
    def _calculate_template_relevance(self, question_text: str, content_analysis: Dict[str, Any]) -> float:
        """Calculate relevance score for template-based questions"""
        
        base_score = 0.7  # Base score for template questions
        
        # Boost score based on content match
        question_lower = question_text.lower()
        
        # Check if question mentions key entities or topics
        for entity in content_analysis.get("key_entities", []):
            if entity.lower() in question_lower:
                base_score += 0.1
        
        for topic in content_analysis.get("main_topics", []):
            if topic in question_lower:
                base_score += 0.05
        
        # Category-specific boosts
        category = content_analysis.get("category", "general")
        if category == "code" and any(term in question_lower for term in ["function", "code", "implementation"]):
            base_score += 0.1
        elif category == "research" and any(term in question_lower for term in ["study", "research", "findings"]):
            base_score += 0.1
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _select_model_for_questions(self, content_analysis: Dict[str, Any]) -> str:
        """Select the best AI model for question generation based on content"""
        
        category = content_analysis.get("category", "general")
        complexity = content_analysis.get("complexity", "medium")
        
        # Use Qwen3-Coder for code-related content
        if category == "code":
            return "Qwen/Qwen3-235B-A22B-Instruct-2507"
        
        # Use DeepSeek for complex research or analytical content
        elif category == "research" or complexity == "high":
            return "deepseek-ai/DeepSeek-R1-0528"
        
        # Use Meta-Llama for general content
        else:
            return "meta-llama/Meta-Llama-3.1-70B-Instruct"
    
    def _create_question_prompt(self, content: str, content_analysis: Dict[str, Any], 
                              max_questions: int) -> str:
        """Create a prompt for AI question generation"""
        
        category = content_analysis.get("category", "general")
        complexity = content_analysis.get("complexity", "medium")
        
        base_prompt = f"""
Based on the following {category} document, generate {max_questions} highly relevant and insightful questions that would help someone understand and analyze this content effectively.

The questions should be:
1. Contextually relevant to the content
2. Varied in type (factual, analytical, technical, strategic)
3. Appropriate for the {complexity} complexity level
4. Actionable and specific

Document content:
{content[:2000]}...

Please generate exactly {max_questions} questions, each on a new line, in this format:
[CATEGORY] Question text here

Categories to use: FACTUAL, ANALYTICAL, SUMMARY, TECHNICAL, STRATEGIC, DEBUGGING, OPTIMIZATION, IMPLEMENTATION

Questions:
"""
        
        return base_prompt
    
    def _parse_ai_questions(self, ai_response: str, content_analysis: Dict[str, Any]) -> List[Question]:
        """Parse AI response to extract structured questions"""
        
        questions = []
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.lower().startswith(('questions:', 'here are', 'based on')):
                continue
            
            # Try to parse category and question
            category = QuestionCategory.ANALYTICAL  # default
            question_text = line
            
            # Look for category markers
            if line.startswith('[') and ']' in line:
                try:
                    category_part, question_part = line.split(']', 1)
                    category_name = category_part.strip('[').strip().lower()
                    question_text = question_part.strip()
                    
                    # Map category names
                    category_mapping = {
                        'factual': QuestionCategory.FACTUAL,
                        'analytical': QuestionCategory.ANALYTICAL,
                        'summary': QuestionCategory.SUMMARY,
                        'technical': QuestionCategory.TECHNICAL,
                        'strategic': QuestionCategory.STRATEGIC,
                        'debugging': QuestionCategory.DEBUGGING,
                        'optimization': QuestionCategory.OPTIMIZATION,
                        'implementation': QuestionCategory.IMPLEMENTATION
                    }
                    
                    category = category_mapping.get(category_name, QuestionCategory.ANALYTICAL)
                    
                except:
                    # If parsing fails, use the whole line as question
                    pass
            
            # Remove numbering if present
            question_text = re.sub(r'^\d+\.\s*', '', question_text)
            
            if question_text and len(question_text) > 10:  # Minimum question length
                relevance_score = self._calculate_ai_question_relevance(question_text, content_analysis)
                
                question = Question(
                    text=question_text,
                    category=category,
                    relevance_score=relevance_score,
                    context="Generated by AI model"
                )
                
                questions.append(question)
        
        return questions
    
    def _calculate_ai_question_relevance(self, question_text: str, content_analysis: Dict[str, Any]) -> float:
        """Calculate relevance score for AI-generated questions"""
        
        base_score = 0.8  # Higher base score for AI questions
        
        question_lower = question_text.lower()
        
        # Check for content-specific terms
        for entity in content_analysis.get("key_entities", []):
            if entity.lower() in question_lower:
                base_score += 0.05
        
        for topic in content_analysis.get("main_topics", []):
            if topic in question_lower:
                base_score += 0.03
        
        # Penalize generic questions
        generic_terms = ["what", "how", "why", "when", "where"]
        generic_count = sum(1 for term in generic_terms if question_lower.startswith(term))
        if generic_count > 0:
            base_score -= 0.1
        
        # Boost specific, actionable questions
        specific_terms = ["implement", "optimize", "debug", "analyze", "compare", "evaluate"]
        if any(term in question_lower for term in specific_terms):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _deduplicate_questions(self, questions: List[Question]) -> List[Question]:
        """Remove duplicate or very similar questions"""
        
        unique_questions = []
        seen_questions = set()
        
        for question in questions:
            # Create a normalized version for comparison
            normalized = re.sub(r'[^\w\s]', '', question.text.lower())
            normalized = ' '.join(normalized.split())  # Normalize whitespace
            
            # Check for exact duplicates
            if normalized in seen_questions:
                continue
            
            # Check for very similar questions (simple similarity check)
            is_similar = False
            for seen in seen_questions:
                if self._calculate_similarity(normalized, seen) > 0.8:
                    is_similar = True
                    break
            
            if not is_similar:
                unique_questions.append(question)
                seen_questions.add(normalized)
        
        return unique_questions
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two text strings"""
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _rank_questions(self, questions: List[Question], content_analysis: Dict[str, Any], 
                       user_preferences: Dict[str, Any] = None) -> List[Question]:
        """Rank questions by relevance and user preferences"""
        
        # Apply user preferences if provided
        if user_preferences:
            preferred_categories = user_preferences.get("preferred_categories", [])
            for question in questions:
                if question.category in preferred_categories:
                    question.relevance_score += 0.1
        
        # Sort by relevance score (descending)
        return sorted(questions, key=lambda q: q.relevance_score, reverse=True)
    
    def _generate_cache_key(self, content: str, document_category: str, max_questions: int) -> str:
        """Generate cache key for question results"""
        
        # Create hash of content to avoid storing large content in key
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        
        return f"{self.cache_prefix}{content_hash}_{document_category}_{max_questions}"
    
    def categorize_questions(self, questions: List[Question]) -> Dict[str, List[Question]]:
        """Categorize questions by type"""
        
        categorized = {}
        
        for question in questions:
            category = question.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(question)
        
        return categorized
    
    def get_follow_up_questions(self, original_question: str, answer: str, 
                              content_analysis: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions based on original question and answer"""
        
        follow_ups = []
        
        # Simple rule-based follow-up generation
        question_lower = original_question.lower()
        
        if "what" in question_lower:
            follow_ups.extend([
                f"How does this relate to {content_analysis.get('main_topics', ['the main topic'])[0]}?",
                "Can you provide more specific examples?",
                "What are the implications of this?"
            ])
        
        elif "how" in question_lower:
            follow_ups.extend([
                "What are the potential challenges with this approach?",
                "Are there alternative methods to consider?",
                "What would be the next steps?"
            ])
        
        elif "why" in question_lower:
            follow_ups.extend([
                "What evidence supports this reasoning?",
                "How does this compare to other approaches?",
                "What would happen if this weren't the case?"
            ])
        
        return follow_ups[:3]  # Limit to 3 follow-ups

# Global question generator service instance
question_generator = QuestionGeneratorService()