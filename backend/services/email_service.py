"""
Email Integration Service for Advanced Document Intelligence Platform
Handles email processing, SMTP/IMAP integration, and email-based document sharing
"""

import asyncio
import email
import imaplib
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from email.utils import parseaddr
import os
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import re
import uuid
import base64

from services.cache_service import cache_service
from services.webhook_service import webhook_service

logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Email server configuration"""
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False

@dataclass
class EmailAttachment:
    """Email attachment information"""
    filename: str
    content_type: str
    content: bytes
    size: int

@dataclass
class EmailMessage:
    """Parsed email message"""
    message_id: str
    subject: str
    sender: str
    recipients: List[str]
    body_text: str
    body_html: str
    attachments: List[EmailAttachment]
    received_date: datetime
    headers: Dict[str, str]

@dataclass
class DocumentUploadRequest:
    """Document upload request from email"""
    user_email: str
    document_name: str
    document_content: bytes
    content_type: str
    tags: List[str]
    processing_instructions: Optional[str] = None

class EmailProcessor:
    """Email processing and document extraction"""
    
    def __init__(self):
        """Initialize email processor"""
        self.supported_attachments = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'text/html': '.html',
            'application/json': '.json',
            'text/csv': '.csv',
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/tiff': '.tiff'
        }
        
        # Email processing patterns
        self.instruction_patterns = {
            'tags': re.compile(r'#tags?\s*[:=]\s*([^\n]+)', re.IGNORECASE),
            'process': re.compile(r'#process\s*[:=]\s*([^\n]+)', re.IGNORECASE),
            'questions': re.compile(r'#questions?\s*[:=]\s*(\d+)', re.IGNORECASE),
            'model': re.compile(r'#model\s*[:=]\s*([^\n\s]+)', re.IGNORECASE),
            'share': re.compile(r'#share\s*[:=]\s*([^\n]+)', re.IGNORECASE)
        }
    
    def parse_email(self, raw_email: bytes) -> EmailMessage:
        """Parse raw email into structured format"""
        try:
            msg = email.message_from_bytes(raw_email)
            
            # Extract basic information
            message_id = msg.get('Message-ID', str(uuid.uuid4()))
            subject = self._decode_header(msg.get('Subject', ''))
            sender = self._decode_header(msg.get('From', ''))
            
            # Parse recipients
            recipients = []
            for header in ['To', 'Cc', 'Bcc']:
                if msg.get(header):
                    recipients.extend(self._parse_addresses(msg.get(header)))
            
            # Extract date
            date_str = msg.get('Date')
            received_date = self._parse_date(date_str) if date_str else datetime.utcnow()
            
            # Extract body content
            body_text, body_html = self._extract_body(msg)
            
            # Extract attachments
            attachments = self._extract_attachments(msg)
            
            # Extract headers
            headers = dict(msg.items())
            
            return EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                received_date=received_date,
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            raise
    
    def extract_document_requests(self, email_msg: EmailMessage) -> List[DocumentUploadRequest]:
        """Extract document upload requests from email"""
        requests = []
        
        # Get user email
        user_email = self._extract_email_address(email_msg.sender)
        if not user_email:
            logger.warning(f"Could not extract user email from: {email_msg.sender}")
            return requests
        
        # Parse processing instructions from email body
        instructions = self._parse_processing_instructions(email_msg.body_text)
        
        # Process attachments
        for attachment in email_msg.attachments:
            if self._is_supported_document(attachment):
                # Generate tags from email subject and instructions
                tags = self._generate_tags(email_msg.subject, instructions)
                
                request = DocumentUploadRequest(
                    user_email=user_email,
                    document_name=attachment.filename,
                    document_content=attachment.content,
                    content_type=attachment.content_type,
                    tags=tags,
                    processing_instructions=instructions.get('process')
                )
                
                requests.append(request)
        
        # If no attachments, check if email body contains document content
        if not requests and email_msg.body_text:
            # Check if body looks like a document
            if len(email_msg.body_text.strip()) > 100:  # Minimum content length
                tags = self._generate_tags(email_msg.subject, instructions)
                
                # Generate filename from subject
                filename = self._generate_filename_from_subject(email_msg.subject)
                
                request = DocumentUploadRequest(
                    user_email=user_email,
                    document_name=filename,
                    document_content=email_msg.body_text.encode('utf-8'),
                    content_type='text/plain',
                    tags=tags,
                    processing_instructions=instructions.get('process')
                )
                
                requests.append(request)
        
        return requests
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header value"""
        if not header_value:
            return ''
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string.strip()
        except Exception:
            return header_value
    
    def _parse_addresses(self, address_header: str) -> List[str]:
        """Parse email addresses from header"""
        addresses = []
        try:
            for addr in address_header.split(','):
                name, email_addr = parseaddr(addr.strip())
                if email_addr:
                    addresses.append(email_addr)
        except Exception:
            pass
        return addresses
    
    def _extract_email_address(self, from_header: str) -> Optional[str]:
        """Extract email address from From header"""
        try:
            name, email_addr = parseaddr(from_header)
            return email_addr if email_addr else None
        except Exception:
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string"""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()
    
    def _extract_body(self, msg) -> Tuple[str, str]:
        """Extract text and HTML body from email"""
        text_body = ''
        html_body = ''
        
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    # Skip attachments
                    if 'attachment' in content_disposition:
                        continue
                    
                    if content_type == 'text/plain':
                        charset = part.get_content_charset() or 'utf-8'
                        text_body += part.get_payload(decode=True).decode(charset, errors='ignore')
                    elif content_type == 'text/html':
                        charset = part.get_content_charset() or 'utf-8'
                        html_body += part.get_payload(decode=True).decode(charset, errors='ignore')
            else:
                content_type = msg.get_content_type()
                charset = msg.get_content_charset() or 'utf-8'
                content = msg.get_payload(decode=True).decode(charset, errors='ignore')
                
                if content_type == 'text/plain':
                    text_body = content
                elif content_type == 'text/html':
                    html_body = content
                else:
                    text_body = content  # Fallback
        
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
        
        return text_body, html_body
    
    def _extract_attachments(self, msg) -> List[EmailAttachment]:
        """Extract attachments from email"""
        attachments = []
        
        try:
            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        content_type = part.get_content_type()
                        content = part.get_payload(decode=True)
                        
                        if content:
                            attachment = EmailAttachment(
                                filename=filename,
                                content_type=content_type,
                                content=content,
                                size=len(content)
                            )
                            attachments.append(attachment)
        
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}")
        
        return attachments
    
    def _is_supported_document(self, attachment: EmailAttachment) -> bool:
        """Check if attachment is a supported document type"""
        return attachment.content_type in self.supported_attachments
    
    def _parse_processing_instructions(self, body_text: str) -> Dict[str, Any]:
        """Parse processing instructions from email body"""
        instructions = {}
        
        for key, pattern in self.instruction_patterns.items():
            match = pattern.search(body_text)
            if match:
                value = match.group(1).strip()
                
                if key == 'tags':
                    # Split tags by comma or space
                    instructions[key] = [tag.strip() for tag in re.split(r'[,\s]+', value) if tag.strip()]
                elif key == 'questions':
                    instructions[key] = int(value)
                else:
                    instructions[key] = value
        
        return instructions
    
    def _generate_tags(self, subject: str, instructions: Dict[str, Any]) -> List[str]:
        """Generate tags from email subject and instructions"""
        tags = []
        
        # Add tags from instructions
        if 'tags' in instructions:
            tags.extend(instructions['tags'])
        
        # Extract tags from subject
        subject_tags = re.findall(r'#(\w+)', subject)
        tags.extend(subject_tags)
        
        # Add default tag
        tags.append('email-upload')
        
        # Remove duplicates and return
        return list(set(tags))
    
    def _generate_filename_from_subject(self, subject: str) -> str:
        """Generate filename from email subject"""
        # Clean subject for filename
        filename = re.sub(r'[^\w\s-]', '', subject).strip()
        filename = re.sub(r'[-\s]+', '-', filename)
        
        if not filename:
            filename = f"email-content-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        return f"{filename}.txt"

class EmailService:
    """Complete email integration service"""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """Initialize email service"""
        self.config = config
        self.processor = EmailProcessor()
        self.cache = cache_service
        
        # Email monitoring state
        self.is_monitoring = False
        self.last_check = datetime.utcnow()
        
        logger.info("📧 Email Service initialized")
    
    async def configure_email(self, user_id: str, email_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure email settings for a user"""
        try:
            # Validate configuration
            required_fields = ['smtp_server', 'smtp_port', 'imap_server', 'imap_port', 'username', 'password']
            for field in required_fields:
                if field not in email_config:
                    raise ValueError(f"Missing required field: {field}")
            
            # Test connection
            test_result = await self._test_email_connection(email_config)
            if not test_result['success']:
                raise ValueError(f"Email connection test failed: {test_result['error']}")
            
            # Store configuration (encrypted in production)
            config_key = f"email_config:{user_id}"
            self.cache.set(config_key, email_config, expire_seconds=86400 * 30)  # 30 days
            
            return {
                "message": "Email configuration saved successfully",
                "test_result": test_result,
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error configuring email for user {user_id}: {str(e)}")
            raise
    
    async def start_email_monitoring(self, user_id: str) -> Dict[str, Any]:
        """Start monitoring email for document uploads"""
        try:
            # Get user's email configuration
            config = await self._get_user_email_config(user_id)
            if not config:
                raise ValueError("Email not configured for user")
            
            # Start monitoring task
            if not self.is_monitoring:
                asyncio.create_task(self._monitor_emails())
                self.is_monitoring = True
            
            # Mark user for monitoring
            monitoring_key = f"email_monitoring:{user_id}"
            self.cache.set(monitoring_key, True, expire_seconds=86400)  # 24 hours
            
            return {
                "message": "Email monitoring started",
                "user_id": user_id,
                "started_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error starting email monitoring for user {user_id}: {str(e)}")
            raise
    
    async def process_email_upload(self, user_id: str, raw_email: bytes) -> Dict[str, Any]:
        """Process email for document uploads"""
        try:
            # Parse email
            email_msg = self.processor.parse_email(raw_email)
            
            # Extract document requests
            requests = self.processor.extract_document_requests(email_msg)
            
            if not requests:
                return {
                    "message": "No documents found in email",
                    "email_subject": email_msg.subject,
                    "attachments_count": len(email_msg.attachments)
                }
            
            # Process each document request
            results = []
            for request in requests:
                try:
                    # Here you would integrate with your document upload service
                    # For now, we'll simulate the upload
                    document_id = str(uuid.uuid4())
                    
                    # Trigger webhook for document upload
                    await webhook_service.trigger_webhook(
                        event_type="document.uploaded",
                        payload={
                            "document_id": document_id,
                            "filename": request.document_name,
                            "user_id": user_id,
                            "source": "email",
                            "tags": request.tags,
                            "content_type": request.content_type,
                            "size": len(request.document_content)
                        },
                        user_id=user_id
                    )
                    
                    results.append({
                        "document_id": document_id,
                        "filename": request.document_name,
                        "status": "uploaded",
                        "tags": request.tags
                    })
                    
                except Exception as e:
                    results.append({
                        "filename": request.document_name,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "message": f"Processed {len(results)} documents from email",
                "email_subject": email_msg.subject,
                "sender": email_msg.sender,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing email upload: {str(e)}")
            raise
    
    async def send_document_share_email(self, sender_user_id: str, recipient_email: str, 
                                      document_id: str, document_name: str, 
                                      share_message: Optional[str] = None) -> Dict[str, Any]:
        """Send email to share a document"""
        try:
            # Get sender's email configuration
            config = await self._get_user_email_config(sender_user_id)
            if not config:
                raise ValueError("Email not configured for sender")
            
            # Create email content
            subject = f"Document shared: {document_name}"
            
            # Generate share link (in production, this would be a secure link)
            share_link = f"https://docai.example.com/shared/{document_id}"
            
            body = f"""
Hello,

A document has been shared with you:

Document: {document_name}
Shared by: {config['username']}

{share_message or 'No additional message provided.'}

You can view the document here: {share_link}

Best regards,
Document Intelligence Platform
            """.strip()
            
            # Send email
            success = await self._send_email(
                config=config,
                to_email=recipient_email,
                subject=subject,
                body=body
            )
            
            if success:
                # Trigger webhook
                await webhook_service.trigger_webhook(
                    event_type="document.shared",
                    payload={
                        "document_id": document_id,
                        "document_name": document_name,
                        "sender_user_id": sender_user_id,
                        "recipient_email": recipient_email,
                        "share_link": share_link
                    },
                    user_id=sender_user_id
                )
                
                return {
                    "message": "Document share email sent successfully",
                    "recipient": recipient_email,
                    "document_name": document_name,
                    "sent_at": datetime.utcnow().isoformat()
                }
            else:
                raise Exception("Failed to send email")
            
        except Exception as e:
            logger.error(f"Error sending document share email: {str(e)}")
            raise
    
    async def send_processing_notification(self, user_id: str, document_name: str, 
                                         status: str, results: Optional[Dict[str, Any]] = None) -> bool:
        """Send email notification about document processing"""
        try:
            # Get user's email configuration
            config = await self._get_user_email_config(user_id)
            if not config:
                return False
            
            # Create notification email
            if status == "completed":
                subject = f"Document processing completed: {document_name}"
                body = f"""
Your document "{document_name}" has been processed successfully.

Processing Results:
- Status: Completed
- Processing Time: {results.get('processing_time', 'N/A')}
- Questions Generated: {results.get('questions_count', 0)}
- Confidence Score: {results.get('confidence_score', 'N/A')}

You can view the results in your dashboard.
                """.strip()
            else:
                subject = f"Document processing failed: {document_name}"
                body = f"""
Unfortunately, processing of your document "{document_name}" has failed.

Error Details:
{results.get('error_message', 'Unknown error occurred')}

Please try uploading the document again or contact support if the issue persists.
                """.strip()
            
            return await self._send_email(
                config=config,
                to_email=config['username'],  # Send to user's email
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Error sending processing notification: {str(e)}")
            return False
    
    async def _monitor_emails(self):
        """Background task to monitor emails for document uploads"""
        while self.is_monitoring:
            try:
                # Get all users with email monitoring enabled
                monitoring_users = await self._get_monitoring_users()
                
                for user_id in monitoring_users:
                    try:
                        await self._check_user_emails(user_id)
                    except Exception as e:
                        logger.error(f"Error checking emails for user {user_id}: {str(e)}")
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in email monitoring loop: {str(e)}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _check_user_emails(self, user_id: str):
        """Check emails for a specific user"""
        try:
            config = await self._get_user_email_config(user_id)
            if not config:
                return
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            mail.login(config['username'], config['password'])
            mail.select('INBOX')
            
            # Search for unread emails since last check
            since_date = self.last_check.strftime('%d-%b-%Y')
            status, messages = mail.search(None, f'UNSEEN SINCE {since_date}')
            
            if status == 'OK' and messages[0]:
                email_ids = messages[0].split()
                
                for email_id in email_ids:
                    try:
                        # Fetch email
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        if status == 'OK':
                            raw_email = msg_data[0][1]
                            
                            # Process email for documents
                            await self.process_email_upload(user_id, raw_email)
                            
                            # Mark as read
                            mail.store(email_id, '+FLAGS', '\\Seen')
                    
                    except Exception as e:
                        logger.error(f"Error processing email {email_id}: {str(e)}")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error checking user emails: {str(e)}")
    
    async def _test_email_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test email server connection"""
        try:
            # Test SMTP connection
            smtp_server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                smtp_server.starttls()
            smtp_server.login(config['username'], config['password'])
            smtp_server.quit()
            
            # Test IMAP connection
            imap_server = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            imap_server.login(config['username'], config['password'])
            imap_server.logout()
            
            return {
                "success": True,
                "message": "Email connection test successful"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_email(self, config: Dict[str, Any], to_email: str, 
                         subject: str, body: str, attachments: Optional[List] = None) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('use_tls', True):
                server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    async def _get_user_email_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's email configuration"""
        try:
            config_key = f"email_config:{user_id}"
            return self.cache.get(config_key)
        except Exception:
            return None
    
    async def _get_monitoring_users(self) -> List[str]:
        """Get list of users with email monitoring enabled"""
        try:
            # In production, this would query the database
            # For now, we'll check cache for monitoring flags
            users = []
            # This is a simplified implementation
            return users
        except Exception:
            return []

# Global email service instance
email_service = EmailService()