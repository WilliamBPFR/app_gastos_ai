from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from db_models import UserEmailProcessingLogs, UserGoogleConnections
from fastapi_deps import verify_internal_token
from schemas import ConnectedUserResponse, CheckUserRequest, CheckUserResponse, MessageItem, AttachmentItem
from services.user_service import get_connected_users
from services.gmail_service import get_fresh_access_token, list_recent_messages

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_internal_token)],
)

@router.get("/users/connected", response_model=list[ConnectedUserResponse])
def list_connected_users(db: Session = Depends(get_db)):
    users = get_connected_users(db)
    return [
        ConnectedUserResponse(
            telegram_chat_id=u.user.user_telegram_chat_id,
            google_email=u.user.user_email,
        )
        for u in users
    ]

@router.post("/gmail/check-user", response_model=CheckUserResponse)
async def check_user(payload: CheckUserRequest, db: Session = Depends(get_db)):
    try:
        google_user_log = db.query(UserGoogleConnections).filter_by(user_id=payload.user_id).first()
        if google_user_log.last_email_history_checkup and google_user_log.last_email_history_checkup.fecha_hora_obtencion_datos > hora_obtencion_datos:
            raise HTTPException(status_code=400, detail="No se pudieron obtener los correos más recientes. El último escaneo exitoso es más reciente que la fecha de obtención de datos actual.")
        
        access_token, user = await get_fresh_access_token(db, payload.user_id)

        messages, hora_obtencion_datos = await list_recent_messages(access_token, max_results=20)
       
        new_log_item = UserEmailProcessingLogs(
            user_id=user.user.user_id,
            cantidad_correos_obtenidos=len(messages),
            cantidad_attachments=sum(len(m.get("attachments", [])) for m in messages),
            fecha_hora_obtencion_datos=hora_obtencion_datos
        )
            
        db.add(new_log_item)
        google_user_log.last_email_history_checkup = new_log_item
        
        db.commit()

        return CheckUserResponse(
            connected=True,
            google_email=user.user.user_email,
            id_log_db=new_log_item.id,
            messages=[
                MessageItem(
                    full_msg_id=m["full_msg_id"],
                    message_id=m["message_id"],
                    threadId=m.get("threadId"),
                    snippet=m.get("snippet"),
                    internalDate=m.get("internalDate"),
                    headers=m.get("headers"),
                    attachments=[
                        AttachmentItem(**a)
                        for a in m.get("attachments", [])
                    ],
                )
                for m in messages
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))