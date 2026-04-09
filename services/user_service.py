from sqlalchemy.orm import Session, joinedload
from db_models import UserGoogleConnections, Users


def get_connected_users(db: Session) -> list[UserGoogleConnections]:
    return (
        db.query(UserGoogleConnections)
        .options(joinedload(UserGoogleConnections.user))
        .join(Users, Users.user_id == UserGoogleConnections.user_id)
        .filter(UserGoogleConnections.is_active == True)
        .all()
    )