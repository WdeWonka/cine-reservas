from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.dependencies import require_role
from src.models import User
from src.schemas import RoomCreate, RoomOut, RoomUpdate
from src.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    room = RoomService.create_room(
        db,
        name=payload.name,
        row_labels=payload.row_labels,
        seats_per_row=payload.seats_per_row,
    )
    total_seats = len(payload.row_labels) * payload.seats_per_row
    return RoomOut(
        room_id=room.room_id, name=room.name, asientos_totales=total_seats, is_active=room.is_active
    )


@router.get("", response_model=list[RoomOut])
def list_rooms(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    rows = RoomService.list_rooms(db, include_inactive=include_inactive)
    return [RoomOut(**row) for row in rows]


@router.patch("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    room = RoomService.update_room_name(db, room_id=room_id, name=payload.name)
    total_seats = RoomService.count_seats(db, room_id)
    return RoomOut(
        room_id=room.room_id, name=room.name, asientos_totales=total_seats, is_active=room.is_active
    )


@router.patch("/{room_id}/disable", response_model=RoomOut)
def disable_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    room = RoomService.disable_room(db, room_id=room_id)
    total_seats = RoomService.count_seats(db, room_id)
    return RoomOut(
        room_id=room.room_id, name=room.name, asientos_totales=total_seats, is_active=room.is_active
    )


@router.patch("/{room_id}/enable", response_model=RoomOut)
def enable_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    room = RoomService.enable_room(db, room_id=room_id)
    total_seats = RoomService.count_seats(db, room_id)
    return RoomOut(
        room_id=room.room_id, name=room.name, asientos_totales=total_seats, is_active=room.is_active
    )
