/**
 * JavaScript/Node.js SDK for Advanced Document Intelligence Platform API
 * Official JavaScript client library for easy integration
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

/**
 * Search types enum
 */
const SearchType = {
    STANDARD: 'standard',
    FUZZY: 'fuzzy',
    SEMANTIC: 'semantic',
    CODE: 'code'
};

/**
 * Comparison types enum
 */
const ComparisonType = {
    COMPREHENSIVE: 'comprehensive',
    CONTENT: 'content',
    STRUCTURE: 'structure',
    SEMANTIC: 'semantic'
};

/**
 * Clustering methods enum
 */
const ClusteringMethod = {
    TOPIC: 'topic',
    TEMPORAL: 'temporal',
    AUTHOR: 'author',
    SIMILARITY: 'similarity'
};

/**
 * API Response wrapper class
 */
class APIResponse {
    constructor(success, data, statusCode, headers, error = null) {
        this.success = success;
        this.data = data;
        this.statusCode = statusCode;
        this.headers = headers;
        this.error = error;
    }
}

/**
 * Official JavaScript client for the Advanced Document Intelligence Platform API
 * 
 * @example
 * const client = new DocumentAIClient('your_api_key');
 * 
 * // Upload and analyze document
 * const result = await client.uploadDocument('./document.pdf', 'My Document');
 * 
 * // Ask questions about documents
 * const answer = await client.askQuestion('./document.txt', 'What is this document about?');
 * 
 * // Search documents
 * const results = await client.search('python programming', { documentType: 'code' });
 */
