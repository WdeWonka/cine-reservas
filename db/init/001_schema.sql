-- =====================================================================
-- Cine Reservas — Esquema de base de datos (SQL Server)
-- Fiel al modelo documentado en docs/modelo-bd.md y docs/analisis-funcional.md
-- =====================================================================

-- -----------------------------------------------------------------------
-- Movie
-- -----------------------------------------------------------------------
CREATE TABLE Movie (
    movie_id      INT IDENTITY(1,1) PRIMARY KEY,
    title         VARCHAR(200) NOT NULL,
    -- Valor semilla al crear una función; no se recalcula después.
    duration_min  SMALLINT NOT NULL,
    age_rating    VARCHAR(10) NULL,
    created_at    DATETIME NOT NULL DEFAULT GETUTCDATE()
);

-- -----------------------------------------------------------------------
-- Room
-- -----------------------------------------------------------------------
CREATE TABLE Room (
    room_id     INT IDENTITY(1,1) PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    created_at  DATETIME NOT NULL DEFAULT GETUTCDATE()
);

-- -----------------------------------------------------------------------
-- Seat
-- -----------------------------------------------------------------------
CREATE TABLE Seat (
    seat_id      INT IDENTITY(1,1) PRIMARY KEY,
    room_id      INT NOT NULL,
    row_label    CHAR(1) NOT NULL,
    seat_number  SMALLINT NOT NULL,
    CONSTRAINT fk_seat_room FOREIGN KEY (room_id) REFERENCES Room(room_id),
    CONSTRAINT ux_seat_room_row_number UNIQUE (room_id, row_label, seat_number)
);

-- -----------------------------------------------------------------------
-- MovieFunction
-- -----------------------------------------------------------------------
CREATE TABLE MovieFunction (
    function_id     INT IDENTITY(1,1) PRIMARY KEY,
    movie_id        INT NOT NULL,
    room_id         INT NOT NULL,
    start_datetime  DATETIME NOT NULL,
    -- Fotografía histórica: start_datetime + Movie.duration_min al crear
    -- la función. No se recalcula si la duración cambia después.
    end_datetime    DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_function_movie FOREIGN KEY (movie_id) REFERENCES Movie(movie_id),
    CONSTRAINT fk_function_room FOREIGN KEY (room_id) REFERENCES Room(room_id)
);

CREATE INDEX ix_function_room_start ON MovieFunction(room_id, start_datetime);

-- El no-solapamiento de funciones en la misma sala se valida en la capa de
-- servicio (SQL Server no tiene exclusion constraints nativos como Postgres).

-- -----------------------------------------------------------------------
-- User
-- -----------------------------------------------------------------------
CREATE TABLE [User] (
    user_id      INT IDENTITY(1,1) PRIMARY KEY,
    username     VARCHAR(50) NOT NULL UNIQUE,
    -- Hash bcrypt, nunca texto plano.
    password     VARCHAR(255) NOT NULL,
    role         VARCHAR(20) NOT NULL,
    is_active    BIT NOT NULL DEFAULT 1,
    created_at   DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT ck_user_role CHECK (role IN ('admin','taquillero'))
);

-- -----------------------------------------------------------------------
-- Reservation
-- -----------------------------------------------------------------------
CREATE TABLE Reservation (
    reservation_id  INT IDENTITY(1,1) PRIMARY KEY,
    function_id     INT NOT NULL,
    customer_name   VARCHAR(150) NOT NULL,
    customer_phone  VARCHAR(30) NULL,
    status          VARCHAR(20) NOT NULL,
    expires_at      DATETIME NULL,
    created_by      INT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT GETUTCDATE(),
    updated_at      DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_reservation_function FOREIGN KEY (function_id) REFERENCES MovieFunction(function_id),
    CONSTRAINT fk_reservation_created_by FOREIGN KEY (created_by) REFERENCES [User](user_id),
    CONSTRAINT ck_reservation_status CHECK (status IN ('Reservada','Confirmada','Utilizada','Cancelada','Expirada'))
);

CREATE INDEX ix_reservation_function ON Reservation(function_id);
CREATE INDEX ix_reservation_status ON Reservation(status);
CREATE INDEX ix_reservation_created_by ON Reservation(created_by);

