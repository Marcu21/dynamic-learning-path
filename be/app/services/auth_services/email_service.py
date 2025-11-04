from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# SendGrid configuration from settings
SENDGRID_API_KEY = settings.sendgrid_api_key
FROM_EMAIL = settings.from_email
FRONTEND_URL = settings.frontend_url

if not SENDGRID_API_KEY or SENDGRID_API_KEY == "your-sendgrid-api-key-here":
    logger.warning("SENDGRID_API_KEY not configured properly")


class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=SENDGRID_API_KEY) if SENDGRID_API_KEY else None
    
    async def send_magic_link(self, email: str, token: str) -> bool:
        """Send magic link email for authentication"""
        if not self.sg:
            logger.error("SendGrid client not initialized")
            return False
        
        magic_link = f"{FRONTEND_URL}/auth/verify?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="X-UA-Compatible" content="ie=edge">
            <title>Your Login Link</title>
            <style>
                /* Base styles */
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f7;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
                }}
                .email-container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .email-card {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                    text-align: center;
                }}
                h1 {{
                    color: #2c3e50;
                    font-size: 24px;
                    font-weight: 600;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #576574;
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 0 0 20px;
                }}
                .cta-button {{
                    display: inline-block;
                    background-color: #3498db;
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: 500;
                    text-decoration: none;
                    padding: 14px 28px;
                    border-radius: 50px; /* Pill shape */
                    margin: 20px 0;
                    transition: background-color 0.2s;
                }}
                .cta-button:hover {{
                    background-color: #2980b9;
                }}
                .footer-text {{
                    color: #95a5a6;
                    font-size: 14px;
                    margin-top: 30px;
                }}
                .footer-link {{
                    color: #95a5a6;
                    word-break: break-all;
                    font-size: 12px;
                    margin-top: 10px;
                }}
                hr {{
                    border: none;
                    border-top: 1px solid #e0e0e0;
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-card">
                    <h1>Dynamic Learning Path</h1>
                    <p>Welcome back! Click the button below to securely sign in to your account.</p>
                    
                    <a href="{magic_link}" class="cta-button">Sign In to Your Account</a>
                    
                    <p class="footer-text">This link is valid for 15 minutes. If you did not request this email, you can safely ignore it.</p>
                    
                    <hr>
                    
                    <div class="footer-link">
                        If you're having trouble with the button, copy and paste this URL into your web browser:<br>
                        <a href="{magic_link}" style="color: #95a5a6;">{magic_link}</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=[email],
            subject="Your Login Link - Dynamic Learning Path",
            html_content=html_content
        )
        
        try:
            response = self.sg.send(message)
            logger.info(f"Magic link email sent to {email}, status code: {response.status_code}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send magic link email to {email}: {str(e)}")
            return False

# Singleton instance
email_service = EmailService()
