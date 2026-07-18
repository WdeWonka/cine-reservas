from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, SmallInteger, DateTime,
    ForeignKey, UniqueConstraint, CheckConstraint, Boolean,
)
from sqlalchemy.orm import relationship

from src.db.session import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Movie(Base):
    __tablename__ = "Movie"

    movie_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    # Valor semilla al crear una función; MovieFunction.end_datetime no se
    # recalcula si este valor cambia después (ver docs/modelo-bd.md).
    duration_min = Column(SmallInteger, nullable=False)
    age_rating = Column(String(10), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class Room(Base):
    __tablename__ = "Room"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class Seat(Base):
    __tablename__ = "Seat"
    __table_args__ = (
        UniqueConstraint("room_id", "row_label", "seat_number", name="ux_seat_room_row_number"),
    )

    seat_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("Room.room_id"), nullable=False)
    row_label = Column(String(1), nullable=False)
    seat_number = Column(SmallInteger, nullable=False)


class MovieFunction(Base):
    __tablename__ = "MovieFunction"

    function_id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("Movie.movie_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("Room.room_id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    # Fotografía histórica: start_datetime + Movie.duration_min al crear la
    # función. No se recalcula si la duración de la película cambia después.
    end_datetime = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    # El no-solapamiento de funciones en la misma sala se valida en la capa
    # de servicio (SQL Server no tiene exclusion constraints nativos).


class Reservation(Base):
    __tablename__ = "Reservation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Reservada','Confirmada','Utilizada','Cancelada','Expirada')",
            name="ck_reservation_status",
        ),
    )

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(Integer, ForeignKey("MovieFunction.function_id"), nullable=False, index=True)
    customer_name = Column(String(150), nullable=False)
    customer_phone = Column(String(30), nullable=True)
    customer_email = Column(String(150), nullable=True)
    status = Column(String(20), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("User.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)


class ReservationSeat(Base):
    """Historial permanente: qué asientos pertenecieron a esta reserva.
    Nunca se modifica ni se elimina al cambiar el estado de la reserva.
    No garantiza unicidad de ocupación activa (ver ActiveSeatReservation)."""

    __tablename__ = "ReservationSeat"
    __table_args__ = (
        UniqueConstraint("reservation_id", "seat_id", name="ux_reservation_seat"),
    )

    reservation_seat_id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey("Reservation.reservation_id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("Seat.seat_id"), nullable=False)
    # Denormalizado desde Reservation.function_id, solo para trazabilidad
    # histórica; no participa en ninguna restricción de unicidad activa.
    function_id = Column(Integer, ForeignKey("MovieFunction.function_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class ActiveSeatReservation(Base):
    """Ocupación VIGENTE de un asiento para una función. Se inserta al crear
    la reserva y se elimina al cancelarse o expirar. El UNIQUE(function_id,
    seat_id) es la garantía real de RNF-01 a nivel de motor de base de datos."""

    __tablename__ = "ActiveSeatReservation"
    __table_args__ = (
        UniqueConstraint("function_id", "seat_id", name="ux_active_seat_reservation"),
    )

    active_seat_reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(Integer, ForeignKey("MovieFunction.function_id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("Seat.seat_id"), nullable=False)
    reservation_id = Column(Integer, ForeignKey("Reservation.reservation_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class User(Base):
    __tablename__ = "User"
    __table_args__ = (
        CheckConstraint("role IN ('admin','taquillero')", name="ck_user_role"),
    )

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)  # hash bcrypt, nunca texto plano
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)


class ReservationStatusHistory(Base):
    __tablename__ = "ReservationStatusHistory"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey("Reservation.reservation_id"), nullable=False)
    from_status = Column(String(20), nullable=True)  # NULL en el primer registro
    to_status = Column(String(20), nullable=False)
    changed_by = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=utcnow)


class Ticket(Base):
    """Comprobante digital por asiento confirmado. Referencia ReservationSeat
    (histórico), no ActiveSeatReservation (vigente): el ticket debe seguir
    existiendo aunque la reserva cambie de estado más adelante. No tiene
    ciclo de vida propio (regla 5.2.6 del análisis)."""

    __tablename__ = "Ticket"

    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_seat_id = Column(
        Integer, ForeignKey("ReservationSeat.reservation_seat_id"), nullable=False, unique=True
    )
    ticket_type = Column(String(20), nullable=False, default="Adulto")
    ticket_code = Column(String(20), nullable=False, unique=True)
    issued_at = Column(DateTime, nullable=False, default=utcnow)
