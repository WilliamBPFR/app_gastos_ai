from pydantic import BaseModel
from typing import Optional, List

class ConnectedUserResponse(BaseModel):
    telegram_chat_id: str
    google_email: Optional[str] = None

class CheckUserRequest(BaseModel):
    user_id: str

class AttachmentItem(BaseModel):
    filename: str
    s3_route: str
    mimeType: Optional[str] = None
    size: Optional[int] = None
    attachmentId: Optional[str] = None

class MessageItem(BaseModel):
    full_msg_id: str
    message_id: str
    threadId: Optional[str] = None
    snippet: Optional[str] = None
    internalDate: Optional[str] = None
    headers: Optional[dict] = None
    attachments: Optional[List[AttachmentItem]] = None

class CheckUserResponse(BaseModel):
    connected: bool
    google_email: Optional[str] = None
    id_log_db: Optional[int] = None
    messages: List[MessageItem] = []