from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.exceptions import AppError
from src.models import MovieFunction, Room, Seat


class RoomError(AppError):
    """Error de negocio base para la gestión de salas."""


class RoomNotFoundError(RoomError):
    status_code = status.HTTP_404_NOT_FOUND


class RoomNameAlreadyExistsError(RoomError):
    status_code = status.HTTP_409_CONFLICT


class InvalidRoomLayoutError(RoomError):
    """row_labels contiene filas repetidas, incompatible con el layout de asientos."""


class RoomHasActiveFunctionsError(RoomError):
    status_code = status.HTTP_409_CONFLICT


class RoomService:
    @staticmethod
    def create_room(
        db: Session,
        *,
        name: str,
        row_labels: list[str],
        seats_per_row: int,
    ) -> Room:
        if len(set(row_labels)) != len(row_labels):
            raise InvalidRoomLayoutError("row_labels no puede contener filas repetidas")

        existing = db.query(Room).filter(Room.name == name).first()
        if existing is not None:
            raise RoomNameAlreadyExistsError(f"Ya existe una sala llamada '{name}'")

        room = Room(name=name)
        db.add(room)

        try:
            db.flush()  # asigna room_id; el UNIQUE(Room.name) se valida acá
                        # de verdad si hay una carrera con el SELECT de arriba

            for row_label in row_labels:
                for seat_number in range(1, seats_per_row + 1):
                    db.add(Seat(room_id=room.room_id, row_label=row_label, seat_number=seat_number))

            db.commit()
        except IntegrityError:
            db.rollback()
            raise RoomNameAlreadyExistsError(f"Ya existe una sala llamada '{name}'")

        db.refresh(room)
        return room

    @staticmethod
    def count_seats(db: Session, room_id: int) -> int:
        return (
            db.query(func.count(Seat.seat_id))
            .filter(Seat.room_id == room_id)
            .scalar()
        )

    @staticmethod
    def update_room_name(db: Session, *, room_id: int, name: str) -> Room:
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Sala {room_id} no existe")

        existing = db.query(Room).filter(Room.name == name, Room.room_id != room_id).first()
        if existing is not None:
            raise RoomNameAlreadyExistsError(f"Ya existe una sala llamada '{name}'")

        room.name = name
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise RoomNameAlreadyExistsError(f"Ya existe una sala llamada '{name}'")

        db.refresh(room)
        return room

    @staticmethod
    def disable_room(db: Session, *, room_id: int) -> Room:
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Sala {room_id} no existe")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        has_future_functions = (
            db.query(MovieFunction)
            .filter(
                MovieFunction.room_id == room_id,
                MovieFunction.is_active == True,  # noqa: E712 — MSSQL no soporta "IS 1"
                MovieFunction.start_datetime > now,
            )
            .first()
        )
        if has_future_functions is not None:
            raise RoomHasActiveFunctionsError(
                "No se puede deshabilitar la sala: tiene funciones futuras programadas"
            )

        room.is_active = False
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def enable_room(db: Session, *, room_id: int) -> Room:
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if room is None:
            raise RoomNotFoundError(f"Sala {room_id} no existe")
        room.is_active = True
        db.commit()
        db.refresh(room)
        return room

    @staticmethod
    def list_rooms(db: Session, *, include_inactive: bool = False) -> list[dict]:
        query = (
            db.query(Room, func.count(Seat.seat_id).label("total_seats"))
            .outerjoin(Seat, Seat.room_id == Room.room_id)
        )
        if not include_inactive:
            query = query.filter(Room.is_active == True)  # noqa: E712 — MSSQL no soporta "IS 1"

        rows = (
            query.group_by(Room.room_id, Room.name, Room.created_at, Room.is_active)
            .order_by(Room.name)
            .all()
        )
        return [
            {
                "room_id": room.room_id,
                "name": room.name,
                "asientos_totales": total_seats,
                "is_active": room.is_active,
            }
            for room, total_seats in rows
        ]
