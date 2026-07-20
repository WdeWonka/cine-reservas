export type ReservationStatus =
  | 'Reservada'
  | 'Confirmada'
  | 'Utilizada'
  | 'Cancelada'
  | 'Expirada';

export interface ReservationCreate {
  function_id: number;
  seat_ids: number[];
  customer_name: string;
  customer_phone?: string | null;
  customer_email?: string | null;
}

export interface ReservationOut {
  reservation_id: number;
  function_id: number;
  customer_name: string;
  customer_phone: string | null;
  customer_email: string | null;
  status: ReservationStatus;
  expires_at: string | null;
  created_at: string;
  seat_ids: number[];
}

export interface ReservationStatusUpdate {
  new_status: ReservationStatus;
}
