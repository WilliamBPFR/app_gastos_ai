import os
import resend
from config import config

resend.api_key = config.RESEND_API_KEY


def send_email_with_resend(receiver_email:str, subject:str, html_content:str):
    params: resend.Emails.SendParams = {
        "from": "App Gastos Personales <notifications@appgastos.williamferreiratech.com>",
        "to": [receiver_email],
        "subject": subject,
        "html": html_content,
    }

    email = resend.Emails.send(params)
    print(email)

if __name__ == "__main__":
    send_email_with_resend(
        receiver_email="williamchawillferferreira@gmail.com",
        subject="Test Email from Resend",
        html_content="<h1>Hello from Resend!</h1><p>This is a test email.</p>"
    )
    