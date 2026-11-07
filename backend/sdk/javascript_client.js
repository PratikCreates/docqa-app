/**
 * JavaScript SDK for Advanced Document Intelligence Platform API
 * Provides easy-to-use JavaScript client for all API endpoints
 * 
 * @version 2.0.0
 * @author DocAI Team
 */

class DocAIError extends Error {
    constructor(message, statusCode = null, errorCode = null) {
        super(message);
        this.name = 'DocAIError';
        this.statusCode = statusCode;
        this.errorCode = errorCode;
    }
}

class AuthenticationError extends DocAIError {
    constructor(message) {
        super(message, 401, 'AUTHENTICATION_ERROR');
        this.name = 'AuthenticationError';
    }
}

class RateLimitError extends DocAIError {
    constructor(message, retryAfter = null) {
        super(message, 429, 'RATE_LIMIT_ERROR');
        this.name = 'RateLimitError';
        this.retryAfter = retryAfter;
    }
}

class APIError extends DocAIError {
    constructor(message, statusCode, errorCode) {
        super(message, statusCode, errorCode);
        this.name = 'APIError';
    }
}

/**
 * JavaScript client for Advanced Document Intelligence Platform API
 * 
 * @example
 * const client = new DocAIClient({ apiKey: 'your-api-key' });
 * const result = await client.askDocument(file, 'What is this document about?');
 * console.log(result.answer);
 */
class DocAIClient {
    /**
     * Initialize DocAI client
     * 
     * @param {Object} options - Configuration options
     * @param {string} [options.apiKey] - API key for authentication
     * @param {string} [options.jwtToken] - JWT token for authentication
     * @param {string} [options.baseUrl='https://api.docai.example.com/v2'] - Base URL for the API
     * @param {number} [options.timeout=30000] - Request timeout in milliseconds
     */
    constructor(options = {}) {
        this.baseUrl = (options.baseUrl || 'https://api.docai.example.com/v2').replace(/\/$/, '');
        this.timeout = options.timeout || 30000;
        
        // Set up authentication
        this.headers = {
            'User-Agent': 'DocAI-JavaScript-SDK/2.0.0'
        };
        
        if (options.apiKey) {
            this.headers['X-API-Key'] = options.apiKey;
        } else if (options.jwtToken) {
            this.headers['Authorization'] = `Bearer ${options.jwtToken}`;
        } else {
            // Try to get from environment (Node.js)
            if (typeof process !== 'undefined' && process.env) {
                if (process.env.DOCAI_API_KEY) {
                    this.headers['X-API-Key'] = process.env.DOCAI_API_KEY;
                } else if (process.env.DOCAI_JWT_TOKEN) {
                    this.headers['Authorization'] = `Bearer ${process.env.DOCAI_JWT_TOKEN}`;
                } else {
                    throw new AuthenticationError('No API key or JWT token provided');
                }
            } else {
                throw new AuthenticationError('No API key or JWT token provided');
            }
        }
    }
    
    /**
     * Make HTTP request to API
     * @private
     */
    async _makeRequest(method, endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const requestOptions = {
            method,
            headers: { ...this.headers, ...options.headers },
            ...options
        };
        
        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        requestOptions.signal = controller.signal;
        
        try {
            const response = await fetch(url, requestOptions);
            clearTimeout(timeoutId);
            
            // Handle rate limiting
            if (response.status === 429) {
                const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
                throw new RateLimitError(`Rate limit exceeded. Retry after ${retryAfter} seconds`, retryAfter);
            }
            
            // Handle authentication errors
            if (response.status === 401) {
                throw new AuthenticationError('Invalid API key or JWT token');
            }
            
            // Handle other client errors
            if (response.status >= 400 && response.status < 500) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error?.message || response.statusText;
                throw new APIError(`Client error ${response.status}: ${errorMessage}`, response.status, errorData.error?.code);
            }
            
            // Handle server errors
            if (response.status >= 500) {
                throw new APIError(`Server error ${response.status}: ${response.statusText}`, response.status, 'SERVER_ERROR');
            }
            
            return await response.json();
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new APIError(`Request timeout after ${this.timeout}ms`, null, 'TIMEOUT_ERROR');
            }
            
