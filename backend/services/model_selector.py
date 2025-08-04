# backend/services/model_selector.py

import re
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from models.ai_models import AVAILABLE_MODELS, get_default_model, ModelConfig

class ModelSelector:
    """Intelligent model selection based on document type, content, and performance tracking"""
    
    def __init__(self):
        self.models = AVAILABLE_MODELS
        self.default_model = get_default_model()
        self.performance_data = self._load_performance_data()
        self.user_preferences = self._load_user_preferences()
    
    def recommend_model(self, filename: str, content_preview: str = "", user_preference: str = None, question_type: str = None, complexity_level: str = None) -> str:
        """
        Recommend the best model based on file type, content, and user preference
        
        Args:
            filename: Name of the uploaded file
            content_preview: First 1000 characters of the document content
            user_preference: User's preferred model (if any)
            
        Returns:
            Model ID string
        """
        if user_preference and user_preference in self.models:
            return user_preference
        
        # Get file extension
        file_ext = f".{filename.lower().split('.')[-1]}" if '.' in filename else ""
        content_lower = content_preview.lower()
        
        # Score each model based on file type and content
        model_scores = {}
        
        for model_id, config in self.models.items():
            score = 0
            
            # File extension matching (high weight)
            if file_ext in config.best_for_extensions:
                score += 10
                # Prefer newer models
                if "Instruct-2507" in model_id:
                    score += 2
            
            # Content keyword matching (medium weight)
            content_matches = sum(1 for keyword in config.best_for_content 
                                if keyword in content_lower)
            score += content_matches * 2
            
            # Filename keyword matching (low weight)
            filename_matches = sum(1 for keyword in config.best_for_content 
                                 if keyword in filename.lower())
            score += filename_matches
            
            model_scores[model_id] = score
        
        # Return model with highest score, or default if no clear winner
        best_model = max(model_scores.items(), key=lambda x: x[1])
        
        if best_model[1] > 0:
            return best_model[0]
        else:
            return self.default_model
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        config = self.models.get(model_id)
        if not config:
            return None
            
        return {
            "id": model_id,
            "name": config.name,
            "description": config.description,
            "strengths": config.strengths,
            "best_for_extensions": config.best_for_extensions,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "is_default": config.is_default
        }
    
    def get_all_models_info(self) -> Dict[str, Dict]:
        """Get information about all available models"""
        return {
            model_id: self.get_model_info(model_id) 
            for model_id in self.models.keys()
        }
    
    def get_fallback_chain(self, primary_model: str) -> List[str]:
        """
        Get fallback model chain for reliability
        
        Args:
            primary_model: The primary model that failed
            
        Returns:
            List of model IDs to try in order
        """
        fallback_chain = []
        
        # Always try default model as first fallback
        if primary_model != self.default_model:
            fallback_chain.append(self.default_model)
        
        # Add other models as additional fallbacks
        for model_id in self.models.keys():
            if model_id not in [primary_model] + fallback_chain:
                fallback_chain.append(model_id)
        
        return fallback_chain
    
    def explain_recommendation(self, filename: str, content_preview: str, recommended_model: str) -> Dict:
        """
        Explain why a particular model was recommended
        
        Returns:
            Dictionary with explanation details
        """
        file_ext = f".{filename.lower().split('.')[-1]}" if '.' in filename else ""
        content_lower = content_preview.lower()
        
        config = self.models.get(recommended_model)
        if not config:
            return {"error": "Model not found"}
        
        reasons = []
        
        # Check file extension match
        if file_ext in config.best_for_extensions:
            reasons.append(f"File type '{file_ext}' is optimized for {config.name}")
        
        # Check content matches
        content_matches = [keyword for keyword in config.best_for_content 
                          if keyword in content_lower]
        if content_matches:
            reasons.append(f"Content contains technical terms: {', '.join(content_matches[:3])}")
        
        # Default reason
        if not reasons:
            reasons.append(f"{config.name} is the default model for general analysis")
        
        return {
            "recommended_model": recommended_model,
            "model_name": config.name,
            "reasons": reasons,
            "strengths": config.strengths,
            "confidence": min(len(reasons) * 0.3, 1.0)  # Simple confidence score
        }
    
    def _load_performance_data(self) -> Dict:
        """Load model performance data from storage"""
        try:
            with open('model_performance.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "model_metrics": {},
                "usage_stats": {},
                "success_rates": {},
                "avg_response_times": {},
                "user_satisfaction": {}
            }
    
    def _save_performance_data(self):
        """Save performance data to storage"""
        try:
            with open('model_performance.json', 'w') as f:
                json.dump(self.performance_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save performance data: {e}")
    
    def _load_user_preferences(self) -> Dict:
        """Load user preferences from storage"""
        try:
            with open('user_preferences.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "preferred_models": {},
                "file_type_preferences": {},
                "manual_selections": {},
                "feedback_history": {}
            }
    
    def _save_user_preferences(self):
        """Save user preferences to storage"""
        try:
            with open('user_preferences.json', 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            print(f"Failed to save user preferences: {e}")
    
    def track_model_performance(self, model_id: str, file_type: str, processing_time: float, 
                               success: bool, user_satisfaction: Optional[int] = None):
        """Track model performance metrics"""
        timestamp = datetime.now().isoformat()
        
        # Initialize model data if not exists
        if model_id not in self.performance_data["model_metrics"]:
            self.performance_data["model_metrics"][model_id] = {
                "total_uses": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "file_types": {},
                "recent_performance": []
            }
        
        metrics = self.performance_data["model_metrics"][model_id]
        
        # Update metrics
        metrics["total_uses"] += 1
        if success:
            metrics["successes"] += 1
        else:
            metrics["failures"] += 1
        
        metrics["total_time"] += processing_time
        
        # Track by file type
        if file_type not in metrics["file_types"]:
            metrics["file_types"][file_type] = {"uses": 0, "successes": 0, "avg_time": 0.0}
        
        file_metrics = metrics["file_types"][file_type]
        file_metrics["uses"] += 1
        if success:
            file_metrics["successes"] += 1
        
        # Update average time
        file_metrics["avg_time"] = (file_metrics["avg_time"] * (file_metrics["uses"] - 1) + processing_time) / file_metrics["uses"]
        
        # Keep recent performance history (last 50 uses)
        metrics["recent_performance"].append({
            "timestamp": timestamp,
            "file_type": file_type,
            "processing_time": processing_time,
            "success": success,
            "user_satisfaction": user_satisfaction
        })
        
        if len(metrics["recent_performance"]) > 50:
            metrics["recent_performance"] = metrics["recent_performance"][-50:]
        
        # Update global stats
        self.performance_data["usage_stats"][model_id] = metrics["total_uses"]
        self.performance_data["success_rates"][model_id] = metrics["successes"] / metrics["total_uses"]
        self.performance_data["avg_response_times"][model_id] = metrics["total_time"] / metrics["total_uses"]
        
        if user_satisfaction is not None:
            if model_id not in self.performance_data["user_satisfaction"]:
                self.performance_data["user_satisfaction"][model_id] = []
            self.performance_data["user_satisfaction"][model_id].append(user_satisfaction)
            # Keep only last 20 satisfaction scores
            if len(self.performance_data["user_satisfaction"][model_id]) > 20:
                self.performance_data["user_satisfaction"][model_id] = self.performance_data["user_satisfaction"][model_id][-20:]
        
        self._save_performance_data()
    
    def learn_user_preference(self, file_type: str, selected_model: str, was_recommended: bool):
        """Learn from user's model selection preferences"""
        if file_type not in self.user_preferences["file_type_preferences"]:
            self.user_preferences["file_type_preferences"][file_type] = {}
        
        file_prefs = self.user_preferences["file_type_preferences"][file_type]
        
        if selected_model not in file_prefs:
            file_prefs[selected_model] = {"selections": 0, "manual_overrides": 0}
        
        file_prefs[selected_model]["selections"] += 1
        
        if not was_recommended:
            file_prefs[selected_model]["manual_overrides"] += 1
            
            # Track manual selections globally
            if selected_model not in self.user_preferences["manual_selections"]:
                self.user_preferences["manual_selections"][selected_model] = 0
            self.user_preferences["manual_selections"][selected_model] += 1
        
        self._save_user_preferences()
    
    def get_enhanced_recommendation(self, filename: str, content_preview: str = "", 
                                  user_id: str = "default") -> Dict:
        """Get enhanced model recommendation using performance data and user preferences"""
        file_ext = f".{filename.lower().split('.')[-1]}" if '.' in filename else ""
        content_lower = content_preview.lower()
        
        # Get base recommendation
        base_recommendation = self.recommend_model(filename, content_preview)
        
        # Calculate enhanced scores for each model
        model_scores = {}
        
        for model_id, config in self.models.items():
            score = 0.0
            reasons = []
            
            # Base compatibility score
            if file_ext in config.best_for_extensions:
                score += 0.4
                reasons.append(f"Optimized for {file_ext} files")
            
            # Content matching score
            content_matches = [kw for kw in config.best_for_content if kw in content_lower]
            if content_matches:
                score += 0.3 * (len(content_matches) / len(config.best_for_content))
                reasons.append(f"Content matches: {', '.join(content_matches[:3])}")
            
            # Performance-based scoring
            if model_id in self.performance_data["success_rates"]:
                success_rate = self.performance_data["success_rates"][model_id]
                score += 0.2 * success_rate
                reasons.append(f"Success rate: {success_rate:.1%}")
            
            # User preference scoring
            file_type_key = file_ext or "general"
            if (file_type_key in self.user_preferences["file_type_preferences"] and
                model_id in self.user_preferences["file_type_preferences"][file_type_key]):
                
                user_selections = self.user_preferences["file_type_preferences"][file_type_key][model_id]["selections"]
                preference_score = min(user_selections / 10.0, 0.1)  # Max 0.1 bonus
                score += preference_score
                if user_selections > 2:
                    reasons.append(f"You've used this model {user_selections} times for {file_type_key} files")
            
            # User satisfaction scoring
            if model_id in self.performance_data["user_satisfaction"]:
                satisfaction_scores = self.performance_data["user_satisfaction"][model_id]
                if satisfaction_scores:
                    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                    score += 0.1 * (avg_satisfaction / 5.0)  # Assuming 1-5 scale
                    reasons.append(f"User satisfaction: {avg_satisfaction:.1f}/5")
            
            model_scores[model_id] = {
                "score": score,
                "reasons": reasons,
                "config": config
            }
        
        # Find the best model
        best_model_id = max(model_scores.keys(), key=lambda x: model_scores[x]["score"])
        best_model_data = model_scores[best_model_id]
        
        # Calculate confidence based on score difference
        sorted_scores = sorted(model_scores.values(), key=lambda x: x["score"], reverse=True)
        confidence = 0.5  # Base confidence
        if len(sorted_scores) > 1:
            score_diff = sorted_scores[0]["score"] - sorted_scores[1]["score"]
            confidence = min(0.5 + score_diff, 1.0)
        
        return {
            "recommended_model": best_model_id,
            "model_name": best_model_data["config"].name,
            "reasons": best_model_data["reasons"],
            "confidence": confidence,
            "score": best_model_data["score"],
            "alternatives": [
                {
                    "model_id": mid,
                    "name": data["config"].name,
                    "score": data["score"],
                    "reasons": data["reasons"][:2]  # Top 2 reasons
                }
                for mid, data in sorted(model_scores.items(), 
                                      key=lambda x: x[1]["score"], reverse=True)[1:3]
            ]
        }
    
    def get_model_performance_stats(self) -> Dict:
        """Get comprehensive model performance statistics"""
        stats = {
            "overview": {
                "total_models": len(self.models),
                "models_with_data": len(self.performance_data["model_metrics"]),
                "total_requests": sum(self.performance_data["usage_stats"].values()) if self.performance_data["usage_stats"] else 0
            },
            "model_rankings": [],
            "file_type_performance": {},
            "recent_trends": {}
        }
        
        # Calculate model rankings
        for model_id, config in self.models.items():
            if model_id in self.performance_data["model_metrics"]:
                metrics = self.performance_data["model_metrics"][model_id]
                success_rate = metrics["successes"] / metrics["total_uses"] if metrics["total_uses"] > 0 else 0
                avg_time = metrics["total_time"] / metrics["total_uses"] if metrics["total_uses"] > 0 else 0
                
                # Calculate user satisfaction
                satisfaction = 0
                if model_id in self.performance_data["user_satisfaction"]:
                    sat_scores = self.performance_data["user_satisfaction"][model_id]
                    satisfaction = sum(sat_scores) / len(sat_scores) if sat_scores else 0
                
                stats["model_rankings"].append({
                    "model_id": model_id,
                    "name": config.name,
                    "total_uses": metrics["total_uses"],
                    "success_rate": success_rate,
                    "avg_response_time": avg_time,
                    "user_satisfaction": satisfaction,
                    "composite_score": (success_rate * 0.4 + (1 - min(avg_time/10, 1)) * 0.3 + satisfaction/5 * 0.3)
                })
        
        # Sort by composite score
        stats["model_rankings"].sort(key=lambda x: x["composite_score"], reverse=True)
        
        return stats
    
    def _analyze_content_factors(self, filename: str, content_preview: str, question_type: str = None, complexity_level: str = None) -> Dict:
        """Analyze multiple factors for advanced model selection"""
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        content_lower = content_preview.lower()
        
        # File type analysis
        file_category = self._categorize_file_type(file_ext)
        
        # Content complexity analysis
        complexity = self._analyze_complexity(content_preview)
        
        # Technical vs conceptual analysis
        technical_score = self._calculate_technical_score(content_lower)
        conceptual_score = self._calculate_conceptual_score(content_lower)
        
        # Question type analysis
        question_category = self._categorize_question_type(question_type) if question_type else 'general'
        
        # Language and framework detection
        detected_languages = self._detect_programming_languages(content_preview)
        detected_frameworks = self._detect_frameworks(content_preview)
        
        return {
            'file_extension': file_ext,
            'file_category': file_category,
            'complexity': complexity,
            'technical_score': technical_score,
            'conceptual_score': conceptual_score,
            'question_category': question_category,
            'detected_languages': detected_languages,
            'detected_frameworks': detected_frameworks,
            'content_length': len(content_preview),
            'complexity_level': complexity_level or 'medium'
        }
    
    def _categorize_file_type(self, file_ext: str) -> str:
        """Categorize file type for model selection"""
        categories = {
            'code': ['py', 'js', 'ts', 'java', 'cpp', 'c', 'sh', 'go', 'rs', 'php'],
            'web': ['html', 'css', 'jsx', 'tsx', 'vue', 'svelte'],
            'data': ['json', 'xml', 'csv', 'yaml', 'yml'],
            'documentation': ['md', 'txt', 'rst'],
            'research': ['pdf', 'docx', 'tex'],
            'notebook': ['ipynb'],
            'config': ['ini', 'conf', 'cfg', 'toml']
        }
        
        for category, extensions in categories.items():
            if file_ext in extensions:
                return category
        return 'general'
    
    def _analyze_complexity(self, content: str) -> str:
        """Analyze content complexity"""
        lines = content.split('\n')
        
        # Complexity indicators
        nested_structures = content.count('    ') + content.count('\t')
        function_count = len(re.findall(r'\b(def|function|class|interface)\b', content, re.IGNORECASE))
        import_count = len(re.findall(r'\b(import|from|#include|require)\b', content, re.IGNORECASE))
        
        complexity_score = (nested_structures * 0.1) + (function_count * 2) + (import_count * 1.5)
        
        if complexity_score > 20:
            return 'high'
        elif complexity_score > 10:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_technical_score(self, content: str) -> int:
        """Calculate technical content score"""
        technical_keywords = [
            'function', 'class', 'import', 'def', 'var', 'const', 'let', 'public', 'private',
            'algorithm', 'data structure', 'api', 'database', 'server', 'client', 'framework',
            'library', 'module', 'package', 'dependency', 'version', 'build', 'deploy'
        ]
        
        return sum(1 for keyword in technical_keywords if keyword in content)
    
    def _calculate_conceptual_score(self, content: str) -> int:
        """Calculate conceptual/research content score"""
        conceptual_keywords = [
            'analysis', 'research', 'study', 'methodology', 'conclusion', 'abstract',
            'theory', 'concept', 'principle', 'approach', 'strategy', 'evaluation',
            'assessment', 'comparison', 'review', 'discussion', 'interpretation'
        ]
        
        return sum(1 for keyword in conceptual_keywords if keyword in content)
    
    def _categorize_question_type(self, question: str) -> str:
        """Categorize the type of question being asked"""
        if not question:
            return 'general'
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['explain', 'what', 'how', 'why', 'describe']):
            return 'explanatory'
        elif any(word in question_lower for word in ['debug', 'fix', 'error', 'problem', 'issue']):
            return 'debugging'
        elif any(word in question_lower for word in ['optimize', 'improve', 'better', 'performance']):
            return 'optimization'
        elif any(word in question_lower for word in ['implement', 'create', 'build', 'develop']):
            return 'implementation'
        elif any(word in question_lower for word in ['analyze', 'review', 'assess', 'evaluate']):
            return 'analysis'
        else:
            return 'general'
    
    def _detect_programming_languages(self, content: str) -> List[str]:
        """Detect programming languages in content"""
        language_patterns = {
            'python': [r'\bdef\s+\w+', r'\bimport\s+\w+', r'\bfrom\s+\w+\s+import', r'\bprint\s*\('],
            'javascript': [r'\bfunction\s+\w+', r'\bconst\s+\w+', r'\blet\s+\w+', r'\bconsole\.log'],
            'java': [r'\bpublic\s+class', r'\bpublic\s+static\s+void\s+main', r'\bSystem\.out\.println'],
            'cpp': [r'#include\s*<', r'\bstd::', r'\bint\s+main\s*\('],
            'html': [r'<\w+[^>]*>', r'<!DOCTYPE\s+html>'],
            'css': [r'\w+\s*{[^}]*}', r'@media\s+'],
            'sql': [r'\bSELECT\s+', r'\bFROM\s+', r'\bWHERE\s+', r'\bINSERT\s+INTO']
        }
        
        detected = []
        for language, patterns in language_patterns.items():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                detected.append(language)
        
        return detected
    
    def _detect_frameworks(self, content: str) -> List[str]:
        """Detect frameworks and libraries in content"""
        framework_patterns = {
            'react': [r'\bReact\b', r'\buseState\b', r'\buseEffect\b', r'\bJSX\b'],
            'vue': [r'\bVue\b', r'\bv-if\b', r'\bv-for\b'],
            'angular': [r'\bAngular\b', r'\b@Component\b', r'\bngOnInit\b'],
            'django': [r'\bdjango\b', r'\bmodels\.Model\b', r'\bHttpResponse\b'],
            'flask': [r'\bflask\b', r'\b@app\.route\b', r'\brender_template\b'],
            'express': [r'\bexpress\b', r'\bapp\.get\b', r'\bapp\.post\b'],
            'spring': [r'\b@SpringBootApplication\b', r'\b@RestController\b']
        }
        
        detected = []
        for framework, patterns in framework_patterns.items():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                detected.append(framework)
        
        return detected
    
    def get_advanced_recommendation(self, filename: str, content_preview: str = "", question_type: str = None, complexity_level: str = None, user_preference: str = None) -> Dict:
        """Get advanced model recommendation with detailed multi-factor analysis"""
        
        # Multi-factor analysis
        factors = self._analyze_content_factors(filename, content_preview, question_type, complexity_level)
        
        # Calculate advanced scores
        model_scores = {}
        
        for model_id, model_config in self.models.items():
            score = self._calculate_advanced_score(model_id, model_config, factors, user_preference)
            model_scores[model_id] = score
        
        # Apply performance history weighting
        weighted_scores = self._apply_performance_weighting(model_scores)
        
        # Find the best model
        best_model = max(weighted_scores.items(), key=lambda x: x[1])
        
        # Store recommendation for learning
        self._store_recommendation_data(filename, content_preview, best_model[0], factors)
        
        # Get alternatives
        alternatives = []
        sorted_models = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)[1:4]
        
        for model_id, score in sorted_models:
            config = self.models[model_id]
            alternatives.append({
                "model_id": model_id,
                "model_name": config.name,
                "score": round(score, 2),
                "success_rate": self._get_success_rate(model_id)
            })
        
        return {
            "model_id": best_model[0],
            "model_name": self.models[best_model[0]].name,
            "confidence": min(best_model[1] / 100.0, 1.0),
            "alternatives": alternatives,
            "factors": factors,
            "reasoning": self._generate_reasoning(best_model[0], factors)
        }
    
    def _calculate_advanced_score(self, model_id: str, model_config: ModelConfig, factors: Dict, user_preference: str = None) -> float:
        """Calculate advanced model score based on multiple factors"""
        score = 0.0
        
        # Base model capabilities score
        base_score = self._get_base_model_score(model_id, model_config, factors)
        score += base_score
        
        # File type specialization bonus
        specialization_bonus = self._get_specialization_bonus(model_id, model_config, factors)
        score += specialization_bonus
        
        # Complexity matching bonus
        complexity_bonus = self._get_complexity_bonus(model_id, model_config, factors)
        score += complexity_bonus
        
        # Question type matching bonus
        question_bonus = self._get_question_type_bonus(model_id, model_config, factors)
        score += question_bonus
        
        # Language/framework expertise bonus
        expertise_bonus = self._get_expertise_bonus(model_id, model_config, factors)
        score += expertise_bonus
        
        # User preference bonus
        if user_preference and user_preference.lower() in model_config.name.lower():
            score += 15.0
        
        return score
    
    def _get_base_model_score(self, model_id: str, model_config: ModelConfig, factors: Dict) -> float:
        """Get base score for model capabilities"""
        # Model-specific base scores based on general capabilities
        base_scores = {
            'meta-llama/Meta-Llama-3.1-70B-Instruct': 25.0,  # Balanced, good for general tasks
            'deepseek-ai/DeepSeek-R1-0528': 30.0,  # Strong reasoning and analysis
            'Qwen/Qwen3-235B-A22B-Instruct-2507': 35.0,  # Latest, most capable
            'Qwen/Qwen3-235B-A22B': 28.0  # Good but older version
        }
        
        return base_scores.get(model_id, 20.0)
    
    def _get_specialization_bonus(self, model_id: str, model_config: ModelConfig, factors: Dict) -> float:
        """Get bonus for model specialization in specific areas"""
        bonus = 0.0
        file_category = factors.get('file_category', 'general')
        
        # Qwen3 Coder specialization
        if 'qwen' in model_id.lower():
            if file_category in ['code', 'web', 'notebook']:
                bonus += 20.0
            elif factors.get('technical_score', 0) > factors.get('conceptual_score', 0):
                bonus += 15.0
        
        # DeepSeek reasoning specialization
        elif 'deepseek' in model_id.lower():
            if file_category in ['research', 'documentation']:
                bonus += 18.0
            elif factors.get('conceptual_score', 0) > factors.get('technical_score', 0):
                bonus += 12.0
            elif factors.get('complexity') == 'high':
                bonus += 10.0
        
        # Meta-Llama balanced approach
        elif 'meta-llama' in model_id.lower():
            if file_category in ['documentation', 'general']:
                bonus += 12.0
            elif factors.get('question_category') == 'explanatory':
                bonus += 10.0
        
        return bonus
    
    def _get_complexity_bonus(self, model_id: str, model_config: ModelConfig, factors: Dict) -> float:
        """Get bonus based on complexity matching"""
        complexity = factors.get('complexity', 'medium')
        
        # DeepSeek excels at high complexity
        if 'deepseek' in model_id.lower() and complexity == 'high':
            return 12.0
        
        # Qwen3 good for medium-high complexity
        elif 'qwen' in model_id.lower() and complexity in ['medium', 'high']:
            return 8.0
        
        # Meta-Llama good for low-medium complexity
        elif 'meta-llama' in model_id.lower() and complexity in ['low', 'medium']:
            return 6.0
        
        return 0.0
    
    def _get_question_type_bonus(self, model_id: str, model_config: ModelConfig, factors: Dict) -> float:
        """Get bonus based on question type matching"""
        question_category = factors.get('question_category', 'general')
        
        bonuses = {
            'deepseek-ai/DeepSeek-R1-0528': {
                'analysis': 10.0, 'debugging': 8.0, 'optimization': 12.0
            },
            'Qwen/Qwen3-235B-A22B-Instruct-2507': {
                'implementation': 12.0, 'debugging': 10.0, 'optimization': 8.0
            },
            'meta-llama/Meta-Llama-3.1-70B-Instruct': {
                'explanatory': 10.0, 'general': 8.0, 'analysis': 6.0
            }
        }
        
        model_bonuses = bonuses.get(model_id, {})
        return model_bonuses.get(question_category, 0.0)
    
    def _get_expertise_bonus(self, model_id: str, model_config: ModelConfig, factors: Dict) -> float:
        """Get bonus for language/framework expertise"""
        languages = factors.get('detected_languages', [])
        frameworks = factors.get('detected_frameworks', [])
        
        bonus = 0.0
        
        # Qwen3 Coder gets bonus for programming languages
        if 'qwen' in model_id.lower():
            bonus += len(languages) * 3.0
            bonus += len(frameworks) * 2.0
        
        # DeepSeek gets bonus for complex frameworks
        elif 'deepseek' in model_id.lower():
            complex_frameworks = ['react', 'angular', 'django', 'spring']
            bonus += len([f for f in frameworks if f in complex_frameworks]) * 4.0
        
        return min(bonus, 15.0)  # Cap the bonus
    
    def _apply_performance_weighting(self, model_scores: Dict[str, float]) -> Dict[str, float]:
        """Apply performance history weighting to scores"""
        weighted_scores = {}
        
        for model_id, score in model_scores.items():
            success_rate = self._get_success_rate(model_id)
            performance_multiplier = 0.8 + (success_rate * 0.4)  # 0.8 to 1.2 range
            weighted_scores[model_id] = score * performance_multiplier
        
        return weighted_scores
    
    def _get_success_rate(self, model_id: str) -> float:
        """Get success rate for a model"""
        if model_id in self.performance_data["success_rates"]:
            return self.performance_data["success_rates"][model_id]
        return 0.8  # Default success rate for new models
    
    def _store_recommendation_data(self, filename: str, content: str, recommended_model: str, factors: Dict):
        """Store recommendation data for learning"""
        # Store pattern for future learning
        pattern_key = f"{factors.get('file_category', 'general')}_{factors.get('complexity', 'medium')}"
        
        # This would typically store to a database or file for learning
        # For now, we'll just track in memory
        pass
    
    def _generate_reasoning(self, model_id: str, factors: Dict) -> List[str]:
        """Generate human-readable reasoning for the recommendation"""
        reasons = []
        config = self.models[model_id]
        
        # File type reasoning
        file_category = factors.get('file_category', 'general')
        if file_category != 'general':
            reasons.append(f"Optimized for {file_category} files")
        
        # Complexity reasoning
        complexity = factors.get('complexity', 'medium')
        if complexity == 'high' and 'deepseek' in model_id.lower():
            reasons.append("Excellent for complex reasoning tasks")
        elif 'qwen' in model_id.lower() and factors.get('technical_score', 0) > 0:
            reasons.append("Strong technical and coding capabilities")
        
        # Language/framework reasoning
        languages = factors.get('detected_languages', [])
        if languages and 'qwen' in model_id.lower():
            reasons.append(f"Specialized for {', '.join(languages[:2])} programming")
        
        # Performance reasoning
        success_rate = self._get_success_rate(model_id)
        if success_rate > 0.9:
            reasons.append(f"High success rate ({success_rate:.1%})")
        
        return reasons[:3]  # Return top 3 reasons