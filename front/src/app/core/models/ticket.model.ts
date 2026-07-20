export interface TicketOut {
  ticket_id: number;
  ticket_code: string;
  ticket_type: string;
  issued_at: string;
  seat_id: number;
  row_label: string;
  seat_number: number;
  seat_label: string;
}

export interface TicketScanRequest {
  ticket_code: string;
}

export interface ScanResultOut {
  reservation_id: number;
  customer_name: string;
  customer_email: string | null;
  status: string;
  seat_ids: number[];
  tickets: TicketOut[];
}
