from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey,
                        Index, Integer, JSON, Numeric, String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


def now():
    return datetime.now(timezone.utc)


MONEY = Numeric(14, 2)
TS = DateTime(timezone=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(TS, default=now)
    updated_at: Mapped[datetime] = mapped_column(TS, default=now, onupdate=now)


class User(Base, TimestampMixin):
    """Dashboard login. role: super_admin | reseller"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reseller_id: Mapped[int | None] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)


class ResellerAccount(Base, TimestampMixin):
    __tablename__ = "reseller_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|suspended


class TelegramBot(Base, TimestampMixin):
    """reseller_id NULL = the owner's primary bot."""
    __tablename__ = "telegram_bots"
    id: Mapped[int] = mapped_column(primary_key=True)
    reseller_id: Mapped[int | None] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    telegram_bot_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(64))
    token_encrypted: Mapped[str] = mapped_column(Text)
    webhook_secret: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="inactive")  # active|suspended|inactive
    last_webhook_error: Mapped[str | None] = mapped_column(Text)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("bot_id", "telegram_user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("telegram_bots.id"), index=True)
    reseller_id: Mapped[int | None] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger)
    display_name: Mapped[str | None] = mapped_column(String(255))


class CourseCategory(Base):
    __tablename__ = "course_categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("course_categories.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    thumbnail_file_id: Mapped[str | None] = mapped_column(String(255))
    regular_price: Mapped[Decimal] = mapped_column(MONEY)
    sale_price: Mapped[Decimal | None] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|published|archived
    delivery_method: Mapped[str] = mapped_column(String(30), default="manual")
    delivery_ref_encrypted: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (CheckConstraint("regular_price >= 0"),)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("telegram_bots.id"), index=True)
    reseller_id: Mapped[int | None] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="created", index=True)
    total: Mapped[Decimal] = mapped_column(MONEY)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    """unit_price is a snapshot: later price changes never alter it."""
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    unit_price: Mapped[Decimal] = mapped_column(MONEY)
    order: Mapped[Order] = relationship(back_populates="items")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("provider", "provider_ref"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_ref: Mapped[str | None] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    verified_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class PaymentVerificationEvent(Base):
    __tablename__ = "payment_verification_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class CourseFulfillment(Base, TimestampMixin):
    __tablename__ = "course_fulfillments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    revoked_at: Mapped[datetime | None] = mapped_column(TS)


class ResellerCreditLimit(Base):
    """Append-only history; latest row is the active limit."""
    __tablename__ = "reseller_credit_limits"
    id: Mapped[int] = mapped_column(primary_key=True)
    reseller_id: Mapped[int] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    limit_amount: Mapped[Decimal] = mapped_column(MONEY)
    set_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class FinancialLedgerEntry(Base):
    """IMMUTABLE. Corrections = new reversing entries. (DB trigger added in Phase 6.)
    entry_type: sale_accrual|reseller_payment|refund_reversal|adjustment"""
    __tablename__ = "financial_ledger_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    reseller_id: Mapped[int] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    entry_type: Mapped[str] = mapped_column(String(30))
    gross_amount: Mapped[Decimal] = mapped_column(MONEY, default=0)
    owner_share_delta: Mapped[Decimal] = mapped_column(MONEY, default=0)  # + increases owed
    reseller_share_delta: Mapped[Decimal] = mapped_column(MONEY, default=0)
    idempotency_key: Mapped[str] = mapped_column(String(160), unique=True)
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class ResellerPaymentRecord(Base):
    __tablename__ = "reseller_payment_records"
    __table_args__ = (UniqueConstraint("reseller_id", "method", "reference"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    reseller_id: Mapped[int] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(MONEY)
    paid_on: Mapped[datetime] = mapped_column(TS)
    method: Mapped[str] = mapped_column(String(40))
    reference: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class CreditReservation(Base, TimestampMixin):
    __tablename__ = "credit_reservations"
    id: Mapped[int] = mapped_column(primary_key=True)
    reseller_id: Mapped[int] = mapped_column(ForeignKey("reseller_accounts.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount: Mapped[Decimal] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(20), default="held")  # held|consumed|released


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(MONEY)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reason: Mapped[str | None] = mapped_column(Text)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("source", "external_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(40))  # telegram:<bot_id> | provider name
    external_id: Mapped[str] = mapped_column(String(120))  # e.g. Telegram update_id
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime | None] = mapped_column(TS)
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), index=True)
    target: Mapped[str | None] = mapped_column(String(120))
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(TS, default=now)


class ApplicationSetting(Base):
    __tablename__ = "application_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
