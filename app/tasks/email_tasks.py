from datetime import datetime
import logging

from celery import shared_task
from fastapi_mail import FastMail, MessageSchema
import asyncio

from app.core.config import settings  #

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(
    self, email_to: str, username: str, verification_link: str
):
    mail_conf = settings.mail_connection_config
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
        logger.info(
            f"Task send_verification_email_task: Attempting to send email to {email_to}"
        )

        async def send_async():
            await fm.send_message(message, template_name="verification_email.html")

        try:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(send_async())
        except RuntimeError:
            asyncio.run(send_async())
        logger.info(
            f"Task send_verification_email_task: Verification email sent to {email_to}"
        )
        return {"message": "Email sent successfully", "recipient": email_to}  #
    except Exception as exc:
        logger.error(
            f"Task send_verification_email_task: Error sending email to {email_to}: {exc}",
            exc_info=True,  # This will include stack trace for the error
        )
        raise self.retry(exc=exc)  #


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(  #
    self, email_to: str, username: str, reset_link: str
):
    mail_conf = settings.mail_connection_config  #
    current_year = datetime.now().year  #
    expiry_duration_text = f"{settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hour"  #
    if settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS > 1:  #
        expiry_duration_text += "s"  #

    template_body_context = {  #
        "username": username,  #
        "reset_link": reset_link,  #
        "app_title": settings.APP_TITLE,  #
        "token_expiry_duration_text": expiry_duration_text,  #
        "current_year": current_year,  #
    }
    message = MessageSchema(  #
        subject=f"Password Reset Request for {settings.APP_TITLE}",  #
        recipients=[email_to],  #
        template_body=template_body_context,  #
        subtype="html",  #
    )
    fm = FastMail(mail_conf)  #
    try:
        logger.info(
            f"Task send_password_reset_email_task: Attempting to send email to {email_to}"
        )  #

        async def send_async():  #
            await fm.send_message(message, template_name="password_reset_email.html")  #

        try:
            loop = asyncio.get_running_loop()  #
            loop.run_until_complete(send_async())  #
        except RuntimeError:  #
            asyncio.run(send_async())  #
        logger.info(
            f"Task send_password_reset_email_task: Password reset email sent to {email_to}"
        )  #
        return {
            "message": "Password reset email sent successfully",
            "recipient": email_to,
        }  #
    except Exception as exc:
        logger.info(
            f"Task send_password_reset_email_task: Error sending email to {email_to}: {exc}"
        )  #
        raise self.retry(exc=exc)  #
