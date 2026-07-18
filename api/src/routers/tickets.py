from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.dependencies import require_role
from src.models import User
from src.schemas import ScanResultOut, TicketScanRequest
from src.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/scan", response_model=ScanResultOut)
def scan_ticket(
    payload: TicketScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "taquillero")),
):
    result = TicketService.scan_ticket(
        db, ticket_code=payload.ticket_code, changed_by=current_user.user_id
    )
    return ScanResultOut(**result)
