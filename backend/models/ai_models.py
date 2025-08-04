# backend/models/ai_models.py

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ModelConfig:
    name: str
    description: str
    strengths: List[str]
    best_for_extensions: List[str]
    best_for_content: List[str]
    max_tokens: int
    temperature: float
    is_default: bool = False

# Available AI Models Configuration
AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    "meta-llama/Meta-Llama-3.1-70B-Instruct": ModelConfig(
        name="Meta Llama 3.1",
        description="General-purpose model for balanced analysis and conversation",
        strengths=[
            "General document analysis",
            "Q&A and conversation", 
            "Text summarization",
            "Balanced reasoning",
            "Multi-domain knowledge"
        ],
        best_for_extensions=[".txt", ".pdf", ".docx", ".md", ".rtf"],
        best_for_content=["general", "summary", "question", "conversation"],
        max_tokens=4096,
        temperature=0.6,
        is_default=True
    ),
    
    "deepseek-ai/DeepSeek-R1-0528": ModelConfig(
        name="DeepSeek R1",
        description="Advanced reasoning model for complex analysis and research",
        strengths=[
            "Complex reasoning and analysis",
            "Mathematical problem solving",
            "Research paper analysis", 
            "Academic content understanding",
            "Logical deduction",
            "Scientific reasoning"
        ],
        best_for_extensions=[".pdf", ".tex", ".md", ".docx"],
        best_for_content=[
            "research", "academic", "analysis", "mathematical", "scientific",
            "theorem", "hypothesis", "methodology", "conclusion", "abstract",
            "equation", "formula", "proof", "study", "experiment"
        ],
        max_tokens=8192,
        temperature=0.4
    ),
    
    "Qwen/Qwen3-235B-A22B-Instruct-2507": ModelConfig(
        name="Qwen3 Coder (Latest)",
        description="Latest specialized model for code analysis and technical documentation",
        strengths=[
            "Advanced code analysis and review",
            "Programming concept explanation",
            "Technical documentation",
            "API documentation analysis",
            "Software architecture understanding",
            "Debugging assistance",
            "Code optimization suggestions"
        ],
        best_for_extensions=[
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".sh", ".html", 
            ".xml", ".json", ".yaml", ".yml", ".sql", ".css", ".scss",
            ".php", ".rb", ".go", ".rs", ".kt", ".swift", ".ipynb"
        ],
        best_for_content=[
            "function", "class", "import", "def", "var", "const", "let",
            "public", "private", "static", "async", "await", "return",
            "if", "else", "for", "while", "try", "catch", "throw",
            "interface", "type", "enum", "struct", "namespace", "package",
            "api", "endpoint", "request", "response", "database", "query"
        ],
        max_tokens=32768,
        temperature=0.2
    ),
    
    "Qwen/Qwen3-235B-A22B": ModelConfig(
        name="Qwen3 Coder (Legacy)",
        description="Previous version - specialized model for code analysis",
        strengths=[
            "Code analysis and review",
            "Programming concept explanation",
            "Technical documentation",
            "API documentation analysis"
        ],
        best_for_extensions=[
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".sh", ".html", 
            ".xml", ".json", ".yaml", ".yml", ".sql", ".css", ".scss"
        ],
        best_for_content=[
            "function", "class", "import", "def", "var", "const", "let",
            "public", "private", "static", "async", "await", "return"
        ],
        max_tokens=32768,
        temperature=0.2
    )
}

def get_model_config(model_id: str) -> Optional[ModelConfig]:
    """Get configuration for a specific model"""
    return AVAILABLE_MODELS.get(model_id)

def get_default_model() -> str:
    """Get the default model ID"""
    for model_id, config in AVAILABLE_MODELS.items():
        if config.is_default:
            return model_id
    return list(AVAILABLE_MODELS.keys())[0]

def get_all_models() -> Dict[str, ModelConfig]:
    """Get all available models"""
    return AVAILABLE_MODELS