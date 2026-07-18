from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.dependencies import require_role
from src.models import User
from src.schemas import MovieCreate, MovieOut, MovieUpdate
from src.services.movie_service import MovieService

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
def create_movie(
    payload: MovieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return MovieService.create_movie(
        db,
        title=payload.title,
        duration_min=payload.duration_min,
        age_rating=payload.age_rating,
    )


@router.get("", response_model=list[MovieOut])
def list_movies(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    return MovieService.list_movies(db, include_inactive=include_inactive)


@router.patch("/{movie_id}", response_model=MovieOut)
def update_movie(
    movie_id: int,
    payload: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    updates = payload.model_dump(exclude_unset=True)
    return MovieService.update_movie(db, movie_id=movie_id, updates=updates)


@router.patch("/{movie_id}/disable", response_model=MovieOut)
def disable_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return MovieService.disable_movie(db, movie_id=movie_id)


@router.patch("/{movie_id}/enable", response_model=MovieOut)
def enable_movie(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return MovieService.enable_movie(db, movie_id=movie_id)
