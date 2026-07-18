import secrets
from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config import settings
from src.exceptions import AppError
from src.models import (
    ActiveSeatReservation,
    MovieFunction,
    Reservation,
    ReservationSeat,
    ReservationStatusHistory,
    Seat,
    Ticket,
)
from src.services.movie_function_service import FunctionNotFoundError


class ReservationError(AppError):
    """Error de negocio base para la creación de reservas."""


class FunctionAlreadyStartedError(ReservationError):
    pass


class InvalidSeatsError(ReservationError):
    """seat_ids vacío, duplicado, o con asientos que no pertenecen a la sala."""


class CapacityExceededError(ReservationError):
    pass


class SeatConflictError(ReservationError):
    """Uno o más asientos ya están ocupados para esta función (UNIQUE violado)."""
    status_code = status.HTTP_409_CONFLICT


class ReservationNotFoundError(ReservationError):
    status_code = status.HTTP_404_NOT_FOUND


class InvalidTransitionError(ReservationError):
    """La transición de estado solicitada no es válida para el estado actual."""
    status_code = status.HTTP_409_CONFLICT


_MANUAL_TRANSITIONS: dict[tuple[str, str], str | None] = {
    ("Reservada", "Confirmada"): None,
    ("Reservada", "Cancelada"): "function_not_started",
    ("Confirmada", "Utilizada"): None,
    ("Confirmada", "Cancelada"): "function_not_started",
}


