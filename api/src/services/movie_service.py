from fastapi import status
from sqlalchemy.orm import Session

from src.exceptions import AppError
from src.models import Movie


class MovieError(AppError):
    """Error de negocio base para la gestión de películas."""


class MovieNotFoundError(MovieError):
    status_code = status.HTTP_404_NOT_FOUND


class MovieService:
    @staticmethod
    def create_movie(
        db: Session,
        *,
        title: str,
        duration_min: int,
        age_rating: str | None,
    ) -> Movie:
        movie = Movie(title=title, duration_min=duration_min, age_rating=age_rating)
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def update_movie(db: Session, *, movie_id: int, updates: dict) -> Movie:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if movie is None:
            raise MovieNotFoundError(f"Película {movie_id} no existe")

        for field, value in updates.items():
            setattr(movie, field, value)

        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def disable_movie(db: Session, *, movie_id: int) -> Movie:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if movie is None:
            raise MovieNotFoundError(f"Película {movie_id} no existe")
        movie.is_active = False
        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def enable_movie(db: Session, *, movie_id: int) -> Movie:
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if movie is None:
            raise MovieNotFoundError(f"Película {movie_id} no existe")
        movie.is_active = True
        db.commit()
        db.refresh(movie)
        return movie

    @staticmethod
    def list_movies(db: Session, *, include_inactive: bool = False) -> list[Movie]:
        query = db.query(Movie)
        if not include_inactive:
            query = query.filter(Movie.is_active == True)  # noqa: E712 — MSSQL no soporta "IS 1"
        return query.order_by(Movie.title).all()
