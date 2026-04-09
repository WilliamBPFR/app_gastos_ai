from typing import Optional
import datetime

from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', name='users_pkey'),
        UniqueConstraint('user_email', name='users_user_email_key')
    )

    user_id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    user_email: Mapped[Optional[str]] = mapped_column(String(150))
    user_telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_last_interaction: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user_email_processing_logs: Mapped[list['UserEmailProcessingLogs']] = relationship('UserEmailProcessingLogs', back_populates='user')
    user_google_connections: Mapped[list['UserGoogleConnections']] = relationship('UserGoogleConnections', back_populates='user')


class UserEmailProcessingLogs(Base):
    __tablename__ = 'user_email_processing_logs'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='fk_user_email_processing_logs_user'),
        PrimaryKeyConstraint('id', name='user_email_processing_logs_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_hora_obtencion_datos: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    cantidad_correos_obtenidos: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_attachments: Mapped[int] = mapped_column(Integer, nullable=False)
    procesamiento_ejecutado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    cantidad_correos_validos: Mapped[Optional[int]] = mapped_column(Integer)
    fecha_terminacion_procesamiento: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['Users'] = relationship('Users', back_populates='user_email_processing_logs')


class UserGoogleConnections(Base):
    __tablename__ = 'user_google_connections'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='fk_user_google_connections_user'),
        PrimaryKeyConstraint('id', name='user_google_connections_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    scope: Mapped[Optional[str]] = mapped_column(Text)
    token_type: Mapped[Optional[str]] = mapped_column(String(50))
    last_history_id: Mapped[Optional[str]] = mapped_column(String(100))

    user: Mapped['Users'] = relationship('Users', back_populates='user_google_connections')