class DocumentAIClient {
    /**
     * Initialize the DocumentAI client
     * 
     * @param {string} apiKey - Your API key (can also be set via DOCAI_API_KEY env var)
     * @param {string} baseUrl - API base URL (default: http://localhost:8000)
     */
    constructor(apiKey = null, baseUrl = 'http://localhost:8000') {
        this.apiKey = apiKey || process.env.DOCAI_API_KEY;
        if (!this.apiKey) {
            throw new Error('API key is required. Set DOCAI_API_KEY environment variable or pass apiKey parameter.');
        }
        
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'X-API-Key': this.apiKey,
                'User-Agent': 'DocumentAI-JavaScript-SDK/1.0.0'
            }
        });
    }

    /**
     * Make HTTP request to API
     * @private
     */
    async _makeRequest(method, endpoint, options = {}) {
        try {
            const response = await this.client.request({
                method,
                url: endpoint,
                ...options
            });

            return new APIResponse(
                true,
                response.data,
                response.status,
                response.headers
            );
        } catch (error) {
            const statusCode = error.response?.status || 0;
            const data = error.response?.data || { message: error.message };
            const headers = error.response?.headers || {};
            
            return new APIResponse(
                false,
                data,
                statusCode,
                headers,
                data.error?.message || error.message
            );
        }
    }

    /**
     * Check API health status
     */
    async healthCheck() {
        return this._makeRequest('GET', '/health');
    }

    /**
     * Get list of available AI models
     */
    async listModels() {
        return this._makeRequest('GET', '/models');
    }

    /**
     * Upload a document for processing
     * 
     * @param {string|Buffer|Stream} file - File path, Buffer, or Stream
     * @param {string} title - Optional document title
     * @param {string[]} tags - Optional list of tags
     */
    async uploadDocument(file, title = null, tags = null) {
        const formData = new FormData();
        
        // Handle different file input types
        if (typeof file === 'string') {
            // File path
            formData.append('file', fs.createReadStream(file));
        } else if (Buffer.isBuffer(file)) {
            // Buffer
            formData.append('file', file, 'document');
        } else {
            // Stream or other
            formData.append('file', file);
        }
        
        // Add optional parameters
        if (title) {
            formData.append('title', title);
        }
        if (tags && Array.isArray(tags)) {
            formData.append('tags', tags.join(','));
        }

        return this._makeRequest('POST', '/documents/upload', {
            data: formData,
            headers: formData.getHeaders()
        });
    }

    /**
     * List user's documents
     * 
     * @param {number} page - Page number (default: 1)
     * @param {number} limit - Items per page (default: 20, max: 100)
     * @param {string[]} tags - Filter by tags
     */
    async listDocuments(page = 1, limit = 20, tags = null) {
        const params = { page, limit };
        if (tags && Array.isArray(tags)) {
            params.tags = tags.join(',');
        }

        return this._makeRequest('GET', '/documents', { params });
    }

    /**
     * Ask a question about a document
     * 
     * @param {string|Buffer|Stream} file - File path, Buffer, or Stream
     * @param {string} question - Question to ask about the document
     * @param {string} model - AI model to use (optional)
     */
    async askQuestion(file, question, model = null) {
        const formData = new FormData();
        
        // Handle different file input types
        if (typeof file === 'string') {
            formData.append('file', fs.createReadStream(file));
        } else if (Buffer.isBuffer(file)) {
            formData.append('file', file, 'document');
        } else {
            formData.append('file', file);
        }
        
        formData.append('question', question);
        if (model) {
            formData.append('model', model);
        }

        return this._makeRequest('POST', '/ask', {
            data: formData,
            headers: formData.getHeaders()
        });
    }

    /**
     * Generate questions from document content
     * 
     * @param {string|Buffer|Stream} file - File path, Buffer, or Stream
     * @param {number} maxQuestions - Maximum number of questions to generate
     * @param {string} documentCategory - Document category (general, code, research, documentation)
     */
    async generateQuestions(file, maxQuestions = 10, documentCategory = 'general') {
        const formData = new FormData();
        
        // Handle different file input types
        if (typeof file === 'string') {
            formData.append('file', fs.createReadStream(file));
        } else if (Buffer.isBuffer(file)) {
            formData.append('file', file, 'document');
        } else {
            formData.append('file', file);
        }
        
        formData.append('max_questions', maxQuestions.toString());
        formData.append('document_category', documentCategory);

        return this._makeRequest('POST', '/generate-questions', {
            data: formData,
            headers: formData.getHeaders()
        });
    }

    /**
     * Search documents
     * 
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @param {string} options.documentType - Filter by document type
     * @param {string} options.dateFrom - Filter by creation date (from)
     * @param {string} options.dateTo - Filter by creation date (to)
     * @param {string} options.fileFormat - Filter by file format
     * @param {string[]} options.tags - Filter by tags
     * @param {number} options.size - Number of results (max: 100)
     */
    async search(query, options = {}) {
        const params = { q: query, size: options.size || 20 };
        
        if (options.documentType) params.document_type = options.documentType;
        if (options.dateFrom) params.date_from = options.dateFrom;
        if (options.dateTo) params.date_to = options.dateTo;
        if (options.fileFormat) params.file_format = options.fileFormat;
        if (options.tags && Array.isArray(options.tags)) {
            params.tags = options.tags.join(',');
        }

        return this._makeRequest('GET', '/search', { params });
    }

    /**
     * Perform advanced search with multiple strategies
     * 
     * @param {string} query - Search query
     * @param {Object} options - Advanced search options
     * @param {string} options.searchType - Search strategy (standard, fuzzy, semantic, code)
     * @param {string} options.sortBy - Sort results by (relevance, date, title, size)
     * @param {boolean} options.highlight - Enable result highlighting
     */
    async advancedSearch(query, options = {}) {
        const params = {
            q: query,
            search_type: options.searchType || SearchType.STANDARD,
            sort_by: options.sortBy || 'relevance',
            highlight: options.highlight !== false
        };
        
        // Add any additional filters
        Object.keys(options).forEach(key => {
            if (!['searchType', 'sortBy', 'highlight'].includes(key)) {
                params[key] = options[key];
            }
        });

        return this._makeRequest('GET', '/search/advanced', { params });
    }

    /**
     * Compare two documents
     * 
     * @param {string} document1Id - First document ID
     * @param {string} document2Id - Second document ID
     * @param {string} comparisonType - Type of comparison to perform
     */
    async compareDocuments(document1Id, document2Id, comparisonType = ComparisonType.COMPREHENSIVE) {
        const data = new URLSearchParams({
            document1_id: document1Id,
            document2_id: document2Id,
            comparison_type: comparisonType
        });

        return this._makeRequest('POST', '/documents/compare', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Compare multiple documents simultaneously
     * 
     * @param {string[]} documentIds - List of document IDs to compare
     * @param {string} comparisonMode - Comparison mode (all_pairs, clustering, outlier_detection)
     */
    async batchCompareDocuments(documentIds, comparisonMode = 'all_pairs') {
        const data = new URLSearchParams({
            document_ids: documentIds.join(','),
            comparison_mode: comparisonMode
        });

        return this._makeRequest('POST', '/documents/batch-compare', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Find documents similar to the specified document
     * 
     * @param {string} documentId - Target document ID
     * @param {number} limit - Maximum number of similar documents to return
     * @param {number} minSimilarity - Minimum similarity threshold
     */
    async findSimilarDocuments(documentId, limit = 10, minSimilarity = 0.3) {
        const params = { limit, min_similarity: minSimilarity };
        return this._makeRequest('GET', `/documents/${documentId}/find-similar`, { params });
    }

    /**
     * Analyze relationships between documents
     * 
     * @param {string[]} documentIds - List of document IDs to analyze
     * @param {string} relationshipTypes - Types of relationships to analyze
     */
    async analyzeRelationships(documentIds, relationshipTypes = 'all') {
        const data = new URLSearchParams({
            document_ids: documentIds.join(','),
            relationship_types: relationshipTypes
        });

        return this._makeRequest('POST', '/documents/analyze-relationships', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Create clusters of related documents
     * 
     * @param {string[]} documentIds - List of document IDs to cluster
     * @param {string} clusteringMethod - Clustering method to use
     * @param {number} maxClusters - Maximum number of clusters to create
     */
    async createClusters(documentIds, clusteringMethod = ClusteringMethod.TOPIC, maxClusters = 10) {
        const data = new URLSearchParams({
            document_ids: documentIds.join(','),
            clustering_method: clusteringMethod,
            max_clusters: maxClusters.toString()
        });

        return this._makeRequest('POST', '/documents/create-clusters', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Perform trend analysis across document collections
     * 
     * @param {string[]} documentIds - List of document IDs to analyze
     * @param {number} timeWindow - Time window in days
     * @param {number} minDocumentCount - Minimum documents required for a trend
     */
    async performTrendAnalysis(documentIds, timeWindow = 30, minDocumentCount = 3) {
        const data = new URLSearchParams({
            document_ids: documentIds.join(','),
            time_window: timeWindow.toString(),
            min_document_count: minDocumentCount.toString()
        });

        return this._makeRequest('POST', '/documents/trend-analysis', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Perform cross-document search with correlation analysis
     * 
     * @param {string} query - Search query
     * @param {string[]} documentIds - List of document IDs to search within
     * @param {string} searchType - Type of search (comprehensive, entity, topic, temporal)
     */
    async crossDocumentSearch(query, documentIds, searchType = 'comprehensive') {
        const data = new URLSearchParams({
            query,
            document_ids: documentIds.join(','),
            search_type: searchType
        });

        return this._makeRequest('POST', '/documents/cross-search', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Create a network map of document relationships
     * 
     * @param {string[]} documentIds - List of document IDs to map
     * @param {number} minRelationshipStrength - Minimum relationship strength threshold
     */
    async createNetworkMap(documentIds, minRelationshipStrength = 0.3) {
        const data = new URLSearchParams({
            document_ids: documentIds.join(','),
            min_relationship_strength: minRelationshipStrength.toString()
        });

        return this._makeRequest('POST', '/documents/network-map', {
            data,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    }

    /**
     * Calculate influence score for a document
     * 
     * @param {string} documentId - Target document ID
     * @param {string[]} contextDocumentIds - List of context document IDs
     */
    async getDocumentInfluenceScore(documentId, contextDocumentIds = null) {
        const params = {};
        if (contextDocumentIds && Array.isArray(contextDocumentIds)) {
            params.context_document_ids = contextDocumentIds.join(',');
        }

        return this._makeRequest('GET', `/documents/${documentId}/influence-score`, { params });
    }
}

// Convenience functions for quick usage

/**
 * Quick search function for simple use cases
 * @param {string} query - Search query
 * @param {string} apiKey - API key
 */
async function quickSearch(query, apiKey = null) {
    const client = new DocumentAIClient(apiKey);
    const response = await client.search(query);
    return response.success ? response.data : { error: response.error };
}

/**
 * Quick question asking function
 * @param {string} filePath - File path
 * @param {string} question - Question to ask
 * @param {string} apiKey - API key
 */
async function quickAsk(filePath, question, apiKey = null) {
    const client = new DocumentAIClient(apiKey);
    const response = await client.askQuestion(filePath, question);
    return response.success ? response.data : { error: response.error };
}

/**
 * Quick document comparison function
 * @param {string} doc1Id - First document ID
 * @param {string} doc2Id - Second document ID
 * @param {string} apiKey - API key
 */
async function quickCompare(doc1Id, doc2Id, apiKey = null) {
    const client = new DocumentAIClient(apiKey);
    const response = await client.compareDocuments(doc1Id, doc2Id);
    return response.success ? response.data : { error: response.error };
}

// Export classes and functions
module.exports = {
    DocumentAIClient,
    APIResponse,
    SearchType,
    ComparisonType,
    ClusteringMethod,
    quickSearch,
    quickAsk,
    quickCompare
};

// Example usage
if (require.main === module) {
    (async () => {
        try {
            // Example usage of the SDK
            const client = new DocumentAIClient('your_api_key_here');
            
            // Check API health
            const health = await client.healthCheck();
            console.log('API Health:', health.data);
            
            // List available models
            const models = await client.listModels();
            console.log('Available models:', models.data);
            
            // Search documents
            const searchResults = await client.search('python programming');
            console.log('Search results:', searchResults.data);
            
        } catch (error) {
            console.error('Error:', error.message);
        }
    })();
}