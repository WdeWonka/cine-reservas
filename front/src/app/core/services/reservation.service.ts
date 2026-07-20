import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  ReservationCreate,
  ReservationOut,
  ReservationStatus,
  ReservationStatusUpdate,
  TicketOut,
} from '../models';

@Injectable({ providedIn: 'root' })
export class ReservationService {
  private readonly baseUrl = `${environment.apiUrl}/reservations`;

  constructor(private readonly http: HttpClient) {}

  list(options: { functionId?: number; status?: ReservationStatus } = {}): Observable<ReservationOut[]> {
    let params = new HttpParams();
    if (options.functionId != null) {
      params = params.set('function_id', options.functionId);
    }
    if (options.status) {
      params = params.set('status', options.status);
    }
    return this.http.get<ReservationOut[]>(this.baseUrl, { params });
  }

  get(reservationId: number): Observable<ReservationOut> {
    return this.http.get<ReservationOut>(`${this.baseUrl}/${reservationId}`);
  }

  create(payload: ReservationCreate): Observable<ReservationOut> {
    return this.http.post<ReservationOut>(this.baseUrl, payload);
  }

  changeStatus(reservationId: number, payload: ReservationStatusUpdate): Observable<ReservationOut> {
    return this.http.patch<ReservationOut>(`${this.baseUrl}/${reservationId}`, payload);
  }

  getTickets(reservationId: number): Observable<TicketOut[]> {
    return this.http.get<TicketOut[]>(`${this.baseUrl}/${reservationId}/tickets`);
  }
}
