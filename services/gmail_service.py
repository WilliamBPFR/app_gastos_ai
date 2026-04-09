import httpx
import base64
from sqlalchemy.orm import Session
import datetime

from config import config
from db_models import UserGoogleConnections
from utils.crypto_utils import decrypt_text
from services.s3_service import s3_service

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



async def get_fresh_access_token(db: Session, user_id: str) -> tuple[str, UserGoogleConnections]:
    user = (
        db.query(UserGoogleConnections)
        .filter(
            UserGoogleConnections.user_id == user_id,
            UserGoogleConnections.is_active == True,
        )
        .first()
    )

    if not user:
        raise ValueError("Usuario no conectado")

    refresh_token = decrypt_text(user.refresh_token_encrypted)

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=config.GOOGLE_OAUTH_SCOPE.split(" "),
    )
    creds.refresh(Request())  # hace el refresh contra Google
    return creds.token, user

def extract_headers(headers):
    wanted = {"From", "Subject", "Date", "To", "Cc", "Bcc", "Reply-To", "Message-ID"}
    return {h["name"]: h["value"] for h in headers if h["name"] in wanted}

def extract_attachments_from_part(service, message_id, part):
    attachments = []

    filename = part.get("filename")
    body = part.get("body", {})
    attachment_id = body.get("attachmentId")

    if filename and attachment_id:
        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(
                userId="me",
                messageId=message_id,
                id=attachment_id,
            )
            .execute()
        )

        data = attachment["data"]
        file_bytes = base64.urlsafe_b64decode(data.encode("UTF-8"))

        file_s3_route = s3_service.upload_bytes(
            data=file_bytes,
            object_name=f"gmail_attachments/{message_id}/{attachment_id[:10]}_{filename}",
            content_type=part.get("mimeType"),
        )

        attachments.append({
            "filename": attachment_id[:10] + "_" + filename,
            "s3_route": file_s3_route,
            "mimeType": part.get("mimeType"),
            "size": body.get("size"),
            "attachmentId": attachment_id,
        })



    for child in part.get("parts", []):
        attachments.extend(extract_attachments_from_part(service, message_id, child))

    return attachments

async def list_recent_messages(access_token: str, max_results: int = 5, datetime_obtencion_datos: datetime.datetime | None = None):
    try: 
        print("Listando mensajes recientes con access_token:", access_token[:10] + "...")
        creds = Credentials(token=access_token)
        service = build("gmail", "v1", credentials=creds)
        req = {
            "userId": "me",
            "maxResults": max_results,
            "includeSpamTrash": False,
        }
        
        datetime_inicio_obtencion = datetime.datetime(datetime_obtencion_datos, tzinfo=datetime.timezone.utc) if datetime_obtencion_datos else datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)        
        hora_obtencion_datos = datetime.datetime.now(datetime.timezone.utc)

        date_inicio_ts = int(datetime_inicio_obtencion.timestamp())
        date_fin_ts = int(hora_obtencion_datos.timestamp())

        req["q"] = f"after:{date_inicio_ts} before:{date_fin_ts}"

        response = service.users().messages().list(**req).execute()
        messages = response.get("messages", [])

        detailed_messages = []
        for msg in messages:
            message_id = msg["id"]
            full_msg = (service.users().messages().get(userId="me", id=message_id, format="full").execute())  # format="metadata", metadataHeaders=["From", "Subject", "Date", "To", "Cc", "Bcc", "ReplyTo"]).execute())
            
            payload = full_msg.get("payload", {})
            headers = extract_headers(payload.get("headers", []))
            attachments = extract_attachments_from_part(service, message_id, payload)

            detailed_messages.append({
                "full_msg_id": full_msg.get("id"),
                "message_id": message_id,
                "threadId": full_msg.get("threadId"),
                "snippet": full_msg.get("snippet"),
                "internalDate": full_msg.get("internalDate"),
                "headers": headers,
                "attachments": attachments,
            })
            # detailed_messages.append(msg)
        
        return detailed_messages, hora_obtencion_datos, datetime_inicio_obtencion
    
    except Exception as e:
        print(f"Error al listar mensajes: {e}")
        raise ValueError(f"Error al listar mensajes: {str(e)}")
  
async def get_message_detail(access_token: str, message_id: str):
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
        )

    if resp.status_code != 200:
        raise ValueError(f"Error leyendo mensaje: {resp.text}")

    return resp.json()