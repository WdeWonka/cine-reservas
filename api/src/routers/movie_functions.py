from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.dependencies import require_role
from src.models import User
from src.schemas import (
    MovieFunctionCreate,
    MovieFunctionOut,
    MovieFunctionReportOut,
    SeatAvailabilityOut,
)
from src.services.movie_function_service import MovieFunctionService

router = APIRouter(prefix="/movie-functions", tags=["movie-functions"])


@router.post("", response_model=MovieFunctionOut, status_code=status.HTTP_201_CREATED)
def create_movie_function(
    payload: MovieFunctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    function = MovieFunctionService.create_function(
        db,
        movie_id=payload.movie_id,
        room_id=payload.room_id,
        start_datetime=payload.start_datetime,
    )
    total_seats = MovieFunctionService.count_seats(db, function.room_id)
    return MovieFunctionOut(
        function_id=function.function_id,
        movie_id=function.movie_id,
        room_id=function.room_id,
        start_datetime=function.start_datetime,
        end_datetime=function.end_datetime,
        asientos_totales=total_seats,
        asientos_ocupados=0,
        asientos_disponibles=total_seats,
        is_active=function.is_active,
    )


@router.get("", response_model=list[MovieFunctionOut])
def list_movie_functions(
    include_inactive: bool = False,
    date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    rows = MovieFunctionService.list_functions_with_availability(
        db, include_inactive=include_inactive, target_date=date
    )
    return [MovieFunctionOut(**row) for row in rows]


@router.patch("/{function_id}/disable", response_model=MovieFunctionOut)
def disable_movie_function(
    function_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    function = MovieFunctionService.disable_function(db, function_id=function_id)
    total_seats = MovieFunctionService.count_seats(db, function.room_id)
    occupied = MovieFunctionService.count_occupied(db, function_id)
    return MovieFunctionOut(
        function_id=function.function_id,
        movie_id=function.movie_id,
        room_id=function.room_id,
        start_datetime=function.start_datetime,
        end_datetime=function.end_datetime,
        asientos_totales=total_seats,
        asientos_ocupados=occupied,
        asientos_disponibles=total_seats - occupied,
        is_active=function.is_active,
    )


@router.patch("/{function_id}/enable", response_model=MovieFunctionOut)
def enable_movie_function(
    function_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    function = MovieFunctionService.enable_function(db, function_id=function_id)
    total_seats = MovieFunctionService.count_seats(db, function.room_id)
    occupied = MovieFunctionService.count_occupied(db, function_id)
    return MovieFunctionOut(
        function_id=function.function_id,
        movie_id=function.movie_id,
        room_id=function.room_id,
        start_datetime=function.start_datetime,
        end_datetime=function.end_datetime,
        asientos_totales=total_seats,
        asientos_ocupados=occupied,
        asientos_disponibles=total_seats - occupied,
        is_active=function.is_active,
    )


@router.get("/{function_id}/report", response_model=MovieFunctionReportOut)
def get_movie_function_report(
    function_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    report = MovieFunctionService.get_function_report(
        db, function_id=function_id, changed_by=current_user.user_id
    )
    return MovieFunctionReportOut(**report)


@router.get("/{function_id}/seats", response_model=list[SeatAvailabilityOut])
def get_movie_function_seats(
    function_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    seats = MovieFunctionService.get_function_seats(
        db, function_id=function_id, changed_by=current_user.user_id
    )
    return [SeatAvailabilityOut(**seat) for seat in seats]
