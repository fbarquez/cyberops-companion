"""
Email service for sending notifications via SMTP.

Supports:
- Async email sending with aiosmtplib
- HTML and plain text emails
- Jinja2 templates
- Connection pooling and error handling
"""
import logging
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import settings

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
        self.smtp_from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        self.use_ssl = settings.SMTP_SSL
        self.enabled = settings.EMAIL_ENABLED

        # Initialize Jinja2 environment for templates
        if TEMPLATE_DIR.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(TEMPLATE_DIR)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.jinja_env = None
            logger.warning(f"Email template directory not found: {TEMPLATE_DIR}")

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.enabled
            and self.smtp_host
            and self.smtp_user
            and self.smtp_password
            and self.smtp_from
        )

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, generated from HTML if not provided)
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email service not configured. Skipping email send.")
            return False

        # Normalize recipients to list
        if isinstance(to, str):
            to = [to]

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formataddr((self.smtp_from_name, self.smtp_from))
            msg["To"] = ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["Reply-To"] = reply_to

            # Add plain text part (fallback)
            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            else:
                # Generate simple text from HTML by stripping tags
                import re
                text = re.sub(r"<[^>]+>", "", body_html)
                text = re.sub(r"\s+", " ", text).strip()
                msg.attach(MIMEText(text, "plain", "utf-8"))

            # Add HTML part
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            # Calculate all recipients
            all_recipients = list(to)
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.use_tls,
                use_tls=self.use_ssl,
                recipients=all_recipients,
            )

            logger.info(f"Email sent successfully to {to}")
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {to}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to}: {e}")
            return False

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render an email template with the given context.

        Args:
            template_name: Name of the template file (e.g., "notification.html")
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered HTML string
        """
        if not self.jinja_env:
            # Fallback to basic HTML if templates not available
            return self._render_fallback_template(template_name, context)

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return self._render_fallback_template(template_name, context)

    def _render_fallback_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a basic HTML email when templates are not available."""
        title = context.get("title", "Notification")
        message = context.get("message", "")
        priority = context.get("priority", "normal")
        action_url = context.get("action_url", "")
        action_text = context.get("action_text", "View Details")

        priority_color = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#ca8a04",
            "low": "#16a34a",
            "normal": "#6b7280",
        }.get(priority, "#6b7280")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f5;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #18181b; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                                CyberOps Companion
                            </h1>
                        </td>
                    </tr>

                    <!-- Priority Badge -->
                    <tr>
                        <td style="padding: 20px 40px 0;">
                            <span style="display: inline-block; padding: 4px 12px; background-color: {priority_color}; color: #ffffff; font-size: 12px; font-weight: 600; text-transform: uppercase; border-radius: 4px;">
                                {priority}
                            </span>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px;">
                            <h2 style="margin: 0 0 16px; color: #18181b; font-size: 20px; font-weight: 600;">
                                {title}
                            </h2>
                            <p style="margin: 0 0 24px; color: #52525b; font-size: 16px; line-height: 1.6;">
                                {message}
                            </p>
                            {"" if not action_url else f'''
                            <a href="{action_url}" style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff; text-decoration: none; font-weight: 600; border-radius: 6px;">
                                {action_text}
                            </a>
                            '''}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f4f4f5; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; color: #71717a; font-size: 14px;">
                                This is an automated notification from CyberOps Companion.
                            </p>
                            <p style="margin: 8px 0 0; color: #a1a1aa; font-size: 12px;">
                                Sent at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html

    async def send_notification_email(
        self,
        to: str,
        title: str,
        message: str,
        priority: str = "normal",
        notification_type: str = "general",
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> bool:
        """
        Send a notification email using the notification template.

        Args:
            to: Recipient email address
            title: Notification title
            message: Notification message
            priority: Priority level (critical, high, medium, low)
            notification_type: Type of notification
            entity_type: Related entity type (incident, alert, etc.)
            entity_id: Related entity ID
            action_url: URL for the action button

        Returns:
            True if sent successfully
        """
        context = {
            "title": title,
            "message": message,
            "priority": priority,
            "notification_type": notification_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action_url": action_url,
            "action_text": "View Details",
            "year": datetime.utcnow().year,
        }

        body_html = self.render_template("notification.html", context)

        subject = f"[{priority.upper()}] {title}"

        return await self.send_email(
            to=to,
            subject=subject,
            body_html=body_html,
        )

    async def send_incident_alert(
        self,
        to: str | List[str],
        incident_id: str,
        incident_title: str,
        severity: str,
        description: str,
        incident_url: str,
    ) -> bool:
        """Send an incident alert email."""
        context = {
            "title": f"New Incident: {incident_title}",
            "message": description,
            "priority": severity,
            "notification_type": "incident_created",
            "entity_type": "incident",
            "entity_id": incident_id,
            "action_url": incident_url,
            "action_text": "View Incident",
            "year": datetime.utcnow().year,
        }

        body_html = self.render_template("notification.html", context)

        subject = f"[{severity.upper()}] New Incident: {incident_title}"

        return await self.send_email(
            to=to,
            subject=subject,
            body_html=body_html,
        )

    async def send_password_reset(
        self,
        to: str,
        reset_url: str,
        expires_in_minutes: int = 30,
    ) -> bool:
        """Send a password reset email."""
        context = {
            "title": "Password Reset Request",
            "message": f"You requested to reset your password. Click the button below to create a new password. This link will expire in {expires_in_minutes} minutes.",
            "priority": "normal",
            "action_url": reset_url,
            "action_text": "Reset Password",
            "year": datetime.utcnow().year,
        }

        body_html = self.render_template("notification.html", context)

        return await self.send_email(
            to=to,
            subject="Password Reset - CyberOps Companion",
            body_html=body_html,
        )

    async def send_welcome_email(
        self,
        to: str,
        username: str,
        login_url: str,
    ) -> bool:
        """Send a welcome email to new users."""
        context = {
            "title": f"Welcome to CyberOps Companion, {username}!",
            "message": "Your account has been created successfully. You can now log in to access the security operations platform.",
            "priority": "normal",
            "action_url": login_url,
            "action_text": "Log In",
            "year": datetime.utcnow().year,
        }

        body_html = self.render_template("notification.html", context)

        return await self.send_email(
            to=to,
            subject="Welcome to CyberOps Companion",
            body_html=body_html,
        )

    async def send_test_email(self, to: str) -> bool:
        """Send a test email to verify configuration."""
        return await self.send_notification_email(
            to=to,
            title="Test Email",
            message="This is a test email from CyberOps Companion. If you received this, your email configuration is working correctly.",
            priority="normal",
            notification_type="test",
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
