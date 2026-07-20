export interface MovieFunctionCreate {
  movie_id: number;
  room_id: number;
  start_datetime: string; // naive-UTC ISO, sin sufijo de zona
}

export interface MovieFunctionOut {
  function_id: number;
  movie_id: number;
  room_id: number;
  start_datetime: string;
  end_datetime: string;
  asientos_totales: number;
  asientos_ocupados: number;
  asientos_disponibles: number;
  is_active: boolean;
}

export interface SeatAvailabilityOut {
  seat_id: number;
  row_label: string;
  seat_number: number;
  seat_label: string;
  ocupado: boolean;
  reservation_id: number | null;
}

export interface ReservationStatusOut {
  reservation_id: number;
  customer_name: string;
  status: string;
  seat_ids: number[];
}

export interface MovieFunctionReportOut {
  function_id: number;
  movie_title: string;
  room_name: string;
  start_datetime: string;
  end_datetime: string;
  asientos_ocupados: number;
  asientos_disponibles: number;
  reservations: ReservationStatusOut[];
}
