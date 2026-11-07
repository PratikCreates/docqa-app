# Advanced Document Intelligence Platform API v2.0

A comprehensive REST API for document processing, analysis, and intelligent automation with multi-model AI support.

## 🚀 Quick Start

### Authentication

Get your API key from the dashboard and include it in your requests:

```bash
curl -H "X-API-Key: your-api-key" https://api.docai.example.com/v2/health
```

Or use JWT tokens:

```bash
curl -H "Authorization: Bearer your-jwt-token" https://api.docai.example.com/v2/health
```

### Basic Document Processing

```bash
# Ask a question about a document
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "question=What is the main topic?" \
  https://api.docai.example.com/v2/ask
```

## 📚 API Documentation

- **Interactive Docs**: [https://api.docai.example.com/v2/docs](https://api.docai.example.com/v2/docs)
- **ReDoc**: [https://api.docai.example.com/v2/redoc](https://api.docai.example.com/v2/redoc)
- **OpenAPI Spec**: [https://api.docai.example.com/v2/openapi.json](https://api.docai.example.com/v2/openapi.json)

## 🔐 Authentication

### API Keys

1. Register at [https://docai.example.com/register](https://docai.example.com/register)
2. Generate an API key in your dashboard
3. Include in requests: `X-API-Key: your-api-key`

### JWT Tokens

1. Login via `/auth/login` endpoint
2. Use returned JWT token: `Authorization: Bearer token`
3. Tokens expire after 24 hours

## 📊 Rate Limits

| Tier | Requests/Hour | Requests/Minute | Burst Limit |
|------|---------------|-----------------|-------------|
| Free | 100 | 10 | 20 |
| Pro | 1,000 | 50 | 100 |
| Enterprise | 10,000 | 500 | 1,000 |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

## 🔔 Webhooks

### Register Webhook

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["document.uploaded", "document.processed"],
    "secret": "your-webhook-secret"
  }' \
  https://api.docai.example.com/v2/webhooks/register
```

### Available Events

- `document.uploaded` - Document successfully uploaded
- `document.processed` - Document processing completed
- `document.failed` - Document processing failed
- `question.generated` - Questions auto-generated
- `search.completed` - Search operation completed
- `comparison.completed` - Document comparison completed
- `analysis.completed` - Cross-document analysis completed

### Webhook Security

Verify webhook signatures using HMAC-SHA256:

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        json.dumps(payload, sort_keys=True).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## 📧 Email Integration

### Configure Email

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "use_tls": true
  }' \
  https://api.docai.example.com/v2/email/configure
```

### Start Email Monitoring

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  https://api.docai.example.com/v2/email/monitoring/start
```

### Email Processing Instructions

Include these tags in your email body for automatic processing:

- `#tags: research, important` - Add tags to documents
- `#process: summarize` - Custom processing instructions
- `#questions: 5` - Generate specific number of questions
- `#model: qwen3-coder` - Use specific AI model
- `#share: colleague@company.com` - Share processed document

## ☁️ Cloud Storage Integration

### Connect Google Drive

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google_drive",
    "access_token": "your-oauth-token",
    "refresh_token": "your-refresh-token",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret"
  }' \
  https://api.docai.example.com/v2/cloud-storage/connect
```

### Configure Auto-Sync

```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google_drive",
    "folder_path": "/Documents/Research",
    "sync_interval": 60,
    "auto_process": true,
    "file_filters": [".pdf", ".docx", ".txt"],
    "tags": ["cloud-sync", "research"]
  }' \
  https://api.docai.example.com/v2/cloud-storage/configure-sync
```

## 🛠️ SDKs

### Python

```bash
pip install docai-python
```

```python
from docai import DocAIClient

client = DocAIClient(api_key="your-api-key")
result = client.ask_document("document.pdf", "What is this about?")
print(result['answer'])
```

### JavaScript/Node.js

```bash
npm install docai-js
```

```javascript
const { DocAIClient } = require('docai-js');

const client = new DocAIClient({ apiKey: 'your-api-key' });
const result = await client.askDocument(file, 'What is this about?');
console.log(result.answer);
```

### Browser

```html
<script src="https://cdn.docai.example.com/sdk/docai-2.0.0.min.js"></script>
<script>
const client = new DocAI.DocAIClient({ apiKey: 'your-api-key' });
// Use client...
</script>
```

## 📈 API Endpoints

### Core Document Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask question about document |
| POST | `/documents/upload` | Upload document |
| GET | `/documents` | List documents |
| GET | `/search` | Search documents |
| GET | `/search/advanced` | Advanced search |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/register` | Register webhook |
| GET | `/webhooks/` | List webhooks |
| PUT | `/webhooks/{id}` | Update webhook |
| DELETE | `/webhooks/{id}` | Delete webhook |
| POST | `/webhooks/{id}/test` | Test webhook |

### Email Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/email/configure` | Configure email |
| POST | `/email/monitoring/start` | Start monitoring |
| POST | `/email/monitoring/stop` | Stop monitoring |
| POST | `/email/share` | Share via email |

### Cloud Storage

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/cloud-storage/connect` | Connect provider |
| POST | `/cloud-storage/configure-sync` | Configure sync |
| POST | `/cloud-storage/sync` | Manual sync |
| GET | `/cloud-storage/files` | List files |
| GET | `/cloud-storage/sync-status` | Sync status |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/info` | API information |
| GET | `/metrics` | Usage metrics |
| GET | `/rate-limits` | Rate limit info |

## 🔍 Advanced Search

### Search Types

- `standard` - Basic text search
- `fuzzy` - Fuzzy matching for typos
- `semantic` - AI-powered semantic search
- `code` - Code-aware search for programming files

### Search Filters

```bash
curl -G \
  -H "X-API-Key: your-api-key" \
  -d "q=machine learning" \
  -d "document_type=pdf" \
  -d "date_from=2024-01-01" \
  -d "size=50" \
  https://api.docai.example.com/v2/search
```

## 🚨 Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid document format",
    "timestamp": "2024-01-15T10:30:00Z",
    "path": "/ask",
    "method": "POST"
  }
}
```

### Common Error Codes

- `AUTHENTICATION_REQUIRED` - Missing or invalid API key
- `RATE_LIMIT_EXCEEDED` - Rate limit exceeded
- `VALIDATION_ERROR` - Invalid request data
- `FILE_TOO_LARGE` - File exceeds size limit
- `UNSUPPORTED_FORMAT` - File format not supported
- `PROCESSING_FAILED` - Document processing failed
- `WEBHOOK_DELIVERY_FAILED` - Webhook delivery failed

## 📊 Monitoring & Analytics

### Health Check

```bash
curl -H "X-API-Key: your-api-key" \
  https://api.docai.example.com/v2/health
