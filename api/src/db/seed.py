"""
Ejecutar con:  python -m src.db.seed
"""
from datetime import datetime, timedelta, timezone

from src.db.session import SessionLocal
from src.models import Movie, Room, Seat, MovieFunction, User
from src.security import hash_password


def run_seed():
    db = SessionLocal()
    try:
        # --- Usuarios ---
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                password=hash_password("Admin123!"),
                role="admin",
            ))

        if not db.query(User).filter(User.username == "taquillero1").first():
            db.add(User(
                username="taquillero1",
                password=hash_password("Taquilla123!"),
                role="taquillero",
            ))

        db.commit()

        # --- Sala + asientos (4 filas x 5 asientos) ---
        room = db.query(Room).filter(Room.name == "Sala 1").first()
        if not room:
            room = Room(name="Sala 1")
            db.add(room)
            db.commit()
            db.refresh(room)

            for row_label in ["A", "B", "C", "D"]:
                for seat_number in range(1, 6):
                    db.add(Seat(room_id=room.room_id, row_label=row_label, seat_number=seat_number))
            db.commit()

        # --- Película ---
        movie = db.query(Movie).filter(Movie.title == "Spiderman 2").first()
        if not movie:
            movie = Movie(title="Spiderman 2", duration_min=127, age_rating="PG-13")
            db.add(movie)
            db.commit()
            db.refresh(movie)

        # --- Función de ejemplo, mañana a las 19:00 ---
        existing_function = db.query(MovieFunction).filter(
            MovieFunction.movie_id == movie.movie_id,
            MovieFunction.room_id == room.room_id,
        ).first()
        if not existing_function:
            start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
                hour=19, minute=0, second=0, microsecond=0, tzinfo=None
            )
            end = start + timedelta(minutes=movie.duration_min)
            db.add(MovieFunction(
                movie_id=movie.movie_id,
                room_id=room.room_id,
                start_datetime=start,
                end_datetime=end,
            ))
            db.commit()

        print("Seed aplicado correctamente.")
        print("  admin / Admin123!")
        print("  taquillero1 / Taquilla123!")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
