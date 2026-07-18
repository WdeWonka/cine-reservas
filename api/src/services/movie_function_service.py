from datetime import date, datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.exceptions import AppError
from src.models import (
    ActiveSeatReservation,
    Movie,
    MovieFunction,
    Reservation,
    ReservationSeat,
    Room,
    Seat,
)
from src.services.movie_service import MovieNotFoundError
from src.services.room_service import RoomNotFoundError


class MovieFunctionError(AppError):
    """Error de negocio base para la gestión de funciones."""


class FunctionOverlapError(MovieFunctionError):
    """La función se solapa con otra existente en la misma sala."""
    status_code = status.HTTP_409_CONFLICT


class FunctionNotFoundError(MovieFunctionError):
    status_code = status.HTTP_404_NOT_FOUND


class FunctionHasActiveReservationsError(MovieFunctionError):
    status_code = status.HTTP_409_CONFLICT


class MovieFunctionService:
    @staticmethod
    def create_function(
        db: Session,
        *,
        movie_id: int,
        room_id: int,
        start_datetime: datetime,
    ) -> MovieFunction:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if movie is None:
            raise MovieNotFoundError(f"Película {movie_id} no existe")

        room = db.query(Room).filter(Room.room_id == room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Sala {room_id} no existe")

        end_datetime = start_datetime + timedelta(minutes=movie.duration_min)

        MovieFunctionService._check_overlap(
            db, room_id=room_id, start_datetime=start_datetime, end_datetime=end_datetime
        )

        function = MovieFunction(
            movie_id=movie_id,
            room_id=room_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        db.add(function)
        db.commit()
        db.refresh(function)
        return function

    @staticmethod
    def _check_overlap(
        db: Session,
        *,
        room_id: int,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_function_id: int | None = None,
    ) -> None:
        query = db.query(MovieFunction).filter(
            MovieFunction.room_id == room_id,
            MovieFunction.is_active == True,  # noqa: E712 — MSSQL no soporta "IS 1"
            MovieFunction.start_datetime < end_datetime,
            MovieFunction.end_datetime > start_datetime,
        )
        if exclude_function_id is not None:
            query = query.filter(MovieFunction.function_id != exclude_function_id)

        if query.first() is not None:
            raise FunctionOverlapError(
                "La función se solapa con otra existente en la misma sala"
            )

    @staticmethod
    def count_seats(db: Session, room_id: int) -> int:
        return (
            db.query(func.count(Seat.seat_id))
            .filter(Seat.room_id == room_id)
            .scalar()
        )

    @staticmethod
    def count_occupied(db: Session, function_id: int) -> int:
        return (
            db.query(func.count(ActiveSeatReservation.active_seat_reservation_id))
            .filter(ActiveSeatReservation.function_id == function_id)
            .scalar()
        )

    @staticmethod
    def list_functions_with_availability(
        db: Session, *, include_inactive: bool = False, target_date: date | None = None
    ) -> list[dict]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        seats_subq = (
            db.query(Seat.room_id, func.count(Seat.seat_id).label("total_seats"))
            .group_by(Seat.room_id)
            .subquery()
        )
        occupied_subq = (
            db.query(
                ActiveSeatReservation.function_id,
                func.count(ActiveSeatReservation.active_seat_reservation_id).label("occupied"),
            )
            .join(Reservation, Reservation.reservation_id == ActiveSeatReservation.reservation_id)
            .filter(
                or_(
                    Reservation.status != "Reservada",
                    Reservation.expires_at.is_(None),
                    Reservation.expires_at > now,
                )
            )
            .group_by(ActiveSeatReservation.function_id)
            .subquery()
        )

        query = (
            db.query(
                MovieFunction,
                func.coalesce(seats_subq.c.total_seats, 0).label("total_seats"),
                func.coalesce(occupied_subq.c.occupied, 0).label("occupied"),
            )
            .outerjoin(seats_subq, seats_subq.c.room_id == MovieFunction.room_id)
            .outerjoin(occupied_subq, occupied_subq.c.function_id == MovieFunction.function_id)
        )

        if not include_inactive:
            query = query.filter(MovieFunction.is_active == True)  # noqa: E712 — MSSQL no soporta "IS 1"

        if target_date is not None:
            range_start = datetime.combine(target_date, datetime.min.time())
            range_end = range_start + timedelta(days=1)
            query = query.filter(
                MovieFunction.start_datetime >= range_start,
                MovieFunction.start_datetime < range_end,
            )

        rows = query.order_by(MovieFunction.start_datetime).all()

        return [
            {
                "function_id": function.function_id,
                "movie_id": function.movie_id,
                "room_id": function.room_id,
                "start_datetime": function.start_datetime,
                "end_datetime": function.end_datetime,
                "asientos_totales": total_seats,
                "asientos_ocupados": occupied,
                "asientos_disponibles": total_seats - occupied,
                "is_active": function.is_active,
            }
            for function, total_seats, occupied in rows
        ]

    @staticmethod
    def disable_function(db: Session, *, function_id: int) -> MovieFunction:
        function = (
            db.query(MovieFunction)
            .filter(MovieFunction.function_id == function_id)
            .first()
        )
        if function is None:
            raise FunctionNotFoundError(f"Función {function_id} no existe")

        has_active_reservations = (
            db.query(Reservation)
            .filter(
                Reservation.function_id == function_id,
                Reservation.status.in_(("Reservada", "Confirmada")),
            )
            .first()
        )
        if has_active_reservations is not None:
            raise FunctionHasActiveReservationsError(
                "No se puede deshabilitar la función: tiene reservas activas "
                "(cancelalas individualmente primero)"
            )

        function.is_active = False
        db.commit()
        db.refresh(function)
        return function

    @staticmethod
    def enable_function(db: Session, *, function_id: int) -> MovieFunction:
        function = (
            db.query(MovieFunction)
            .filter(MovieFunction.function_id == function_id)
            .first()
        )
        if function is None:
            raise FunctionNotFoundError(f"Función {function_id} no existe")

        MovieFunctionService._check_overlap(
            db,
            room_id=function.room_id,
            start_datetime=function.start_datetime,
            end_datetime=function.end_datetime,
            exclude_function_id=function.function_id,
        )

        function.is_active = True
        db.commit()
        db.refresh(function)
        return function

    @staticmethod
    def get_function_report(db: Session, *, function_id: int, changed_by: int) -> dict:
        # Import local (no a nivel de módulo) para evitar ciclo: este módulo
        # es importado por reservation_service.py (para FunctionNotFoundError),
        # así que no puede importar ReservationService de vuelta arriba del todo.
        from src.services.reservation_service import ReservationService

        function = (
            db.query(MovieFunction)
            .filter(MovieFunction.function_id == function_id)
            .first()
        )
        if function is None:
            raise FunctionNotFoundError(f"Función {function_id} no existe")

        movie = db.query(Movie).filter(Movie.movie_id == function.movie_id).first()
        room = db.query(Room).filter(Room.room_id == function.room_id).first()

        reservations = (
            db.query(Reservation)
            .filter(Reservation.function_id == function_id)
            .all()
        )
        for reservation in reservations:
            ReservationService.expire_if_needed(db, reservation, changed_by=changed_by)

        total_seats = MovieFunctionService.count_seats(db, function.room_id)
        occupied = MovieFunctionService.count_occupied(db, function_id)

        reservation_rows = []
        for reservation in reservations:
            seat_ids = [
                seat_id
                for (seat_id,) in db.query(ReservationSeat.seat_id).filter(
                    ReservationSeat.reservation_id == reservation.reservation_id
                )
            ]
            reservation_rows.append({
                "reservation_id": reservation.reservation_id,
                "customer_name": reservation.customer_name,
                "status": reservation.status,
                "seat_ids": seat_ids,
            })

        return {
            "function_id": function.function_id,
            "movie_title": movie.title,
            "room_name": room.name,
            "start_datetime": function.start_datetime,
            "end_datetime": function.end_datetime,
            "asientos_ocupados": occupied,
            "asientos_disponibles": total_seats - occupied,
            "reservations": reservation_rows,
        }

    @staticmethod
    def get_function_seats(db: Session, *, function_id: int, changed_by: int) -> list[dict]:
        from src.services.reservation_service import ReservationService

        function = (
            db.query(MovieFunction)
            .filter(MovieFunction.function_id == function_id)
            .first()
        )
        if function is None:
            raise FunctionNotFoundError(f"Función {function_id} no existe")

        reservations = (
            db.query(Reservation)
            .filter(Reservation.function_id == function_id)
            .all()
        )
        for reservation in reservations:
            ReservationService.expire_if_needed(db, reservation, changed_by=changed_by)

        seats = (
            db.query(Seat)
            .filter(Seat.room_id == function.room_id)
            .order_by(Seat.row_label, Seat.seat_number)
            .all()
        )
        active_by_seat = {
            seat_id: reservation_id
            for seat_id, reservation_id in db.query(
                ActiveSeatReservation.seat_id, ActiveSeatReservation.reservation_id
            ).filter(ActiveSeatReservation.function_id == function_id)
        }

        return [
            {
                "seat_id": seat.seat_id,
                "row_label": seat.row_label,
                "seat_number": seat.seat_number,
                "seat_label": f"{seat.row_label}{seat.seat_number}",
                "ocupado": seat.seat_id in active_by_seat,
                "reservation_id": active_by_seat.get(seat.seat_id),
            }
            for seat in seats
        ]