```

### Usage Metrics

```bash
curl -H "X-API-Key: your-api-key" \
  https://api.docai.example.com/v2/metrics
```

### Webhook Statistics

```bash
curl -H "X-API-Key: your-api-key" \
  https://api.docai.example.com/v2/webhooks/{webhook-id}/stats
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
DOCAI_API_KEY=your-api-key
DOCAI_BASE_URL=https://api.docai.example.com/v2
DOCAI_TIMEOUT=30000

# Webhook Configuration
DOCAI_WEBHOOK_SECRET=your-webhook-secret

# Email Configuration
DOCAI_SMTP_SERVER=smtp.gmail.com
DOCAI_SMTP_PORT=587
DOCAI_IMAP_SERVER=imap.gmail.com
DOCAI_IMAP_PORT=993

# Cloud Storage
GOOGLE_DRIVE_CLIENT_ID=your-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-client-secret
DROPBOX_APP_KEY=your-app-key
DROPBOX_APP_SECRET=your-app-secret
```

## 🛡️ Security Best Practices

### API Key Security

- Never expose API keys in client-side code
- Use environment variables for API keys
- Rotate API keys regularly
- Use different keys for different environments

### Webhook Security

- Always verify webhook signatures
- Use HTTPS endpoints only
- Implement proper retry logic
- Log webhook deliveries for debugging

### File Upload Security

- Validate file types and sizes
- Scan files for malware
- Use secure file storage
- Implement access controls

## 🚀 Performance Optimization

### Caching

- API responses are cached for 5 minutes
- Use ETags for conditional requests
- Implement client-side caching

### Batch Processing

- Upload multiple documents in batches
- Use async processing for large files
- Implement proper error handling

### Rate Limit Management

- Implement exponential backoff
- Monitor rate limit headers
- Use multiple API keys for high volume

## 📞 Support

- **Documentation**: [https://docs.docai.example.com](https://docs.docai.example.com)
- **API Status**: [https://status.docai.example.com](https://status.docai.example.com)
- **Support Email**: support@docai.example.com
- **Community Forum**: [https://community.docai.example.com](https://community.docai.example.com)
- **GitHub Issues**: [https://github.com/docai/api-issues](https://github.com/docai/api-issues)

## 📄 License

This API is provided under the MIT License. See [LICENSE](LICENSE) for details.

## 🔄 Changelog

### v2.0.0 (2024-01-15)
- Added comprehensive webhook system
- Implemented email integration
- Added cloud storage sync (Google Drive, Dropbox)
- Enhanced authentication with JWT support
- Improved rate limiting with tier-based limits
- Added comprehensive API documentation
- Released Python and JavaScript SDKs

### v1.0.0 (2023-12-01)
- Initial API release
- Basic document processing
- Simple search functionality
- API key authentication