-- -----------------------------------------------------------------------
-- ReservationSeat — historial permanente, nunca se borra ni se modifica.
-- No garantiza unicidad de ocupación activa (ver ActiveSeatReservation).
-- -----------------------------------------------------------------------
CREATE TABLE ReservationSeat (
    reservation_seat_id  INT IDENTITY(1,1) PRIMARY KEY,
    reservation_id        INT NOT NULL,
    seat_id                INT NOT NULL,
    -- Denormalizado desde Reservation.function_id, solo para trazabilidad
    -- histórica; no participa en ninguna restricción de unicidad activa.
    function_id            INT NOT NULL,
    created_at             DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_resseat_reservation FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id),
    CONSTRAINT fk_resseat_seat FOREIGN KEY (seat_id) REFERENCES Seat(seat_id),
    CONSTRAINT fk_resseat_function FOREIGN KEY (function_id) REFERENCES MovieFunction(function_id),
    CONSTRAINT ux_reservation_seat UNIQUE (reservation_id, seat_id)
);

-- -----------------------------------------------------------------------
-- ActiveSeatReservation — ocupación VIGENTE de un asiento por función.
-- Se inserta al crear la reserva; se elimina al cancelarse o expirar.
-- El UNIQUE(function_id, seat_id) es la garantía real de RNF-01 a nivel
-- de motor de base de datos (ver docs/modelo-bd.md, sección 2).
-- -----------------------------------------------------------------------
CREATE TABLE ActiveSeatReservation (
    active_seat_reservation_id  INT IDENTITY(1,1) PRIMARY KEY,
    function_id                  INT NOT NULL,
    seat_id                      INT NOT NULL,
    reservation_id               INT NOT NULL,
    created_at                   DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_activeseat_function FOREIGN KEY (function_id) REFERENCES MovieFunction(function_id),
    CONSTRAINT fk_activeseat_seat FOREIGN KEY (seat_id) REFERENCES Seat(seat_id),
    CONSTRAINT fk_activeseat_reservation FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id),
    CONSTRAINT ux_active_seat_reservation UNIQUE (function_id, seat_id)
);

-- -----------------------------------------------------------------------
-- ReservationStatusHistory — auditoría de cambios de estado (RNF-05).
-- -----------------------------------------------------------------------
CREATE TABLE ReservationStatusHistory (
    history_id      INT IDENTITY(1,1) PRIMARY KEY,
    reservation_id  INT NOT NULL,
    from_status     VARCHAR(20) NULL,  -- NULL en el primer registro
    to_status       VARCHAR(20) NOT NULL,
    changed_by      INT NOT NULL,
    changed_at      DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_history_reservation FOREIGN KEY (reservation_id) REFERENCES Reservation(reservation_id),
    CONSTRAINT fk_history_changed_by FOREIGN KEY (changed_by) REFERENCES [User](user_id),
    CONSTRAINT ck_history_from_status CHECK (from_status IS NULL OR from_status IN ('Reservada','Confirmada','Utilizada','Cancelada','Expirada')),
    CONSTRAINT ck_history_to_status CHECK (to_status IN ('Reservada','Confirmada','Utilizada','Cancelada','Expirada'))
);

-- -----------------------------------------------------------------------
-- Ticket — comprobante digital por asiento confirmado (RF-11, RF-12).
-- Referencia ReservationSeat (histórico), no ActiveSeatReservation
-- (vigente). No tiene ciclo de vida propio (regla 5.2.6 del análisis).
-- -----------------------------------------------------------------------
CREATE TABLE Ticket (
    ticket_id            INT IDENTITY(1,1) PRIMARY KEY,
    reservation_seat_id  INT NOT NULL UNIQUE,
    ticket_type          VARCHAR(20) NOT NULL DEFAULT 'Adulto',
    ticket_code          VARCHAR(20) NOT NULL UNIQUE,
    issued_at            DATETIME NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT fk_ticket_resseat FOREIGN KEY (reservation_seat_id) REFERENCES ReservationSeat(reservation_seat_id)
);