            if (error instanceof DocAIError) {
                throw error;
            }
            
            throw new APIError(`Request failed: ${error.message}`, null, 'NETWORK_ERROR');
        }
    }
    
    // Document Processing Methods
    
    /**
     * Ask a question about a document
     * 
     * @param {File|Blob} file - Document file
     * @param {string} question - Question to ask about the document
     * @param {Object} [options] - Additional options
     * @param {string} [options.model] - AI model to use
     * @param {string} [options.systemPrompt] - Custom system prompt
     * @returns {Promise<Object>} Answer and metadata
     */
    async askDocument(file, question, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('question', question);
        
        if (options.model) {
            formData.append('model', options.model);
        }
        if (options.systemPrompt) {
            formData.append('system_prompt', options.systemPrompt);
        }
        
        return this._makeRequest('POST', '/ask', { body: formData });
    }
    
    /**
     * Upload a document for processing
     * 
     * @param {File|Blob} file - Document file
     * @param {Object} [options] - Additional options
     * @param {string} [options.title] - Document title
     * @param {string[]} [options.tags] - Document tags
     * @returns {Promise<Object>} Upload result
     */
    async uploadDocument(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (options.title) {
            formData.append('title', options.title);
        }
        if (options.tags) {
            formData.append('tags', options.tags.join(','));
        }
        
        return this._makeRequest('POST', '/documents/upload', { body: formData });
    }
    
    /**
     * List user's documents
     * 
     * @param {Object} [options] - Query options
     * @param {number} [options.page=1] - Page number
     * @param {number} [options.limit=20] - Items per page
     * @param {string} [options.tags] - Filter by tags
     * @returns {Promise<Object>} Document list
     */
    async listDocuments(options = {}) {
        const params = new URLSearchParams({
            page: options.page || 1,
            limit: options.limit || 20
        });
        
        if (options.tags) {
            params.append('tags', options.tags);
        }
        
        return this._makeRequest('GET', `/documents?${params}`);
    }
    
    // Search Methods
    
    /**
     * Search documents
     * 
     * @param {string} query - Search query
     * @param {Object} [options] - Search options
     * @param {string} [options.documentType] - Filter by document type
     * @param {string} [options.dateFrom] - Filter by creation date (YYYY-MM-DD)
     * @param {number} [options.size=20] - Number of results
     * @returns {Promise<Object>} Search results
     */
    async searchDocuments(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            size: options.size || 20
        });
        
        if (options.documentType) {
            params.append('document_type', options.documentType);
        }
        if (options.dateFrom) {
            params.append('date_from', options.dateFrom);
        }
        
        return this._makeRequest('GET', `/search?${params}`);
    }
    
    /**
     * Perform advanced search
     * 
     * @param {string} query - Search query
     * @param {Object} [options] - Advanced search options
     * @param {string} [options.searchType='standard'] - Search strategy
     * @param {string} [options.sortBy='relevance'] - Sort results by
     * @returns {Promise<Object>} Advanced search results
     */
    async advancedSearch(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            search_type: options.searchType || 'standard',
            sort_by: options.sortBy || 'relevance'
        });
        
        return this._makeRequest('GET', `/search/advanced?${params}`);
    }
    
    // Webhook Methods
    
    /**
     * Register a webhook endpoint
     * 
     * @param {string} url - Webhook URL
     * @param {string[]} events - List of events to subscribe to
     * @param {string} [secret] - Optional webhook secret
     * @returns {Promise<Object>} Webhook registration result
     */
    async registerWebhook(url, events, secret = null) {
        const data = { url, events };
        if (secret) {
            data.secret = secret;
        }
        
        return this._makeRequest('POST', '/webhooks/register', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    /**
     * List all webhooks
     * @returns {Promise<Object>} Webhook list
     */
    async listWebhooks() {
        return this._makeRequest('GET', '/webhooks/');
    }
    
    /**
     * Delete a webhook
     * @param {string} webhookId - Webhook ID
     * @returns {Promise<Object>} Deletion result
     */
    async deleteWebhook(webhookId) {
        return this._makeRequest('DELETE', `/webhooks/${webhookId}`);
    }
    
    /**
     * Test a webhook endpoint
     * @param {string} webhookId - Webhook ID
     * @param {Object} [testData] - Optional test data
     * @returns {Promise<Object>} Test result
     */
    async testWebhook(webhookId, testData = null) {
        const data = {};
        if (testData) {
            data.test_data = testData;
        }
        
        return this._makeRequest('POST', `/webhooks/${webhookId}/test`, {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    // Email Integration Methods
    
    /**
     * Configure email settings
     * 
     * @param {Object} config - Email configuration
     * @param {string} config.smtpServer - SMTP server hostname
     * @param {number} config.smtpPort - SMTP server port
     * @param {string} config.imapServer - IMAP server hostname
     * @param {number} config.imapPort - IMAP server port
     * @param {string} config.username - Email username
     * @param {string} config.password - Email password
     * @param {boolean} [config.useTls=true] - Use TLS encryption
     * @returns {Promise<Object>} Configuration result
     */
    async configureEmail(config) {
        const data = {
            smtp_server: config.smtpServer,
            smtp_port: config.smtpPort,
            imap_server: config.imapServer,
            imap_port: config.imapPort,
            username: config.username,
            password: config.password,
            use_tls: config.useTls !== false
        };
        
        return this._makeRequest('POST', '/email/configure', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Start email monitoring for document uploads
     * @returns {Promise<Object>} Monitoring start result
     */
    async startEmailMonitoring() {
        return this._makeRequest('POST', '/email/monitoring/start');
    }
    
    /**
     * Stop email monitoring
     * @returns {Promise<Object>} Monitoring stop result
     */
    async stopEmailMonitoring() {
        return this._makeRequest('POST', '/email/monitoring/stop');
    }
    
    /**
     * Share a document via email
     * 
     * @param {string} recipientEmail - Recipient's email address
     * @param {string} documentId - Document ID to share
     * @param {string} documentName - Document name
     * @param {string} [shareMessage] - Optional message to include
     * @returns {Promise<Object>} Share result
     */
    async shareDocumentViaEmail(recipientEmail, documentId, documentName, shareMessage = null) {
        const data = {
            recipient_email: recipientEmail,
            document_id: documentId,
            document_name: documentName
        };
        if (shareMessage) {
            data.share_message = shareMessage;
        }
        
        return this._makeRequest('POST', '/email/share', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    // Cloud Storage Methods
    
    /**
     * Connect to cloud storage provider
     * 
     * @param {string} provider - Provider name (google_drive, dropbox)
     * @param {string} accessToken - OAuth access token
     * @param {Object} [options] - Additional options
     * @param {string} [options.refreshToken] - OAuth refresh token
     * @param {string} [options.clientId] - OAuth client ID
     * @param {string} [options.clientSecret] - OAuth client secret
     * @returns {Promise<Object>} Connection result
     */
    async connectCloudStorage(provider, accessToken, options = {}) {
        const data = {
            provider,
            access_token: accessToken
        };
        
        if (options.refreshToken) {
            data.refresh_token = options.refreshToken;
        }
        if (options.clientId) {
            data.client_id = options.clientId;
        }
        if (options.clientSecret) {
            data.client_secret = options.clientSecret;
        }
        
        return this._makeRequest('POST', '/cloud-storage/connect', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Configure automatic cloud storage sync
     * 
     * @param {string} provider - Provider name
     * @param {string} folderPath - Folder path to sync
     * @param {Object} [options] - Sync options
     * @param {number} [options.syncInterval=60] - Sync interval in minutes
     * @param {boolean} [options.autoProcess=true] - Automatically process synced files
     * @param {string[]} [options.fileFilters] - List of file extensions to sync
     * @returns {Promise<Object>} Configuration result
     */
    async configureCloudSync(provider, folderPath, options = {}) {
        const data = {
            provider,
            folder_path: folderPath,
            sync_interval: options.syncInterval || 60,
            auto_process: options.autoProcess !== false
        };
        
        if (options.fileFilters) {
            data.file_filters = options.fileFilters;
        }
        
        return this._makeRequest('POST', '/cloud-storage/configure-sync', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    /**
     * Manually trigger cloud storage sync
     * @param {string} provider - Provider name
     * @param {string} [folderPath] - Optional folder path
     * @returns {Promise<Object>} Sync result
     */
    async manualCloudSync(provider, folderPath = null) {
        const data = { provider };
        if (folderPath) {
            data.folder_path = folderPath;
        }
        
        return this._makeRequest('POST', '/cloud-storage/sync', {
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }
    
    /**
     * List files from cloud storage
     * @param {string} provider - Provider name
     * @param {string} [folderPath] - Optional folder path
     * @returns {Promise<Object>} File list
     */
    async listCloudFiles(provider, folderPath = null) {
        const params = new URLSearchParams({ provider });
        if (folderPath) {
            params.append('folder_path', folderPath);
        }
        
        return this._makeRequest('GET', `/cloud-storage/files?${params}`);
    }
    
    /**
     * Get cloud storage sync status
     * @returns {Promise<Object>} Sync status
     */
    async getSyncStatus() {
        return this._makeRequest('GET', '/cloud-storage/sync-status');
    }
    
    // Utility Methods
    
    /**
     * Get API health status
     * @returns {Promise<Object>} Health status
     */
    async getHealth() {
        return this._makeRequest('GET', '/health');
    }
    
    /**
     * Get API information
     * @returns {Promise<Object>} API information
     */
    async getApiInfo() {
        return this._makeRequest('GET', '/info');
    }
    
    /**
     * Get API metrics
     * @returns {Promise<Object>} API metrics
     */
    async getMetrics() {
        return this._makeRequest('GET', '/metrics');
    }
    
    /**
     * Get rate limit information
     * @returns {Promise<Object>} Rate limit information
     */
    async getRateLimits() {
        return this._makeRequest('GET', '/rate-limits');
    }
}

// Convenience functions
function createClient(options = {}) {
    return new DocAIClient(options);
}

async function askDocument(file, question, apiKey = null) {
    const client = new DocAIClient({ apiKey });
    return client.askDocument(file, question);
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = {
        DocAIClient,
        DocAIError,
        AuthenticationError,
        RateLimitError,
        APIError,
        createClient,
        askDocument
    };
} else if (typeof window !== 'undefined') {
    // Browser
    window.DocAI = {
        DocAIClient,
        DocAIError,
        AuthenticationError,
        RateLimitError,
        APIError,
        createClient,
        askDocument
    };
}

// Example usage
/*
// Browser usage
const client = new DocAIClient({ apiKey: 'your-api-key' });

// File input handling
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        try {
            const result = await client.askDocument(file, 'What is this document about?');
            console.log('Answer:', result.answer);
        } catch (error) {
            console.error('Error:', error.message);
        }
    }
});

// Node.js usage
const { DocAIClient } = require('./docai-client');

async function example() {
    const client = new DocAIClient({ apiKey: process.env.DOCAI_API_KEY });
    
    try {
        // Check API health
        const health = await client.getHealth();
        console.log('API Status:', health.status);
        
        // Search documents
        const searchResults = await client.searchDocuments('machine learning');
        console.log(`Found ${searchResults.results.length} documents`);
        
        // Register webhook
        const webhook = await client.registerWebhook(
            'https://your-app.com/webhook',
            ['document.uploaded', 'document.processed']
        );
        console.log('Webhook registered:', webhook.webhook_id);
        
    } catch (error) {
        if (error instanceof RateLimitError) {
            console.log(`Rate limited. Retry after ${error.retryAfter} seconds`);
        } else {
            console.error('Error:', error.message);
        }
    }
}
*/