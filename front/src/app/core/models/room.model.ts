export interface RoomCreate {
  name: string;
  row_labels: string[];
  seats_per_row: number;
}

export interface RoomUpdate {
  name: string;
}

export interface RoomOut {
  room_id: number;
  name: string;
  asientos_totales: number;
  is_active: boolean;
}
