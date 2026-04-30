from typing import Optional
import datetime
import decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKeyConstraint, Identity, Index, Integer, Numeric, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class AccountTypes(Base):
    __tablename__ = 'account_types'
    __table_args__ = (
        PrimaryKeyConstraint('account_type_id', name='account_types_pkey'),
    )

    account_type_id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    account_type_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    account_type_description: Mapped[Optional[str]] = mapped_column(Text)

    user_accounts: Mapped[list['UserAccounts']] = relationship('UserAccounts', back_populates='account_type')


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
    account_activated: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    user_accounts: Mapped[list['UserAccounts']] = relationship('UserAccounts', back_populates='user')
    user_categories: Mapped[list['UserCategories']] = relationship('UserCategories', back_populates='user')
    user_email_processing_logs: Mapped[list['UserEmailProcessingLogs']] = relationship('UserEmailProcessingLogs', back_populates='user')
    user_passwords: Mapped['UserPasswords'] = relationship('UserPasswords', uselist=False, back_populates='user')
    user_reset_password: Mapped[list['UserResetPassword']] = relationship('UserResetPassword', back_populates='user')
    user_financial_transactions: Mapped[list['UserFinancialTransactions']] = relationship('UserFinancialTransactions', back_populates='user')
    user_google_connections: Mapped[list['UserGoogleConnections']] = relationship('UserGoogleConnections', back_populates='user')


class UserAccounts(Base):
    __tablename__ = 'user_accounts'
    __table_args__ = (
        ForeignKeyConstraint(['account_type_id'], ['account_types.account_type_id'], name='user_accounts_account_type_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='user_accounts_user_id_fkey'),
        PrimaryKeyConstraint('account_id', name='user_accounts_pkey')
    )

    account_id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dinero_total_cuenta: Mapped[decimal.Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default=text('0'))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    account_description: Mapped[Optional[str]] = mapped_column(Text)

    account_type: Mapped['AccountTypes'] = relationship('AccountTypes', back_populates='user_accounts')
    user: Mapped['Users'] = relationship('Users', back_populates='user_accounts')
    user_financial_transactions: Mapped[list['UserFinancialTransactions']] = relationship('UserFinancialTransactions', back_populates='account')


class UserCategories(Base):
    __tablename__ = 'user_categories'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='user_categories_user_id_fkey'),
        PrimaryKeyConstraint('category_id', name='user_categories_pkey')
    )

    category_id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    category_description: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped['Users'] = relationship('Users', back_populates='user_categories')
    user_financial_transactions: Mapped[list['UserFinancialTransactions']] = relationship('UserFinancialTransactions', back_populates='category')


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
    total_segundos_retrieval_correos: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 2))

    user: Mapped['Users'] = relationship('Users', back_populates='user_email_processing_logs')
    user_financial_transactions: Mapped[list['UserFinancialTransactions']] = relationship('UserFinancialTransactions', back_populates='user_email_processing_log')
    user_google_connections: Mapped[list['UserGoogleConnections']] = relationship('UserGoogleConnections', back_populates='last_email_history_checkup')


class UserPasswords(Base):
    __tablename__ = 'user_passwords'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='fk_user_passwords_user'),
        PrimaryKeyConstraint('id', name='user_passwords_pkey'),
        UniqueConstraint('user_id', name='user_passwords_user_id_key')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    hash_password: Mapped[str] = mapped_column(Text, nullable=False)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    user: Mapped['Users'] = relationship('Users', back_populates='user_passwords')


class UserResetPassword(Base):
    __tablename__ = 'user_reset_password'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', onupdate='CASCADE', name='user_reset_password_user_id_fkey'),
        PrimaryKeyConstraint('id', name='user_reset_password_pkey'),
        Index('idx_user_reset_password_active_code', 'user_id', 'verify_code', 'code_used', 'valid_expiration_date'),
        Index('idx_user_reset_password_user_id', 'user_id'),
        Index('idx_user_reset_password_verify_code', 'verify_code')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    valid_expiration_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    verify_code: Mapped[str] = mapped_column(String(20), nullable=False)
    code_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    update_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    user: Mapped['Users'] = relationship('Users', back_populates='user_reset_password')


class UserFinancialTransactions(Base):
    __tablename__ = 'user_financial_transactions'
    __table_args__ = (
        CheckConstraint("tipo_transaccion::text = ANY (ARRAY['income'::character varying::text, 'expense'::character varying::text])", name='chk_user_financial_transactions_tipo'),
        ForeignKeyConstraint(['account_id'], ['user_accounts.account_id'], ondelete='SET NULL', name='fk_user_financial_transactions_account'),
        ForeignKeyConstraint(['category_id'], ['user_categories.category_id'], ondelete='SET NULL', name='fk_user_financial_transactions_category'),
        ForeignKeyConstraint(['user_email_processing_log_id'], ['user_email_processing_logs.id'], ondelete='CASCADE', name='fk_user_financial_transactions_email_processing_log'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='fk_user_financial_transactions_user'),
        PrimaryKeyConstraint('id', name='user_financial_transactions_pkey')
    )

    id: Mapped[int] = mapped_column(Integer, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_email_processing_log_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_transaccion: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    monto_reconocido: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    tipo_transaccion: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    account_id: Mapped[Optional[int]] = mapped_column(Integer)
    category_id: Mapped[Optional[int]] = mapped_column(Integer)
    monto: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 2))
    descripcion_transaccion: Mapped[Optional[str]] = mapped_column(Text)

    account: Mapped[Optional['UserAccounts']] = relationship('UserAccounts', back_populates='user_financial_transactions')
    category: Mapped[Optional['UserCategories']] = relationship('UserCategories', back_populates='user_financial_transactions')
    user_email_processing_log: Mapped['UserEmailProcessingLogs'] = relationship('UserEmailProcessingLogs', back_populates='user_financial_transactions')
    user: Mapped['Users'] = relationship('Users', back_populates='user_financial_transactions')


class UserGoogleConnections(Base):
    __tablename__ = 'user_google_connections'
    __table_args__ = (
        ForeignKeyConstraint(['last_email_history_checkup_id'], ['user_email_processing_logs.id'], ondelete='SET NULL', name='fk_user_google_connections_last_email_history_checkup'),
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
    last_email_history_checkup_id: Mapped[Optional[int]] = mapped_column(Integer)

    last_email_history_checkup: Mapped[Optional['UserEmailProcessingLogs']] = relationship('UserEmailProcessingLogs', back_populates='user_google_connections')
    user: Mapped['Users'] = relationship('Users', back_populates='user_google_connections')
