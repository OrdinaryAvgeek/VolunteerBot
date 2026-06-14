# models.py
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


class Role(str, enum.Enum):
    VOLUNTEER = "volunteer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ParticipationStatus(str, enum.Enum):
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class Volunteer(Base):
    __tablename__ = "volunteers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[Role] = mapped_column(SQLEnum(Role), default=Role.VOLUNTEER)
    preferences: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_active: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    participations: Mapped[list["Participation"]] = relationship(back_populates="volunteer")

    def __repr__(self):
        return f"<Volunteer {self.telegram_id}: {self.full_name}>"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    location_coords: Mapped[str] = mapped_column(String(100), nullable=True)
    sphere: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[EventStatus] = mapped_column(SQLEnum(EventStatus), default=EventStatus.PUBLISHED)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("volunteers.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, onupdate=datetime.now)

    organizer: Mapped["Volunteer"] = relationship(foreign_keys=[organizer_id])
    participations: Mapped[list["Participation"]] = relationship(back_populates="event")

    def __repr__(self):
        return f"<Event {self.id}: {self.title}>"


class Participation(Base):
    __tablename__ = "participation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    volunteer_id: Mapped[int] = mapped_column(ForeignKey("volunteers.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    status: Mapped[ParticipationStatus] = mapped_column(SQLEnum(ParticipationStatus), default=ParticipationStatus.REGISTERED)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    checked_out_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    volunteer: Mapped["Volunteer"] = relationship(back_populates="participations")
    event: Mapped["Event"] = relationship(back_populates="participations")

    def __repr__(self):
        return f"<Participation v{self.volunteer_id} e{self.event_id}: {self.status.value}>"