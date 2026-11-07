import React, { useState, useEffect } from "react";
import "./App.css";

interface ApiResponse {
  answer: string;
  extracted_text: string;
  file_type: string;
  model_used: string;
  model_info: {
    name: string;
    description: string;
    strengths: string[];
  };
  recommended_model: string;
  recommendation_explanation: {
    recommended_model: string;
    model_name: string;
    reasons: string[];
    confidence: number;
  };
  processing_time: number;
  fallback_used: boolean;
}

interface ModelInfo {
  id: string;
  name: string;
  description: string;
  strengths: string[];
  best_for_extensions: string[];
  max_tokens: number;
  temperature: number;
  is_default: boolean;
}

interface SupportedFormats {
  supported_formats: {
    images: string[];
    documents: string[];
    code_files: string[];
    notebooks: string[];
    data_files: string[];
  };
}

// Enhanced copy function with better debugging and error handling
const copyToClipboard = async (text: string, btn: HTMLButtonElement, originalText: string) => {
  console.log('🔍 Copy attempt started:', { textLength: text.length, hasClipboard: !!navigator.clipboard, isSecure: window.isSecureContext });
  
  // Method 1: Try modern Clipboard API
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      console.log('✅ Modern Clipboard API success');
      
      // Success feedback
      btn.textContent = '✅ Copied!';
      btn.style.backgroundColor = '#4CAF50';
      btn.classList.add('copied');
      
      setTimeout(() => {
        btn.textContent = originalText;
        btn.style.backgroundColor = '';
        btn.classList.remove('copied');
      }, 2000);
      
      return true;
    } catch (err) {
      console.error('❌ Modern Clipboard API failed:', err);
      // Fall through to fallback method
    }
  } else {
    console.log('⚠️ Modern Clipboard API not available, using fallback');
  }
  
  // Method 2: Fallback using execCommand
  const textArea = document.createElement('textarea');
  textArea.value = text;
  
  // Better positioning to avoid visual glitches
  textArea.style.position = 'fixed';
  textArea.style.top = '0';
  textArea.style.left = '0';
  textArea.style.width = '2em';
  textArea.style.height = '2em';
  textArea.style.padding = '0';
  textArea.style.border = 'none';
  textArea.style.outline = 'none';
  textArea.style.boxShadow = 'none';
  textArea.style.background = 'transparent';
  textArea.style.opacity = '0';
  textArea.style.pointerEvents = 'none';
  
  document.body.appendChild(textArea);
  
  try {
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, 99999); // For mobile devices
    
    const successful = document.execCommand('copy');
    console.log('📋 execCommand result:', successful);
    
    if (successful) {
      console.log('✅ Fallback copy success');
      
      // Success feedback
      btn.textContent = '✅ Copied!';
      btn.style.backgroundColor = '#4CAF50';
      btn.classList.add('copied');
      
      setTimeout(() => {
        btn.textContent = originalText;
        btn.style.backgroundColor = '';
        btn.classList.remove('copied');
      }, 2000);
      
      return true;
    } else {
      throw new Error('execCommand returned false');
    }
  } catch (err) {
    console.error('❌ Fallback copy failed:', err);
    
    // Error feedback
    btn.textContent = '❌ Failed';
    btn.style.backgroundColor = '#dc3545';
    
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.backgroundColor = '';
    }, 3000);
    
    return false;
  } finally {
    document.body.removeChild(textArea);
  }
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [extractedText, setExtractedText] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [showExtractedText, setShowExtractedText] = useState(false);
  const [supportedFormats, setSupportedFormats] = useState<SupportedFormats | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [availableModels, setAvailableModels] = useState<{[key: string]: ModelInfo}>({});
  const [recommendedModel, setRecommendedModel] = useState<string>("");
  const [modelRecommendation, setModelRecommendation] = useState<any>(null);
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);
  const [showModelComparison, setShowModelComparison] = useState(false);
  const [comparisonResults, setComparisonResults] = useState<any>(null);
  const [generatedQuestions, setGeneratedQuestions] = useState<any[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [savedQuestions, setSavedQuestions] = useState<any[]>([]);
  const [favoriteQuestions, setFavoriteQuestions] = useState<Set<string>>(new Set());
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [questionHistory, setQuestionHistory] = useState<string[]>([]);
  const [showQuestionManager, setShowQuestionManager] = useState(false);
  const [isQuestionSectionCollapsed, setIsQuestionSectionCollapsed] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  useEffect(() => {
    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldUseDark = savedTheme === 'dark' || (!savedTheme && prefersDark);
    
    setIsDarkMode(shouldUseDark);
    document.documentElement.setAttribute('data-theme', shouldUseDark ? 'dark' : 'light');
    
    // Fetch supported formats and available models on component mount
    Promise.all([
      fetch("/supported-formats").then(res => res.json()),
      fetch("/models").then(res => res.json())
    ])
      .then(([formatsData, modelsData]) => {
        setSupportedFormats(formatsData);
        setAvailableModels(modelsData.available_models);
        setSelectedModel(modelsData.default_model);
      })
      .catch(err => console.error("Failed to fetch initial data:", err));
  }, []);

  // Theme toggle function
  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    const themeValue = newTheme ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', themeValue);
    localStorage.setItem('theme', themeValue);
  };

  // Track if user has manually selected a model
  const [userHasManuallySelectedModel, setUserHasManuallySelectedModel] = useState(false);

  // Get model recommendation when file is selected
  useEffect(() => {
    if (file) {
      setIsLoadingRecommendation(true);
      const formData = new FormData();
      formData.append("file", file);
      
      fetch("/recommend-model", {
        method: "POST",
        body: formData,
      })
        .then(res => res.json())
        .then(data => {
          setRecommendedModel(data.recommended_model);
          setModelRecommendation(data.explanation);
          // Only auto-select recommended model if user hasn't manually chosen one
          if (!userHasManuallySelectedModel) {
            setSelectedModel(data.recommended_model);
          }
        })
        .catch(err => console.error("Failed to get model recommendation:", err))
        .finally(() => setIsLoadingRecommendation(false));
    }
  }, [file, userHasManuallySelectedModel]);

  const handleUpload = async () => {
    if (!file || !question.trim()) return;
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("question", question);
    if (selectedModel) {
      formData.append("model", selectedModel);
    }
    if (systemPrompt.trim()) {
      formData.append("system_prompt", systemPrompt);
    }

    setLoading(true);
    try {
      const res = await fetch("/ask", {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data: ApiResponse = await res.json();
      setAnswer(data.answer);
      setExtractedText(data.extracted_text);
      setApiResponse(data);
    } catch (err) {
      setAnswer(`⚠️ Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setExtractedText("");
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const uploadedFile = files[0];
      setFile(uploadedFile);
      generateQuestionsFromFile(uploadedFile);
    }
  };

  const getAcceptedFileTypes = () => {
    if (!supportedFormats || !supportedFormats.supported_formats) return "*";
    const { images, documents, code_files, notebooks, data_files } = supportedFormats.supported_formats;
    
    const allFormats = [
      ...(images || []).map(ext => `.${ext}`),
      ...(documents || []).map(ext => `.${ext}`),
      ...(code_files || []).map(ext => `.${ext}`),
      ...(notebooks || []).map(ext => `.${ext}`),
      ...(data_files || []).map(ext => `.${ext}`)
    ];
    
    return allFormats.length > 0 ? allFormats.join(",") : "*";
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const compareModels = async () => {
    if (!file || !question.trim()) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("question", question);
      formData.append("models", Object.keys(availableModels).slice(0, 3).join(","));
      const res = await fetch("/compare-models", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setComparisonResults(data);
      setShowModelComparison(true);
    } catch (err) {
      console.error("Model comparison failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const renderFormattedAnswer = (text: string): React.ReactElement[] => {
    const lines = text.split('\n');
    const elements: React.ReactElement[] = [];
    let inCodeBlock = false;
    let codeLines: string[] = [];
    let codeLanguage = '';
    
    lines.forEach((line, index) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          const currentCodeContent = codeLines.join('\n'); // Capture the code content before clearing
          elements.push(
            <div key={`code-${index}`} className="code-block">
              <div className="code-header">
                <span className="code-language">{codeLanguage || 'python'}</span>
                <button 
                  className="copy-code-btn"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    const btn = event.currentTarget as HTMLButtonElement;
                    const originalText = btn.textContent || '📋 Copy';
                    const codeText = currentCodeContent; // Use the captured content
                    
                    console.log('🔍 Simple copy attempt:', codeText.length, 'characters');
                    
                    // Simple direct approach
                    if (navigator.clipboard && window.isSecureContext) {
                      navigator.clipboard.writeText(codeText).then(() => {
                        console.log('✅ Direct clipboard success');
                        btn.textContent = '✅ Copied!';
                        btn.style.backgroundColor = '#4CAF50';
                        setTimeout(() => {
                          btn.textContent = originalText;
                          btn.style.backgroundColor = '';
                        }, 2000);
                      }).catch((err) => {
                        console.error('❌ Direct clipboard failed:', err);
                        // Simple fallback
                        const textarea = document.createElement('textarea');
                        textarea.value = codeText;
                        textarea.style.position = 'fixed';
                        textarea.style.opacity = '0';
                        textarea.style.left = '-9999px';
                        document.body.appendChild(textarea);
                        textarea.select();
                        
                        try {
                          const success = document.execCommand('copy');
                          console.log('📋 Simple fallback result:', success);
                          if (success) {
                            btn.textContent = '✅ Copied!';
                            btn.style.backgroundColor = '#4CAF50';
                            setTimeout(() => {
                              btn.textContent = originalText;
                              btn.style.backgroundColor = '';
                            }, 2000);
                          } else {
                            btn.textContent = '❌ Failed';
                            setTimeout(() => btn.textContent = originalText, 2000);
                          }
                        } catch (e) {
                          console.error('❌ Simple fallback error:', e);
                          btn.textContent = '❌ Failed';
                          setTimeout(() => btn.textContent = originalText, 2000);
                        }
                        
                        document.body.removeChild(textarea);
                      });
                    } else {
                      console.log('⚠️ No clipboard API, using execCommand');
                      // Direct execCommand
                      const textarea = document.createElement('textarea');
                      textarea.value = codeText;
                      textarea.style.position = 'fixed';
                      textarea.style.opacity = '0';
                      textarea.style.left = '-9999px';
                      document.body.appendChild(textarea);
                      textarea.select();
                      
                      try {
                        const success = document.execCommand('copy');
                        console.log('📋 Direct execCommand result:', success);
                        if (success) {
                          btn.textContent = '✅ Copied!';
                          btn.style.backgroundColor = '#4CAF50';
                          setTimeout(() => {
                            btn.textContent = originalText;
                            btn.style.backgroundColor = '';
                          }, 2000);
                        } else {
                          btn.textContent = '❌ Failed';
                          setTimeout(() => btn.textContent = originalText, 2000);
                        }
                      } catch (e) {
                        console.error('❌ Direct execCommand error:', e);
                        btn.textContent = '❌ Failed';
                        setTimeout(() => btn.textContent = originalText, 2000);
                      }
                      
                      document.body.removeChild(textarea);
                    }
                  }}
                >
                  📋 Copy
                </button>
              </div>
              <pre className="code-content">
                <code>{currentCodeContent}</code>
              </pre>
            </div>
          );
          codeLines = [];
          inCodeBlock = false;
          codeLanguage = '';
        } else {
          // Start code block
          inCodeBlock = true;
          codeLanguage = line.replace('```', '').trim();
        }
        return;
      }
      
      if (inCodeBlock) {
        codeLines.push(line);
        return;
      }
      
      // Handle headers
      if (line.startsWith('## 🔹')) {
        elements.push(
          <h3 key={index} className="problem-header">
            {line.replace('## 🔹', '').trim()}
          </h3>
        );
        return;
      }
      
      if (line.startsWith('🔹')) {
        elements.push(
          <h4 key={index} className="section-header">
            {line}
          </h4>
        );
        return;
      }
      
      // Handle bullet points
      if (line.startsWith('• ')) {
        elements.push(
          <div key={index} className="bullet-point">
            {line}
          </div>
        );
        return;
      }
      
      // Handle inline formatting (code and bold)
      if ((line.includes('`') && !line.startsWith('```')) || line.includes('**')) {
        let formattedLine: React.ReactNode[] = [line];
        
        // Handle inline code first
        if (line.includes('`') && !line.startsWith('```')) {
          const parts = line.split(/(`[^`]+`)/);
          formattedLine = parts.map((part, partIndex) => {
            if (part.startsWith('`') && part.endsWith('`')) {
              return (
                <code key={`code-${partIndex}`} className="inline-code">
                  {part.slice(1, -1)}
                </code>
              );
            }
            return part;
          });
        }
        
        // Handle bold text
        if (line.includes('**')) {
          const processedLine = formattedLine.map((item, itemIndex) => {
            if (typeof item === 'string' && item.includes('**')) {
              const boldParts = item.split(/(\*\*[^*]+\*\*)/);
              return boldParts.map((boldPart, boldIndex) => {
                if (boldPart.startsWith('**') && boldPart.endsWith('**')) {
                  return (
                    <strong key={`bold-${itemIndex}-${boldIndex}`} className="bold-text">
                      {boldPart.slice(2, -2)}
                    </strong>
                  );
                }
                return boldPart;
              });
            }
            return item;
          }).flat();
          formattedLine = processedLine;
        }
        
        elements.push(
          <p key={index} className="answer-line">
            {formattedLine}
          </p>
        );
        return;
      }
      
      // Regular text
      if (line.trim()) {
        elements.push(
          <p key={index} className="answer-line">
            {line}
          </p>
        );
      } else {
        elements.push(<br key={index} />);
      }
    });
    
    return elements;
  };

  const exportResults = (format: 'txt' | 'json') => {
    if (!answer || !file) return;

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${file.name.split('.')[0]}_analysis_${timestamp}`;

    let content: string;
    let mimeType: string;
    let extension: string;

    if (format === 'json') {
      const data = {
        document: {
          filename: file.name,
          size: file.size,
          type: file.type,
          processed_at: new Date().toISOString()
        },
        question: question,
        answer: answer,
        extracted_text: extractedText,
        system_prompt: systemPrompt || 'Default system prompt'
      };
      content = JSON.stringify(data, null, 2);
      mimeType = 'application/json';
      extension = 'json';
    } else {
      content = `Document Analysis Report
Generated: ${new Date().toLocaleString()}
Document: ${file.name}

Question: ${question}

Answer:
${answer}

${extractedText ? `\nExtracted Text:\n${extractedText}` : ''}
`;
      mimeType = 'text/plain';
      extension = 'txt';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exportExtractedText = () => {
    if (!extractedText || !file) return;

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${file.name.split('.')[0]}_extracted_text_${timestamp}`;
    
    const content = `Extracted Text from ${file.name}
Generated: ${new Date().toLocaleString()}
Original File Size: ${file.size} bytes
Extracted Text Length: ${extractedText.length} characters
Extraction Method: ${file.type.startsWith('image/') ? 'OCR (Optical Character Recognition)' : 'Direct Text Extraction'}

=== EXTRACTED CONTENT ===

${extractedText}

=== END OF EXTRACTED CONTENT ===

Note: This is the raw text extracted from your document before AI processing.
For Jupyter notebooks, this includes code, markdown, and output content.
For images, this is OCR-extracted text which may contain recognition errors.
For documents, this is the direct text content extraction.
`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const generateQuestionsFromFile = async (uploadedFile: File) => {
    if (!uploadedFile) return;
    
    setLoadingQuestions(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);
      formData.append("max_questions", "8");
      formData.append("document_category", "general");
      
      const response = await fetch("/generate-questions", {
        method: "POST",
        body: formData,
      });
      
      if (response.ok) {
        const result = await response.json();
        setGeneratedQuestions(result.questions || []);
        console.log("✅ Generated questions:", result);
      } else {
        console.error("❌ Failed to generate questions:", response.statusText);
        // Fallback to static suggestions
        setGeneratedQuestions([]);
      }
    } catch (error) {
      console.error("❌ Error generating questions:", error);
      setGeneratedQuestions([]);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const saveQuestion = (question: any) => {
    const questionWithId = {
      ...question,
      id: Date.now().toString(),
      savedAt: new Date().toISOString(),
      fileName: file?.name || 'Unknown'
    };
    
    setSavedQuestions(prev => {
      const exists = prev.find(q => q.text === question.text);
      if (exists) return prev;
      return [questionWithId, ...prev];
    });
    
    // Save to localStorage
    const saved = JSON.parse(localStorage.getItem('savedQuestions') || '[]');
    if (!saved.find((q: any) => q.text === question.text)) {
      saved.unshift(questionWithId);
      localStorage.setItem('savedQuestions', JSON.stringify(saved.slice(0, 50))); // Keep last 50
    }
  };

  const toggleFavorite = (questionId: string) => {
    setFavoriteQuestions(prev => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(questionId)) {
        newFavorites.delete(questionId);
      } else {
        newFavorites.add(questionId);
      }
      
      // Save to localStorage
      localStorage.setItem('favoriteQuestions', JSON.stringify(Array.from(newFavorites)));
      return newFavorites;
    });
  };

  const addToQuestionHistory = (questionText: string) => {
    setQuestionHistory(prev => {
      const newHistory = [questionText, ...prev.filter(q => q !== questionText)];
      const trimmedHistory = newHistory.slice(0, 20); // Keep last 20
      localStorage.setItem('questionHistory', JSON.stringify(trimmedHistory));
      return trimmedHistory;
    });
  };

  const selectQuestion = (questionText: string) => {
    setQuestion(questionText);
    addToQuestionHistory(questionText);
  };

  const getFilteredQuestions = () => {
    if (selectedCategory === "all") {
      return generatedQuestions;
    }
    return generatedQuestions.filter(q => q.category === selectedCategory);
  };

  const getQuestionCategories = () => {
    const categories = Array.from(new Set(generatedQuestions.map(q => q.category)));
    return categories.sort();
  };

  // Load saved data on component mount
  React.useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('savedQuestions') || '[]');
    const favorites = JSON.parse(localStorage.getItem('favoriteQuestions') || '[]');
    const history = JSON.parse(localStorage.getItem('questionHistory') || '[]');
    
    setSavedQuestions(saved);
    setFavoriteQuestions(new Set(favorites));
    setQuestionHistory(history);
  }, []);

  const getQuestionSuggestions = () => {
    // Return AI-generated questions if available, otherwise fallback to static
    if (generatedQuestions.length > 0) {
      return generatedQuestions.map(q => q.text);
    }
    
    // Fallback static suggestions
    if (!file) return [];
    
    const filename = file.name;
    const extension = filename.toLowerCase().split('.').pop();
    const name = filename.toLowerCase();

    // Smart suggestions based on file type and name
    if (extension === 'pdf' || name.includes('syllabus') || name.includes('course')) {
      return [
        "What is the course code and title?",
        "What are the learning objectives?",
        "What is the grading scheme?",
        "What are the prerequisites?"
      ];
    } else if (name.includes('invoice') || name.includes('receipt') || name.includes('bill')) {
      return [
        "What is the total amount?",
        "What items were purchased?",
        "What is the date of purchase?",
        "Who is the vendor?"
      ];
    } else if (name.includes('contract') || name.includes('agreement')) {
      return [
        "What are the key terms?",
        "What is the duration?",
        "Who are the parties involved?",
        "What are the payment terms?"
      ];
    } else if (name.includes('resume') || name.includes('cv')) {
      return [
        "What is the person's experience?",
        "What are their key skills?",
        "What is their education background?",
        "What are their contact details?"
      ];
    } else {
      return [
        "What is this document about?",
        "Summarize the key points",
        "What are the important dates?",
        "Extract all numbers and amounts"
      ];
    }
  };

  return (
    <div className="app-container">
      {/* Theme Toggle Button */}
      <button 
        className="theme-toggle" 
        onClick={toggleTheme}
        title={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
        aria-label={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
      >
        {isDarkMode ? '☀️' : '🌙'}
      </button>

      {/* Documentation Link */}
      <a 
        href="docs/homepage.html" 
        className="docs-link"
        title="View documentation homepage"
        aria-label="View documentation homepage"
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => {
          e.preventDefault();
          // Pass current theme to the docs page
          const currentTheme = isDarkMode ? 'dark' : 'light';
          window.open(`docs/homepage.html?theme=${currentTheme}`, '_blank');
        }}
      >
        📖
      </a>

      <div className="header">
        <h1>📚 DocuMind AI</h1>
        <p>Intelligent document analysis with multi-model AI • Upload any file and get instant insights</p>
      </div>

      <div className="main-content">
        {/* File Upload Section */}
        <div className="upload-section">
          <div 
            className={`file-drop-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept={getAcceptedFileTypes()}
              onChange={(e) => {
                const uploadedFile = e.target.files?.[0] || null;
                setFile(uploadedFile);
                if (uploadedFile) {
                  generateQuestionsFromFile(uploadedFile);
                }
              }}
              style={{ display: 'none' }}
            />
            
            {file ? (
              <div className="file-info">
                <div className="file-icon">📄</div>
                <div className="file-details">
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{formatFileSize(file.size)}</div>
                </div>
                <button 
                  className="remove-file"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                    setAnswer("");
                    setExtractedText("");
                  }}
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="drop-message">
                <div className="upload-icon">📁</div>
                <p>Drag & drop your file here or click to browse</p>
                {supportedFormats && (
                  <div className="supported-formats">
                    <small>
                      Supported: {[...supportedFormats.supported_formats.images, ...supportedFormats.supported_formats.documents].join(', ')}
                    </small>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Enhanced Model Selection */}
        {Object.keys(availableModels).length > 0 && (
          <div className="model-selection-section">
            <div className="section-header">
              <label htmlFor="model-select">🤖 AI Model Selection</label>
              {isLoadingRecommendation && (
                <div className="loading-indicator">
                  <span className="spinner-small"></span>
                  Getting recommendation...
                </div>
              )}
            </div>
            <div className="model-selector-container">
              <select
                id="model-select"
                value={selectedModel}
                onChange={(e) => {
                  setSelectedModel(e.target.value);
                  setUserHasManuallySelectedModel(true);
                }}
                className="model-select"
              >
                {Object.entries(availableModels).map(([modelId, modelInfo]) => (
                  <option key={modelId} value={modelId}>
                    {modelInfo.name} {modelId === recommendedModel ? "⭐ (Recommended)" : ""}
                  </option>
                ))}
              </select>
              {file && (
                <button
                  className="compare-models-btn"
                  onClick={() => setShowModelComparison(!showModelComparison)}
                  disabled={loading}
                >
                  📊 Compare Models
                </button>
              )}
            </div>
            {selectedModel && availableModels[selectedModel] && (
              <div className="model-info-card">
                <div className="model-header">
                  <h4>{availableModels[selectedModel].name}</h4>
                  <div className="model-specs">
                    <span className="spec-item">🎯 {availableModels[selectedModel].temperature}</span>
                    <span className="spec-item">📝 {availableModels[selectedModel].max_tokens} tokens</span>
                  </div>
                </div>
                <p className="model-description">{availableModels[selectedModel].description}</p>
                <div className="model-strengths">
                  <strong>Strengths:</strong>
                  <div className="strength-tags">
                    {availableModels[selectedModel].strengths.slice(0, 4).map((strength, index) => (
                      <span key={index} className="strength-tag">{strength}</span>
                    ))}
                  </div>
                </div>
                {modelRecommendation && selectedModel === recommendedModel && (
                  <div className="recommendation-explanation">
                    <div className="recommendation-header">
                      <span className="recommendation-badge">⭐ Recommended</span>
                      <span className="confidence-score">
                        {Math.round((modelRecommendation.confidence || 0) * 100)}% confidence
                      </span>
                    </div>
                    <p><strong>Why:</strong> {modelRecommendation.reasons?.join(", ")}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Question Input */}
        <div className="question-section">
          <label htmlFor="question">Your Question</label>
          <textarea
            id="question"
            placeholder="What would you like to know about this document?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
          />
          
          {/* Question Management Interface */}
          {file && (
            <div className="question-management">
              <div className="question-manager-header">
                <div className="header-left">
                  <h3>🤖 Smart Questions</h3>
                  <span className="question-count">
                    {generatedQuestions.length} questions
                  </span>
                </div>
                <div className="header-actions">
                  <button 
                    className="collapse-toggle"
                    onClick={() => setIsQuestionSectionCollapsed(!isQuestionSectionCollapsed)}
                    title={isQuestionSectionCollapsed ? "Expand questions" : "Collapse questions"}
                  >
                    {isQuestionSectionCollapsed ? '📈' : '📉'}
                  </button>
                  <button 
                    className="manager-toggle"
                    onClick={() => setShowQuestionManager(!showQuestionManager)}
                    title={showQuestionManager ? "Hide question manager" : "Show question manager"}
                    aria-label={showQuestionManager ? "Hide question manager" : "Show question manager"}
                  >
                    {showQuestionManager ? '📋' : '⚙️'}
                  </button>
                  {!loadingQuestions && (
                    <button 
                      className="regenerate-button"
                      onClick={() => generateQuestionsFromFile(file)}
                      disabled={loadingQuestions}
                      title="Regenerate smart questions for this document"
                      aria-label="Regenerate smart questions for this document"
                    >
                      🔄
                    </button>
                  )}
                </div>
              </div>

              {loadingQuestions && (
                <div className="loading-state">
                  <div className="loading-spinner"></div>
                  <span>Generating intelligent questions...</span>
                </div>
              )}

              {!loadingQuestions && generatedQuestions.length === 0 && (
                <div className="empty-state">
                  <div className="empty-icon">🤔</div>
                  <p>No questions generated yet</p>
                  <button 
                    className="generate-first-button"
                    onClick={() => generateQuestionsFromFile(file)}
                  >
                    Generate Questions
                  </button>
                </div>
              )}

              {!loadingQuestions && generatedQuestions.length > 0 && isQuestionSectionCollapsed && (
                <div className="questions-collapsed-view">
                  <div className="collapsed-summary">
                    {generatedQuestions.slice(0, 3).map((q, index) => (
                      <button
                        key={index}
                        className="collapsed-question-btn"
                        onClick={() => selectQuestion(q.text)}
                        title={q.text}
                      >
                        <span className={`mini-category category-${q.category}`}>
                          {q.category.charAt(0).toUpperCase()}
                        </span>
                        {q.text.length > 40 ? q.text.substring(0, 40) + '...' : q.text}
                      </button>
                    ))}
                    {generatedQuestions.length > 3 && (
                      <span className="more-questions">+{generatedQuestions.length - 3} more</span>
                    )}
                  </div>
                </div>
              )}

              {!loadingQuestions && generatedQuestions.length > 0 && !isQuestionSectionCollapsed && (
                <>
                  {showQuestionManager && (
                    <div className="question-manager-panel">
                      <div className="manager-tabs">
                        <button 
                          className={`tab ${selectedCategory === 'all' ? 'active' : ''}`}
                          onClick={() => setSelectedCategory('all')}
                        >
                          All ({generatedQuestions.length})
                        </button>
                        {getQuestionCategories().map(category => (
                          <button
                            key={category}
                            className={`tab ${selectedCategory === category ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(category)}
                          >
                            {category} ({generatedQuestions.filter(q => q.category === category).length})
                          </button>
                        ))}
                      </div>

                      <div className="manager-actions">
                        <div className="bulk-actions">
                          <button 
                            className="bulk-save"
                            onClick={() => generatedQuestions.forEach(saveQuestion)}
                          >
                            💾 Save All
                          </button>
                          <button 
                            className="bulk-clear"
                            onClick={() => setGeneratedQuestions([])}
                          >
                            🗑️ Clear All
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="questions-grid">
                    {getFilteredQuestions().map((questionData, index) => (
                      <div key={index} className="question-card">
                        <div className="question-header">
                          <span className={`category-badge category-${questionData.category}`}>
                            {questionData.category.toUpperCase()}
                          </span>
                          <div className="question-actions">
                            <button
                              className="action-btn save-btn"
                              onClick={() => saveQuestion(questionData)}
                              title="Save question"
                            >
                              💾
                            </button>
                            <button
                              className={`action-btn favorite-btn ${favoriteQuestions.has(questionData.text) ? 'favorited' : ''}`}
                              onClick={() => toggleFavorite(questionData.text)}
                              title="Add to favorites"
                            >
                              {favoriteQuestions.has(questionData.text) ? '⭐' : '☆'}
                            </button>
                          </div>
                        </div>
                        
                        <div className="question-content">
                          <p className="question-text">{questionData.text}</p>
                          <div className="question-meta">
                            <span className="relevance-score">
                              📊 {(questionData.relevance_score * 100).toFixed(0)}% relevance
                            </span>
                            {questionData.context && (
                              <span className="question-source">
                                🔗 {questionData.context}
                              </span>
                            )}
                          </div>
                        </div>

                        <button
                          className="use-question-btn"
                          onClick={() => selectQuestion(questionData.text)}
                        >
                          ✨ Use This Question
                        </button>
                      </div>
                    ))}
                  </div>

                  {(savedQuestions.length > 0 || questionHistory.length > 0) && (
                    <div className="saved-questions-section">
                      {savedQuestions.length > 0 && (
                        <>
                          <h4>💾 Saved Questions ({savedQuestions.length})</h4>
                          <div className="saved-questions-list">
                            {savedQuestions.slice(0, 3).map((savedQ, index) => (
                              <div key={index} className="saved-question-item">
                                <span className="saved-question-text">{savedQ.text}</span>
                                <div className="saved-question-meta">
                                  <small>{savedQ.fileName} • {new Date(savedQ.savedAt).toLocaleDateString()}</small>
                                  <button
                                    className="use-saved-btn"
                                    onClick={() => selectQuestion(savedQ.text)}
                                  >
                                    Use
                                  </button>
                                </div>
                              </div>
                            ))}
                            {savedQuestions.length > 3 && (
                              <button className="view-all-saved">
                                View all {savedQuestions.length} saved questions
                              </button>
                            )}
                          </div>
                        </>
                      )}
                      
                      {questionHistory.length > 0 && (
                        <>
                          <h4>📝 Recent Questions ({questionHistory.length})</h4>
                          <div className="question-history-list">
                            {questionHistory.slice(0, 3).map((historyQ, index) => (
                              <button
                                key={index}
                                className="history-question-btn"
                                onClick={() => setQuestion(historyQ)}
                              >
                                {historyQ}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
        {/* System Prompt Section */}
        <div className="system-prompt-section">
          <div className="section-header">
            <button 
              className="toggle-button"
              onClick={() => setShowSystemPrompt(!showSystemPrompt)}
            >
              ⚙️ Advanced Settings {showSystemPrompt ? '▼' : '▶'}
            </button>
          </div>
          
          {showSystemPrompt && (
            <div className="system-prompt-content">
              <label htmlFor="system-prompt">Custom System Prompt (Optional)</label>
              <textarea
                id="system-prompt"
                placeholder="Customize how the AI should respond (e.g., 'Be very detailed and technical' or 'Summarize in bullet points')"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={4}
              />
              <small>Leave empty to use the default prompt optimized for document analysis</small>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button 
          className={`submit-button ${loading ? 'loading' : ''}`}
          onClick={handleUpload} 
          disabled={loading || !file || !question.trim()}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Processing...
            </>
          ) : (
            <>
              🚀 Ask Question
            </>
          )}
        </button>

        {/* Enhanced Results Section */}
        {answer && (
          <div className="results-section">
            <div className="answer-card">
              <div className="answer-header">
                <h3>💡 Answer</h3>
                <button 
                  className="copy-answer-btn"
                  onClick={async (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    const btn = event.currentTarget as HTMLButtonElement;
                    const originalText = btn.textContent || '📋 Copy Answer';
                    
                    console.log('🔍 Answer copy button clicked:', { answerLength: answer.length });
                    
                    // Use the enhanced copy function
                    await copyToClipboard(answer, btn, originalText);
                  }}
                >
                  📋 Copy Answer
                </button>
                {apiResponse && (
                  <div className="model-performance-badge">
                    <div className="model-info-compact">
                      <span className="model-name">🤖 {apiResponse.model_info.name}</span>
                      <span className="processing-time">
                        ⏱️ {Math.round(apiResponse.processing_time * 1000)}ms
                      </span>
                      {apiResponse.fallback_used && (
                        <span className="fallback-indicator">⚠️ Fallback</span>
                      )}
                    </div>
                    <div className="model-quality-indicators">
                      <span className="quality-indicator success">✅ Success</span>
                      <span className="attempts-indicator">
                        🔄 {(apiResponse as any).attempts || 1} attempt{((apiResponse as any).attempts || 1) > 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              <div className="answer-content">
                {renderFormattedAnswer(answer)}
              </div>
              {/* Enhanced Model Performance Info */}
              {apiResponse && (
                <div className="model-performance-section">
                  <details className="performance-details">
                    <summary className="performance-summary">
                      🔍 Model Performance & Insights
                    </summary>
                    <div className="performance-content">
                      <div className="performance-grid">
                        <div className="performance-item">
                          <span className="performance-label">Model:</span>
                          <span className="performance-value">{apiResponse.model_info.name}</span>
                        </div>
                        <div className="performance-item">
                          <span className="performance-label">Processing Time:</span>
                          <span className="performance-value">{Math.round(apiResponse.processing_time * 1000)}ms</span>
                        </div>
                        <div className="performance-item">
                          <span className="performance-label">Response Length:</span>
                          <span className="performance-value">{answer.length} characters</span>
                        </div>
                        <div className="performance-item">
                          <span className="performance-label">Reliability:</span>
                          <span className="performance-value">
                            {apiResponse.fallback_used ? 'Fallback used' : 'Primary model'}
                          </span>
                        </div>
                      </div>
                      <div className="model-strengths-section">
                        <strong>Model Capabilities:</strong>
                        <div className="capability-tags">
                          {apiResponse.model_info.strengths.map((strength, index) => (
                            <span key={index} className="capability-tag">{strength}</span>
                          ))}
                        </div>
                      </div>
                      {apiResponse.recommendation_explanation && (
                        <div className="recommendation-insight">
                          <strong>Why this model was chosen:</strong>
                          <p>{apiResponse.recommendation_explanation.reasons?.join(", ")}</p>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}
              {/* Action Buttons */}
              <div className="action-buttons">
                <div className="export-options">
                  <button 
                    className="export-button"
                    onClick={() => exportResults('txt')}
                  >
                    📄 Export Answer
                  </button>
                  <button 
                    className="export-button"
                    onClick={() => exportResults('json')}
                  >
                    📋 Export JSON
                  </button>
                  <button 
                    className="export-button"
                    onClick={() => exportExtractedText()}
                  >
                    📝 Export Extracted Text
                  </button>
                </div>
                {file && (
                  <button 
                    className="compare-button"
                    onClick={compareModels}
                    disabled={loading}
                  >
                    📊 Compare Models
                  </button>
                )}
              </div>
            </div>

            {/* Model Comparison Results */}
            {showModelComparison && comparisonResults && (
              <div className="model-comparison-section">
                <div className="comparison-header">
                  <h3>📊 Model Comparison Results</h3>
                  <button 
                    className="close-comparison"
                    onClick={() => setShowModelComparison(false)}
                  >
                    ✕
                  </button>
                </div>
                <div className="comparison-grid">
                  {Object.entries(comparisonResults.comparison_results).map(([modelId, result]: [string, any]) => (
                    <div key={modelId} className={`comparison-card ${result.success ? 'success' : 'failed'}`}>
                      <div className="comparison-card-header">
                        <h4>{availableModels[modelId]?.name || modelId}</h4>
                        <div className="comparison-metrics">
                          {result.success ? (
                            <>
                              <span className="metric">⏱️ {Math.round(result.processing_time * 1000)}ms</span>
                              <span className="metric">📝 {result.answer.length} chars</span>
                              <span className="status success">✅ Success</span>
                            </>
                          ) : (
                            <span className="status failed">❌ Failed</span>
                          )}
                        </div>
                      </div>
                      {result.success ? (
                        <div className="comparison-answer">
                          <p>{result.answer.substring(0, 200)}...</p>
                          <details>
                            <summary>View full response</summary>
                            <div className="full-answer">
                              {result.answer.split('\n').map((line: string, index: number) => (
                                <p key={index}>{line}</p>
                              ))}
                            </div>
                          </details>
                        </div>
                      ) : (
                        <div className="comparison-error">
                          <p>Error: {result.error}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="comparison-insights">
                  <h4>🎯 Comparison Insights</h4>
                  <div className="insights-grid">
                    <div className="insight-item">
                      <span className="insight-label">Fastest Response:</span>
                      <span className="insight-value">
                        {Object.entries(comparisonResults.comparison_results)
                          .filter(([_, result]: [string, any]) => result.success)
                          .sort(([_, a]: [string, any], [__, b]: [string, any]) => a.processing_time - b.processing_time)[0]?.[0] 
                          ? availableModels[Object.entries(comparisonResults.comparison_results)
                              .filter(([_, result]: [string, any]) => result.success)
                              .sort(([_, a]: [string, any], [__, b]: [string, any]) => a.processing_time - b.processing_time)[0][0]]?.name
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="insight-item">
                      <span className="insight-label">Most Detailed:</span>
                      <span className="insight-value">
                        {Object.entries(comparisonResults.comparison_results)
                          .filter(([_, result]: [string, any]) => result.success)
                          .sort(([_, a]: [string, any], [__, b]: [string, any]) => b.answer.length - a.answer.length)[0]?.[0]
                          ? availableModels[Object.entries(comparisonResults.comparison_results)
                              .filter(([_, result]: [string, any]) => result.success)
                              .sort(([_, a]: [string, any], [__, b]: [string, any]) => b.answer.length - a.answer.length)[0][0]]?.name
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {/* Document Preview & Split View */}
            {file && (
              <div className="document-preview-section">
                <div className="preview-header">
                  <button 
                    className="toggle-button"
                    onClick={() => setShowExtractedText(!showExtractedText)}
                  >
                    📄 Document Analysis {showExtractedText ? '▼' : '▶'}
                  </button>
                </div>
                
                {showExtractedText && (
                  <div className="split-view">
                    <div className="original-document">
                      <h4>📄 Original Document</h4>
                      <div className="document-info">
                        <p><strong>File:</strong> {file.name}</p>
                        <p><strong>Size:</strong> {formatFileSize(file.size)}</p>
                        <p><strong>Type:</strong> {file.type || 'Unknown'}</p>
                      </div>
                      {file.type.startsWith('image/') && (
                        <img 
                          src={URL.createObjectURL(file)} 
                          alt="Document preview" 
                          className="document-image-preview"
                        />
                      )}
                    </div>
                    
                    <div className="extracted-content">
                      <h4>🔍 Extracted Text</h4>
                      <div className="extracted-text-content">
                        <pre>{extractedText}</pre>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
