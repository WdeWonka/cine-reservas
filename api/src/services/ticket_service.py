from fastapi import status
from sqlalchemy.orm import Session

from src.exceptions import AppError
from src.models import ReservationSeat, Ticket
from src.services.reservation_service import ReservationService


class TicketError(AppError):
    """Error de negocio base para el escaneo de tickets."""


class TicketNotFoundError(TicketError):
    status_code = status.HTTP_404_NOT_FOUND


class TicketService:
    @staticmethod
    def scan_ticket(db: Session, *, ticket_code: str, changed_by: int) -> dict:
        ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
        if ticket is None:
            raise TicketNotFoundError(f"Ticket '{ticket_code}' no existe")

        reservation_seat = (
            db.query(ReservationSeat)
            .filter(ReservationSeat.reservation_seat_id == ticket.reservation_seat_id)
            .first()
        )

        reservation, seat_ids = ReservationService.change_status(
            db,
            reservation_id=reservation_seat.reservation_id,
            new_status="Utilizada",
            changed_by=changed_by,
        )

        tickets = ReservationService.get_reservation_tickets(
            db, reservation_id=reservation.reservation_id
        )

        return {
            "reservation_id": reservation.reservation_id,
            "customer_name": reservation.customer_name,
            "customer_email": reservation.customer_email,
            "status": reservation.status,
            "seat_ids": seat_ids,
            "tickets": tickets,
        }
