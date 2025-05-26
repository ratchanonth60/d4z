from datetime import datetime

from fastapi_mail import FastMail, MessageSchema
from pydantic import EmailStr

from app.core.config import settings  #
from app.tasks.email_tasks import (
    send_password_reset_email_task,
    send_verification_email_task,
)  #


def task_send_verification_email(
    email_to: EmailStr, username: str, verification_link: str
):
    print(f"Queueing verification email for {email_to} with username {username}")  #
    send_verification_email_task.delay(  # type: ignore #
        email_to=str(email_to), username=username, verification_link=verification_link
    )
    print(f"Verification email task for {email_to} has been queued.")  #


def task_send_password_reset_email(email_to: EmailStr, username: str, reset_link: str):
    print(f"Queueing password reset email for {email_to} with username {username}")  #
    send_password_reset_email_task.delay(  # type: ignore #
        email_to=str(email_to), username=username, reset_link=reset_link
    )
    print(f"Password reset email task for {email_to} has been queued.")  #


# This function might be deprecated if all email sending is via Celery tasks.
# Keeping it for now as it's referenced.
async def send_verification_email(email_to: str, username: str, verification_link: str):
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

    try:
        fm = FastMail(mail_conf)
        await fm.send_message(message, template_name="verification_email.html")
        print(f"Verification email sent to {email_to} using template.")
    except Exception as e:
        print(f"Error sending verification email to {email_to} using template: {e}")
        pass


async def send_password_reset_email(email_to: str, username: str, reset_link: str):  #
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

    try:
        fm = FastMail(mail_conf)  #
        await fm.send_message(message, template_name="password_reset_email.html")  #
        print(f"Password reset email sent to {email_to} using template.")  #
    except Exception as e:
        print(
            f"Error sending password reset email to {email_to} using template: {e}"
        )  #
        pass
