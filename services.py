# services.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from models import (
    Volunteer, UserStatus, Role,
    Event, EventStatus,
    Participation, ParticipationStatus
)


class VolunteerService:
    """Сервис для работы с волонтёрами"""

    @staticmethod
    async def register(
            session: AsyncSession,
            telegram_id: int,
            full_name: str,
            phone: str,
            preferences: list
    ) -> Volunteer:
        """Создаёт нового волонтёра со статусом PENDING"""
        result = await session.execute(
            select(Volunteer).where(Volunteer.telegram_id == telegram_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        volunteer = Volunteer(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            preferences=preferences,
            status=UserStatus.PENDING,
            role=Role.VOLUNTEER
        )
        session.add(volunteer)
        await session.commit()
        await session.refresh(volunteer)
        return volunteer

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Volunteer | None:
        """Получает волонтёра по Telegram ID"""
        result = await session.execute(
            select(Volunteer).where(Volunteer.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, volunteer_id: int) -> Volunteer | None:
        """Получает волонтёра по ID"""
        result = await session.execute(
            select(Volunteer).where(Volunteer.id == volunteer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_role(session: AsyncSession, telegram_id: int, role: Role) -> Volunteer | None:
        """Обновляет роль пользователя"""
        volunteer = await VolunteerService.get_by_telegram_id(session, telegram_id)
        if volunteer:
            volunteer.role = role
            await session.commit()
            return volunteer
        return None

    @staticmethod
    async def approve(session: AsyncSession, telegram_id: int) -> Volunteer | None:
        """Подтверждает регистрацию волонтёра"""
        volunteer = await VolunteerService.get_by_telegram_id(session, telegram_id)
        if volunteer and volunteer.status == UserStatus.PENDING:
            volunteer.status = UserStatus.ACTIVE
            await session.commit()
            return volunteer
        return None

    @staticmethod
    async def is_organizer(session: AsyncSession, telegram_id: int) -> bool:
        """Проверяет, является ли пользователь организатором"""
        volunteer = await VolunteerService.get_by_telegram_id(session, telegram_id)
        return volunteer is not None and volunteer.role in [Role.ORGANIZER, Role.ADMIN]


class EventService:
    """Сервис для работы с мероприятиями"""

    @staticmethod
    async def create_event(
            session: AsyncSession,
            title: str,
            description: str,
            date_time: datetime,
            location: str,
            sphere: str,
            organizer_id: int
    ) -> Event:
        """Создаёт новое мероприятие со статусом PUBLISHED"""
        event = Event(
            title=title,
            description=description,
            date_time=date_time,
            location=location,
            sphere=sphere,
            organizer_id=organizer_id,
            status=EventStatus.PUBLISHED
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @staticmethod
    async def get_published_events(session: AsyncSession) -> list[Event]:
        """Получает все опубликованные мероприятия"""
        result = await session.execute(
            select(Event).where(Event.status == EventStatus.PUBLISHED)
            .order_by(Event.date_time)
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, event_id: int) -> Event | None:
        """Получает мероприятие по ID"""
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_organizer(session: AsyncSession, organizer_id: int) -> list[Event]:
        """Получает мероприятия, созданные организатором"""
        result = await session.execute(
            select(Event).where(Event.organizer_id == organizer_id)
        )
        return result.scalars().all()

    @staticmethod
    async def cancel_event(session: AsyncSession, event_id: int) -> Event | None:
        """Отменяет мероприятие"""
        event = await EventService.get_by_id(session, event_id)
        if event and event.status == EventStatus.PUBLISHED:
            event.status = EventStatus.CANCELLED
            await session.commit()
            return event
        return None

    @staticmethod
    async def get_upcoming_events(session: AsyncSession, hours: int = 24) -> list[Event]:
        """Получает мероприятия, которые начнутся в ближайшие N часов"""
        now = datetime.now()
        soon = now + timedelta(hours=hours)
        result = await session.execute(
            select(Event).where(
                and_(
                    Event.status == EventStatus.PUBLISHED,
                    Event.date_time.between(now, soon)
                )
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_participants(session: AsyncSession, event_id: int) -> list[Volunteer]:
        """Получает всех участников мероприятия"""
        result = await session.execute(
            select(Volunteer)
            .join(Participation)
            .where(Participation.event_id == event_id)
        )
        return result.scalars().all()


class ParticipationService:
    """Сервис для работы с записями на мероприятия"""

    @staticmethod
    async def register(
            session: AsyncSession,
            volunteer_id: int,
            event_id: int
    ) -> Participation | None:
        """Записывает волонтёра на мероприятие"""
        result = await session.execute(
            select(Participation).where(
                and_(
                    Participation.volunteer_id == volunteer_id,
                    Participation.event_id == event_id
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return None

        participation = Participation(
            volunteer_id=volunteer_id,
            event_id=event_id,
            status=ParticipationStatus.REGISTERED
        )
        session.add(participation)
        await session.commit()
        await session.refresh(participation)
        return participation

    @staticmethod
    async def get_by_volunteer(session: AsyncSession, volunteer_id: int) -> list[Participation]:
        """Получает все записи волонтёра"""
        result = await session.execute(
            select(Participation).where(
                Participation.volunteer_id == volunteer_id
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_by_event(session: AsyncSession, event_id: int) -> list[Participation]:
        """Получает все записи на мероприятие"""
        result = await session.execute(
            select(Participation).where(
                Participation.event_id == event_id
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_active_participation(session: AsyncSession, volunteer_id: int, event_id: int) -> Participation | None:
        """Получает активную записи волонтёра на мероприятие"""
        result = await session.execute(
            select(Participation).where(
                and_(
                    Participation.volunteer_id == volunteer_id,
                    Participation.event_id == event_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_events(session: AsyncSession, volunteer_id: int) -> list[Event]:
        """Получает все мероприятия, на которые записан волонтёр"""
        result = await session.execute(
            select(Event)
            .join(Participation)
            .where(Participation.volunteer_id == volunteer_id)
            .order_by(Event.date_time)
        )
        return result.scalars().all()

    @staticmethod
    async def cancel_registration(
            session: AsyncSession,
            volunteer_id: int,
            event_id: int
    ) -> bool:
        """Отменяет запись волонтёра на мероприятие"""
        result = await session.execute(
            select(Participation).where(
                and_(
                    Participation.volunteer_id == volunteer_id,
                    Participation.event_id == event_id
                )
            )
        )
        participation = result.scalar_one_or_none()

        if participation:
            await session.delete(participation)
            await session.commit()
            return True
        return False

    @staticmethod
    async def check_in(
            session: AsyncSession,
            volunteer_id: int,
            event_id: int
    ) -> Participation | None:
        """Отмечает прибытие волонтёра на мероприятие"""
        result = await session.execute(
            select(Participation).where(
                and_(
                    Participation.volunteer_id == volunteer_id,
                    Participation.event_id == event_id
                )
            )
        )
        participation = result.scalar_one_or_none()

        if participation and participation.status == ParticipationStatus.REGISTERED:
            participation.status = ParticipationStatus.ATTENDED
            participation.checked_in_at = datetime.now()
            await session.commit()
            return participation
        return None

    @staticmethod
    async def check_out(
            session: AsyncSession,
            volunteer_id: int,
            event_id: int
    ) -> Participation | None:
        """Отмечает уход волонтёра с мероприятия"""
        result = await session.execute(
            select(Participation).where(
                and_(
                    Participation.volunteer_id == volunteer_id,
                    Participation.event_id == event_id
                )
            )
        )
        participation = result.scalar_one_or_none()

        if participation and participation.status == ParticipationStatus.ATTENDED:
            participation.checked_out_at = datetime.now()
            await session.commit()
            return participation
        return None

    @staticmethod
    async def get_event_report(session: AsyncSession, event_id: int) -> list[dict]:
        """Получает данные для отчёта по мероприятию"""
        from models import Volunteer, Participation

        result = await session.execute(
            select(Volunteer, Participation)
            .join(Participation, Volunteer.id == Participation.volunteer_id)
            .where(Participation.event_id == event_id)
        )
        rows = result.all()

        report = []
        for volunteer, participation in rows:
            report.append({
                "full_name": volunteer.full_name,
                "phone": volunteer.phone or "—",
                "status": participation.status.value,
                "registered_at": participation.registered_at.strftime("%d.%m.%Y %H:%M"),
                "checked_in_at": participation.checked_in_at.strftime(
                    "%d.%m.%Y %H:%M") if participation.checked_in_at else "—",
                "checked_out_at": participation.checked_out_at.strftime(
                    "%d.%m.%Y %H:%M") if participation.checked_out_at else "—",
            })
        return report