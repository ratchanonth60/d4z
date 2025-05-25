from datetime import datetime  # For current_year

from celery import shared_task
from fastapi_mail import FastMail, MessageSchema

from app.core.config import settings  # For mail settings

# It's good practice to initialize FastMail with the config inside the task
# or ensure the config is globally available if the task runs in a separate process.
# For simplicity here, we'll re-create the ConnectionConfig or fetch it.


@shared_task(
    bind=True, max_retries=3, default_retry_delay=60
)  # bind=True gives access to self
def send_verification_email_task(
    self, email_to: str, username: str, verification_link: str
):
    """
    Celery task to send a verification email.
    """
    mail_conf = (
        settings.mail_connection_config
    )  # Get ConnectionConfig from app settings

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
        template_body=template_body_context,
        subtype="html",
    )

    fm = FastMail(mail_conf)
    try:
        print(
            f"Task send_verification_email_task: Attempting to send email to {email_to}"
        )
        # FastMail's send_message is already async, but Celery tasks are typically synchronous wrappers
        # unless you are using Celery's async capabilities more deeply.
        # For fastapi-mail, which is async, you might need to run its async code within the sync Celery task.
        # A simple way for now, assuming the FastMail instance can be used synchronously in this context
        # or if the Celery worker runs in an event loop (e.g., with `gevent` or `eventlet`).
        # If FastMail strictly requires an event loop, you'd need to manage it here:
        # import asyncio
        # asyncio.run(fm.send_message(message, template_name="verification_email.html"))
        # However, for simplicity, let's assume direct call works or adjust worker type.
        # A more robust approach for async libraries within sync Celery tasks:

        # For fastapi-mail which is async, run it in a new event loop if the worker is sync
        import asyncio

        async def send_async():
            await fm.send_message(message, template_name="verification_email.html")

        # If celery worker is not running with an async pool (like gevent/eventlet)
        # you need to run the async code in a new loop.
        # This is a common pattern for calling async code from sync Celery tasks.
        try:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(send_async())
        except RuntimeError:  # No running event loop
            asyncio.run(send_async())

        print(
            f"Task send_verification_email_task: Verification email sent to {email_to}"
        )
        return {"message": "Email sent successfully", "recipient": email_to}
    except Exception as exc:
        print(
            f"Task send_verification_email_task: Error sending email to {email_to}: {exc}"
        )
        # Retry the task if it fails, Celery will handle this based on max_retries
        raise self.retry(exc=exc)
