from datetime import datetime

from fastapi_mail import FastMail, MessageSchema

from app.core.config import settings


async def send_verification_email(email_to: str, username: str, verification_link: str):
    mail_conf = settings.mail_connection_config  # Get ConnectionConfig from settings

    current_year = datetime.now().year
    expiry_duration_text = f"{settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hour"
    if settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS > 1:
        expiry_duration_text += "s"

    template_body_context = {
        "username": username,
        "verification_link": verification_link,
        "app_title": settings.APP_TITLE,
        "token_expiry_duration_text": expiry_duration_text,
        "current_year": current_year,
    }

    message = MessageSchema(
        subject=f"Verify your email address for {settings.APP_TITLE}",
        recipients=[email_to],
        template_body=template_body_context,  # Pass context for the template
        subtype="html",  # Still important
    )

    try:
        fm = FastMail(mail_conf)
        # Specify the template file name when sending
        await fm.send_message(message, template_name="verification_email.html")
        print(f"Verification email sent to {email_to} using template.")
    except Exception as e:
        print(f"Error sending verification email to {email_to} using template: {e}")
        # Add robust error handling/logging here
        pass

