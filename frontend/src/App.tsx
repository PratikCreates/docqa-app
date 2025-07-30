import React, { useState, useEffect } from "react";
import "./App.css";

interface ApiResponse {
  answer: string;
  extracted_text: string;
  file_type: string;
}

interface SupportedFormats {
  supported_formats: {
    images: string[];
    documents: string[];
  };
}

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

  useEffect(() => {
    // Fetch supported formats on component mount
    fetch("http://localhost:8000/supported-formats")
      .then(res => res.json())
      .then(data => setSupportedFormats(data))
      .catch(err => console.error("Failed to fetch supported formats:", err));
  }, []);

  const handleUpload = async () => {
    if (!file || !question.trim()) return;
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("question", question);
    if (systemPrompt.trim()) {
      formData.append("system_prompt", systemPrompt);
    }

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data: ApiResponse = await res.json();
      setAnswer(data.answer);
      setExtractedText(data.extracted_text);
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
      setFile(files[0]);
    }
  };

  const getAcceptedFileTypes = () => {
    if (!supportedFormats) return "*";
    const { images, documents } = supportedFormats.supported_formats;
    return [...images.map(ext => `.${ext}`), ...documents.map(ext => `.${ext}`)].join(",");
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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

  const getQuestionSuggestions = (filename: string) => {
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
      <div className="header">
        <h1>🤖 Smart Document Q&A</h1>
        <p>Upload images, PDFs, or documents and ask questions about them</p>
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
              onChange={(e) => setFile(e.target.files?.[0] || null)}
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
          
          {/* Question Suggestions */}
          {file && (
            <div className="question-suggestions">
              <p>💡 Suggested questions:</p>
              <div className="suggestion-buttons">
                {getQuestionSuggestions(file.name).map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-button"
                    onClick={() => setQuestion(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
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

        {/* Results Section */}
        {answer && (
          <div className="results-section">
            <div className="answer-card">
              <h3>💡 Answer</h3>
              <div className="answer-content">
                {answer.split('\n').map((line, index) => (
                  <p key={index}>{line}</p>
                ))}
              </div>
              
              {/* Export Options */}
              <div className="export-options">
                <button 
                  className="export-button"
                  onClick={() => exportResults('txt')}
                >
                  📄 Export as TXT
                </button>
                <button 
                  className="export-button"
                  onClick={() => exportResults('json')}
                >
                  📋 Export as JSON
                </button>
              </div>
            </div>

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