class ReservationService:
    @staticmethod
    def create_reservation(
        db: Session,
        *,
        function_id: int,
        seat_ids: list[int],
        customer_name: str,
        customer_phone: str | None,
        customer_email: str | None,
        created_by: int,
    ) -> tuple[Reservation, list[int]]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        unique_seat_ids = list(dict.fromkeys(seat_ids))
        if len(unique_seat_ids) != len(seat_ids):
            raise InvalidSeatsError("seat_ids no puede contener asientos repetidos")

        function = (
            db.query(MovieFunction)
            .filter(MovieFunction.function_id == function_id)
            .first()
        )
        if function is None:
            raise FunctionNotFoundError(f"Función {function_id} no existe")
        if function.start_datetime <= now:
            raise FunctionAlreadyStartedError("La función ya inició o ya pasó")

        room_seat_ids = {
            seat_id
            for (seat_id,) in db.query(Seat.seat_id).filter(Seat.room_id == function.room_id)
        }
        if not set(unique_seat_ids).issubset(room_seat_ids):
            raise InvalidSeatsError("Uno o más asientos no pertenecen a la sala de la función")

        total_seats = len(room_seat_ids)
        active_count = (
            db.query(func.count(ActiveSeatReservation.active_seat_reservation_id))
            .filter(ActiveSeatReservation.function_id == function_id)
            .scalar()
        )
        if active_count + len(unique_seat_ids) > total_seats:
            raise CapacityExceededError("La reserva excede el aforo de la sala")

        reservation = Reservation(
            function_id=function_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            status="Reservada",
            expires_at=now + timedelta(minutes=settings.reservation_hold_minutes),
            created_by=created_by,
        )
        db.add(reservation)

        try:
            db.flush()  # asigna reservation_id sin cerrar la transacción

            for seat_id in unique_seat_ids:
                db.add(ReservationSeat(
                    reservation_id=reservation.reservation_id,
                    seat_id=seat_id,
                    function_id=function_id,
                ))
                db.add(ActiveSeatReservation(
                    function_id=function_id,
                    seat_id=seat_id,
                    reservation_id=reservation.reservation_id,
                ))

            db.commit()
        except IntegrityError:
            db.rollback()
            raise SeatConflictError(
                "Uno o más asientos ya fueron reservados para esta función"
            )

        db.refresh(reservation)
        return reservation, unique_seat_ids

    @staticmethod
    def change_status(
        db: Session,
        *,
        reservation_id: int,
        new_status: str,
        changed_by: int,
    ) -> tuple[Reservation, list[int]]:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.reservation_id == reservation_id)
            .first()
        )
        if reservation is None:
            raise ReservationNotFoundError(f"Reserva {reservation_id} no existe")

        ReservationService.expire_if_needed(db, reservation, changed_by=changed_by)

        transition = (reservation.status, new_status)
        if transition not in _MANUAL_TRANSITIONS:
            raise InvalidTransitionError(
                f"No se puede pasar de '{reservation.status}' a '{new_status}'"
            )

        condition = _MANUAL_TRANSITIONS[transition]
        if condition == "function_not_started":
            function = (
                db.query(MovieFunction)
                .filter(MovieFunction.function_id == reservation.function_id)
                .first()
            )
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if function.start_datetime <= now:
                raise FunctionAlreadyStartedError(
                    "La función ya inició; no se puede cambiar el estado"
                )

        from_status = reservation.status
        reservation.status = new_status
        db.add(ReservationStatusHistory(
            reservation_id=reservation.reservation_id,
            from_status=from_status,
            to_status=new_status,
            changed_by=changed_by,
        ))

        if new_status == "Confirmada":
            reservation_seats = (
                db.query(ReservationSeat)
                .filter(ReservationSeat.reservation_id == reservation.reservation_id)
                .all()
            )
            for reservation_seat in reservation_seats:
                ticket_code = (
                    f"TCK-{reservation.reservation_id}-{reservation_seat.seat_id}-"
                    f"{secrets.token_hex(2).upper()}"
                )
                db.add(Ticket(
                    reservation_seat_id=reservation_seat.reservation_seat_id,
                    ticket_code=ticket_code,
                ))

        if new_status in ("Cancelada", "Expirada"):
            db.query(ActiveSeatReservation).filter(
                ActiveSeatReservation.reservation_id == reservation.reservation_id
            ).delete(synchronize_session=False)

        db.commit()
        db.refresh(reservation)

        seat_ids = [
            seat_id
            for (seat_id,) in db.query(ReservationSeat.seat_id).filter(
                ReservationSeat.reservation_id == reservation.reservation_id
            )
        ]
        return reservation, seat_ids

    @staticmethod
    def get_reservation(
        db: Session, *, reservation_id: int, changed_by: int
    ) -> tuple[Reservation, list[int]]:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.reservation_id == reservation_id)
            .first()
        )
        if reservation is None:
            raise ReservationNotFoundError(f"Reserva {reservation_id} no existe")

        ReservationService.expire_if_needed(db, reservation, changed_by=changed_by)

        seat_ids = [
            seat_id
            for (seat_id,) in db.query(ReservationSeat.seat_id).filter(
                ReservationSeat.reservation_id == reservation.reservation_id
            )
        ]
        return reservation, seat_ids

    @staticmethod
    def get_reservation_tickets(db: Session, *, reservation_id: int) -> list[dict]:
        reservation = (
            db.query(Reservation)
            .filter(Reservation.reservation_id == reservation_id)
            .first()
        )
        if reservation is None:
            raise ReservationNotFoundError(f"Reserva {reservation_id} no existe")

        rows = (
            db.query(Ticket, Seat)
            .join(ReservationSeat, ReservationSeat.reservation_seat_id == Ticket.reservation_seat_id)
            .join(Seat, Seat.seat_id == ReservationSeat.seat_id)
            .filter(ReservationSeat.reservation_id == reservation_id)
            .order_by(Seat.row_label, Seat.seat_number)
            .all()
        )

        return [
            {
                "ticket_id": ticket.ticket_id,
                "ticket_code": ticket.ticket_code,
                "ticket_type": ticket.ticket_type,
                "issued_at": ticket.issued_at,
                "seat_id": seat.seat_id,
                "row_label": seat.row_label,
                "seat_number": seat.seat_number,
                "seat_label": f"{seat.row_label}{seat.seat_number}",
            }
            for ticket, seat in rows
        ]

    @staticmethod
    def list_reservations(
        db: Session,
        *,
        function_id: int | None = None,
        status_filter: str | None = None,
        changed_by: int,
    ) -> list[tuple[Reservation, list[int]]]:
        query = db.query(Reservation)
        if function_id is not None:
            query = query.filter(Reservation.function_id == function_id)

        reservations = query.order_by(Reservation.created_at.desc()).all()

        for reservation in reservations:
            ReservationService.expire_if_needed(db, reservation, changed_by=changed_by)

        if status_filter is not None:
            reservations = [r for r in reservations if r.status == status_filter]

        results = []
        for reservation in reservations:
            seat_ids = [
                seat_id
                for (seat_id,) in db.query(ReservationSeat.seat_id).filter(
                    ReservationSeat.reservation_id == reservation.reservation_id
                )
            ]
            results.append((reservation, seat_ids))
        return results

    @staticmethod
    def expire_if_needed(
        db: Session,
        reservation: Reservation,
        *,
        changed_by: int,
    ) -> Reservation:
        if reservation.status != "Reservada" or reservation.expires_at is None:
            return reservation

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if reservation.expires_at > now:
            return reservation

        # Excepción consciente al patrón de "una sola transacción" de
        # diseño-db.md sección 2.4: esta función hace su propio commit()
        # porque expirar una reserva vencida es un hecho consumado en sí
        # mismo, independiente de si la operación que la descubrió (un
        # PATCH, un reporte, etc.) termina con éxito o falla después.
        db.add(ReservationStatusHistory(
            reservation_id=reservation.reservation_id,
            from_status=reservation.status,
            to_status="Expirada",
            changed_by=changed_by,
        ))
        db.query(ActiveSeatReservation).filter(
            ActiveSeatReservation.reservation_id == reservation.reservation_id
        ).delete(synchronize_session=False)
        reservation.status = "Expirada"

        db.commit()
        db.refresh(reservation)
        return reservation
