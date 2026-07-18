from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.dependencies import require_role
from src.models import User
from src.schemas import ReservationCreate, ReservationOut, ReservationStatusUpdate, TicketOut
from src.services.reservation_service import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    reservation, seat_ids = ReservationService.create_reservation(
        db,
        function_id=payload.function_id,
        seat_ids=payload.seat_ids,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_email=payload.customer_email,
        created_by=current_user.user_id,
    )
    return ReservationOut(
        reservation_id=reservation.reservation_id,
        function_id=reservation.function_id,
        customer_name=reservation.customer_name,
        customer_phone=reservation.customer_phone,
        customer_email=reservation.customer_email,
        status=reservation.status,
        expires_at=reservation.expires_at,
        created_at=reservation.created_at,
        seat_ids=seat_ids,
    )


@router.get("", response_model=list[ReservationOut])
def list_reservations(
    function_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    rows = ReservationService.list_reservations(
        db, function_id=function_id, status_filter=status, changed_by=current_user.user_id
    )
    return [
        ReservationOut(
            reservation_id=reservation.reservation_id,
            function_id=reservation.function_id,
            customer_name=reservation.customer_name,
            customer_phone=reservation.customer_phone,
            customer_email=reservation.customer_email,
            status=reservation.status,
            expires_at=reservation.expires_at,
            created_at=reservation.created_at,
            seat_ids=seat_ids,
        )
        for reservation, seat_ids in rows
    ]


@router.get("/{reservation_id}", response_model=ReservationOut)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    reservation, seat_ids = ReservationService.get_reservation(
        db, reservation_id=reservation_id, changed_by=current_user.user_id
    )
    return ReservationOut(
        reservation_id=reservation.reservation_id,
        function_id=reservation.function_id,
        customer_name=reservation.customer_name,
        customer_phone=reservation.customer_phone,
        customer_email=reservation.customer_email,
        status=reservation.status,
        expires_at=reservation.expires_at,
        created_at=reservation.created_at,
        seat_ids=seat_ids,
    )


@router.get("/{reservation_id}/tickets", response_model=list[TicketOut])
def get_reservation_tickets(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    rows = ReservationService.get_reservation_tickets(db, reservation_id=reservation_id)
    return [TicketOut(**row) for row in rows]


@router.patch("/{reservation_id}", response_model=ReservationOut)
def change_reservation_status(
    reservation_id: int,
    payload: ReservationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    reservation, seat_ids = ReservationService.change_status(
        db,
        reservation_id=reservation_id,
        new_status=payload.new_status,
        changed_by=current_user.user_id,
    )
    return ReservationOut(
        reservation_id=reservation.reservation_id,
        function_id=reservation.function_id,
        customer_name=reservation.customer_name,
        customer_phone=reservation.customer_phone,
        customer_email=reservation.customer_email,
        status=reservation.status,
        expires_at=reservation.expires_at,
        created_at=reservation.created_at,
        seat_ids=seat_ids,
    )
