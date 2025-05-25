from datetime import datetime

from fastapi_mail import FastMail, MessageSchema

from app.core.config import settings
from app.tasks.email_tasks import send_verification_email_task


async def task_send_verification_email(
    email_to: str, username: str, verification_link: str
):
    """
    Sends a verification email by queuing a Celery task.
    This function itself can remain async if called from async FastAPI code,
    but the task it calls will be executed by a Celery worker.
    """
    print(f"Queueing verification email for {email_to} with username {username}")
    # Call the Celery task using .delay() or .apply_async()
    # .delay() is a shortcut for .apply_async()
    send_verification_email_task.delay(  # type: ignore
        email_to=email_to, username=username, verification_link=verification_link
    )
    # The task is now queued and will be picked up by a Celery worker.
    # You don't await the task here if you want it to be non-blocking.
    print(f"Verification email task for {email_to} has been queued.")


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
