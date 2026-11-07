"""
Python SDK for Advanced Document Intelligence Platform API
Provides easy-to-use Python client for all API endpoints
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime
import os
from pathlib import Path

class DocAIError(Exception):
    """Base exception for DocAI SDK"""
    pass

class AuthenticationError(DocAIError):
    """Authentication related errors"""
    pass

class RateLimitError(DocAIError):
    """Rate limit exceeded errors"""
    pass

class APIError(DocAIError):
    """General API errors"""
    pass

class DocAIClient:
    """
    Python client for Advanced Document Intelligence Platform API
    
    Example usage:
        client = DocAIClient(api_key="your-api-key")
        result = client.ask_document("path/to/document.pdf", "What is this document about?")
        print(result['answer'])
    """
    
    def __init__(self, api_key: Optional[str] = None, jwt_token: Optional[str] = None,
                 base_url: str = "https://api.docai.example.com/v2",
                 timeout: int = 30):
        """
        Initialize DocAI client
        
        Args:
            api_key: API key for authentication
            jwt_token: JWT token for authentication (alternative to api_key)
            base_url: Base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Set up authentication
        if api_key:
            self.headers = {"X-API-Key": api_key}
        elif jwt_token:
            self.headers = {"Authorization": f"Bearer {jwt_token}"}
        else:
            # Try to get from environment
            api_key = os.getenv("DOCAI_API_KEY")
            jwt_token = os.getenv("DOCAI_JWT_TOKEN")
            
            if api_key:
                self.headers = {"X-API-Key": api_key}
            elif jwt_token:
                self.headers = {"Authorization": f"Bearer {jwt_token}"}
            else:
                raise AuthenticationError("No API key or JWT token provided")
        
        self.headers["User-Agent"] = "DocAI-Python-SDK/2.0.0"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or JWT token")
            
            # Handle other client errors
            if 400 <= response.status_code < 500:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', response.text)
                raise APIError(f"Client error {response.status_code}: {error_message}")
            
            # Handle server errors
            if response.status_code >= 500:
                raise APIError(f"Server error {response.status_code}: {response.text}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise APIError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    # Document Processing Methods
    
    def ask_document(self, file_path: Union[str, Path, BinaryIO], question: str,
                    model: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question about a document
        
        Args:
            file_path: Path to document file or file-like object
            question: Question to ask about the document
            model: AI model to use (optional)
            system_prompt: Custom system prompt (optional)
            
        Returns:
            Dictionary containing answer and metadata
        """
        if isinstance(file_path, (str, Path)):
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'question': question}
                if model:
                    data['model'] = model
                if system_prompt:
                    data['system_prompt'] = system_prompt
                
                return self._make_request('POST', '/ask', files=files, data=data)
        else:
            files = {'file': file_path}
            data = {'question': question}
            if model:
                data['model'] = model
            if system_prompt:
                data['system_prompt'] = system_prompt
            
            return self._make_request('POST', '/ask', files=files, data=data)
    
    def upload_document(self, file_path: Union[str, Path, BinaryIO], 
                       title: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Upload a document for processing
        
        Args:
            file_path: Path to document file or file-like object
            title: Optional document title
            tags: Optional list of tags
            
        Returns:
            Dictionary containing upload result
        """
        if isinstance(file_path, (str, Path)):
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {}
                if title:
                    data['title'] = title
                if tags:
                    data['tags'] = ','.join(tags)
                
                return self._make_request('POST', '/documents/upload', files=files, data=data)
        else:
            files = {'file': file_path}
            data = {}
            if title:
                data['title'] = title
            if tags:
                data['tags'] = ','.join(tags)
            
            return self._make_request('POST', '/documents/upload', files=files, data=data)
    
    def list_documents(self, page: int = 1, limit: int = 20, tags: Optional[str] = None) -> Dict[str, Any]:
        """
        List user's documents
        
        Args:
            page: Page number
            limit: Items per page
            tags: Filter by tags
            
        Returns:
            Dictionary containing document list
        """
        params = {'page': page, 'limit': limit}
        if tags:
            params['tags'] = tags
        
        return self._make_request('GET', '/documents', params=params)
    
    # Search Methods
    
    def search_documents(self, query: str, document_type: Optional[str] = None,
                        date_from: Optional[str] = None, size: int = 20) -> Dict[str, Any]:
        """
        Search documents
        
        Args:
            query: Search query
            document_type: Filter by document type
            date_from: Filter by creation date (YYYY-MM-DD)
            size: Number of results
            
        Returns:
            Dictionary containing search results
        """
        params = {'q': query, 'size': size}
        if document_type:
            params['document_type'] = document_type
        if date_from:
            params['date_from'] = date_from
        
        return self._make_request('GET', '/search', params=params)
    
    def advanced_search(self, query: str, search_type: str = "standard",
                       sort_by: str = "relevance") -> Dict[str, Any]:
        """
        Perform advanced search
        
        Args:
            query: Search query
            search_type: Search strategy (standard, fuzzy, semantic, code)
            sort_by: Sort results by (relevance, date, title, size)
            
        Returns:
            Dictionary containing advanced search results
        """
        params = {
            'q': query,
            'search_type': search_type,
            'sort_by': sort_by
        }
        
        return self._make_request('GET', '/search/advanced', params=params)
    
    # Webhook Methods
    
    def register_webhook(self, url: str, events: List[str], secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a webhook endpoint
        
        Args:
            url: Webhook URL
            events: List of events to subscribe to
            secret: Optional webhook secret
            
        Returns:
            Dictionary containing webhook registration result
        """
        data = {
            'url': url,
            'events': events
        }
        if secret:
            data['secret'] = secret
        
        return self._make_request('POST', '/webhooks/register', json=data)
    
    def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks"""
        return self._make_request('GET', '/webhooks/')
    
    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook"""
        return self._make_request('DELETE', f'/webhooks/{webhook_id}')
    
    def test_webhook(self, webhook_id: str, test_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Test a webhook endpoint"""
        data = {}
        if test_data:
            data['test_data'] = test_data
        
        return self._make_request('POST', f'/webhooks/{webhook_id}/test', json=data)
    
    # Email Integration Methods
    
    def configure_email(self, smtp_server: str, smtp_port: int, imap_server: str,
                       imap_port: int, username: str, password: str,
                       use_tls: bool = True) -> Dict[str, Any]:
        """
        Configure email settings
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            imap_server: IMAP server hostname
            imap_port: IMAP server port
            username: Email username
            password: Email password
            use_tls: Use TLS encryption
            
        Returns:
            Dictionary containing configuration result
        """
        data = {
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'imap_server': imap_server,
            'imap_port': imap_port,
            'username': username,
            'password': password,
            'use_tls': use_tls
        }
        
        return self._make_request('POST', '/email/configure', json=data)
    
    def start_email_monitoring(self) -> Dict[str, Any]:
        """Start email monitoring for document uploads"""
        return self._make_request('POST', '/email/monitoring/start')
    
    def stop_email_monitoring(self) -> Dict[str, Any]:
        """Stop email monitoring"""
        return self._make_request('POST', '/email/monitoring/stop')
    
    def share_document_via_email(self, recipient_email: str, document_id: str,
                                document_name: str, share_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Share a document via email
        
        Args:
            recipient_email: Recipient's email address
            document_id: Document ID to share
            document_name: Document name
            share_message: Optional message to include
            
        Returns:
            Dictionary containing share result
        """
        data = {
            'recipient_email': recipient_email,
            'document_id': document_id,
            'document_name': document_name
        }
        if share_message:
            data['share_message'] = share_message
        
        return self._make_request('POST', '/email/share', json=data)
    
    # Cloud Storage Methods
    
    def connect_cloud_storage(self, provider: str, access_token: str,
                             refresh_token: Optional[str] = None,
                             client_id: Optional[str] = None,
                             client_secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to cloud storage provider
        
        Args:
            provider: Provider name (google_drive, dropbox)
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            client_id: OAuth client ID (optional)
            client_secret: OAuth client secret (optional)
            
        Returns:
            Dictionary containing connection result
        """
        data = {
            'provider': provider,
            'access_token': access_token
        }
        if refresh_token:
            data['refresh_token'] = refresh_token
        if client_id:
            data['client_id'] = client_id
        if client_secret:
            data['client_secret'] = client_secret
        
        return self._make_request('POST', '/cloud-storage/connect', json=data)
    
    def configure_cloud_sync(self, provider: str, folder_path: str,
                            sync_interval: int = 60, auto_process: bool = True,
                            file_filters: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Configure automatic cloud storage sync
        
        Args:
            provider: Provider name
            folder_path: Folder path to sync
            sync_interval: Sync interval in minutes
            auto_process: Automatically process synced files
            file_filters: List of file extensions to sync
            
        Returns:
            Dictionary containing configuration result
        """
        data = {
            'provider': provider,
            'folder_path': folder_path,
            'sync_interval': sync_interval,
            'auto_process': auto_process
        }
        if file_filters:
            data['file_filters'] = file_filters
        
        return self._make_request('POST', '/cloud-storage/configure-sync', json=data)
    
    def manual_cloud_sync(self, provider: str, folder_path: Optional[str] = None) -> Dict[str, Any]:
        """Manually trigger cloud storage sync"""
        data = {'provider': provider}
        if folder_path:
            data['folder_path'] = folder_path
        
        return self._make_request('POST', '/cloud-storage/sync', json=data)
    
    def list_cloud_files(self, provider: str, folder_path: Optional[str] = None) -> Dict[str, Any]:
        """List files from cloud storage"""
        params = {'provider': provider}
        if folder_path:
            params['folder_path'] = folder_path
        
        return self._make_request('GET', '/cloud-storage/files', params=params)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get cloud storage sync status"""
        return self._make_request('GET', '/cloud-storage/sync-status')
    
    # Utility Methods
    
    def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        return self._make_request('GET', '/health')
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information"""
        return self._make_request('GET', '/info')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get API metrics"""
        return self._make_request('GET', '/metrics')
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limit information"""
        return self._make_request('GET', '/rate-limits')
    
    # Context manager support
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

# Convenience functions
def create_client(api_key: Optional[str] = None, jwt_token: Optional[str] = None,
                 base_url: str = "https://api.docai.example.com/v2") -> DocAIClient:
    """Create a DocAI client instance"""
    return DocAIClient(api_key=api_key, jwt_token=jwt_token, base_url=base_url)

def ask_document(file_path: Union[str, Path], question: str, 
                api_key: Optional[str] = None) -> Dict[str, Any]:
    """Quick function to ask a question about a document"""
    with create_client(api_key=api_key) as client:
        return client.ask_document(file_path, question)

# Example usage
if __name__ == "__main__":
    # Example usage of the SDK
    
    # Initialize client
    client = DocAIClient(api_key="your-api-key-here")
    
    try:
        # Check API health
        health = client.get_health()
        print(f"API Status: {health['status']}")
        
        # Ask a question about a document
        result = client.ask_document("example.pdf", "What is the main topic of this document?")
        print(f"Answer: {result['answer']}")
        
        # Search documents
        search_results = client.search_documents("machine learning")
        print(f"Found {len(search_results['results'])} documents")
        
        # Register a webhook
        webhook = client.register_webhook(
            url="https://your-app.com/webhook",
            events=["document.uploaded", "document.processed"]
        )
        print(f"Webhook registered: {webhook['webhook_id']}")
        
    except DocAIError as e:
        print(f"Error: {e}")
    finally:
        client.session.close()