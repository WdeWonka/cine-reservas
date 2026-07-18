from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, timezone


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    user_id: int
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class ReservationCreate(BaseModel):
    function_id: int
    seat_ids: list[int] = Field(min_length=1)
    customer_name: str = Field(min_length=1, max_length=150)
    customer_phone: str | None = Field(default=None, max_length=30)
    customer_email: str | None = Field(default=None, max_length=150)


class ReservationOut(BaseModel):
    reservation_id: int
    function_id: int
    customer_name: str
    customer_phone: str | None
    customer_email: str | None
    status: str
    expires_at: datetime | None
    created_at: datetime
    seat_ids: list[int]

    class Config:
        from_attributes = True


class ReservationStatusUpdate(BaseModel):
    new_status: str = Field(min_length=1)


class MovieFunctionCreate(BaseModel):
    movie_id: int
    room_id: int
    start_datetime: datetime

    @field_validator("start_datetime")
    @classmethod
    def normalize_start_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class MovieFunctionOut(BaseModel):
    function_id: int
    movie_id: int
    room_id: int
    start_datetime: datetime
    end_datetime: datetime
    asientos_totales: int
    asientos_ocupados: int
    asientos_disponibles: int
    is_active: bool

    class Config:
        from_attributes = True


class ReservationStatusOut(BaseModel):
    reservation_id: int
    customer_name: str
    status: str
    seat_ids: list[int]


class MovieFunctionReportOut(BaseModel):
    function_id: int
    movie_title: str
    room_name: str
    start_datetime: datetime
    end_datetime: datetime
    asientos_ocupados: int
    asientos_disponibles: int
    reservations: list[ReservationStatusOut]


class SeatAvailabilityOut(BaseModel):
    seat_id: int
    row_label: str
    seat_number: int
    seat_label: str
    ocupado: bool
    reservation_id: int | None


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    row_labels: list[str] = Field(min_length=1)
    seats_per_row: int = Field(gt=0)

    @field_validator("row_labels")
    @classmethod
    def validate_row_labels(cls, value: list[str]) -> list[str]:
        for label in value:
            if len(label) != 1:
                raise ValueError(f"row_label '{label}' debe ser un único carácter")
        return value


class RoomUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=50)


class RoomOut(BaseModel):
    room_id: int
    name: str
    asientos_totales: int
    is_active: bool


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    duration_min: int = Field(gt=0)
    age_rating: str | None = Field(default=None, max_length=10)


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    duration_min: int | None = Field(default=None, gt=0)
    age_rating: str | None = Field(default=None, max_length=10)


class MovieOut(BaseModel):
    movie_id: int
    title: str
    duration_min: int
    age_rating: str | None
    is_active: bool

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    ticket_id: int
    ticket_code: str
    ticket_type: str
    issued_at: datetime
    seat_id: int
    row_label: str
    seat_number: int
    seat_label: str


class TicketScanRequest(BaseModel):
    ticket_code: str = Field(min_length=1, max_length=20)


class ScanResultOut(BaseModel):
    reservation_id: int
    customer_name: str
    customer_email: str | None
    status: str
    seat_ids: list[int]
    tickets: list[TicketOut]

