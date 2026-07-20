import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  MovieFunctionCreate,
  MovieFunctionOut,
  MovieFunctionReportOut,
  SeatAvailabilityOut,
} from '../models';

@Injectable({ providedIn: 'root' })
export class MovieFunctionService {
  private readonly baseUrl = `${environment.apiUrl}/movie-functions`;

  constructor(private readonly http: HttpClient) {}

  /**
   * `date` (si se pasa) es el filtro grueso que ya soporta el backend
   * (día calendario naive-UTC). Para "hoy en Guatemala" no alcanza por sí
   * solo — el filtro autoritativo final se hace client-side comparando
   * start_datetime contra el rango UTC calculado (ver plan de timezone
   * acordado). `date`, si se usa, es solo una optimización de consulta.
   */
  list(options: { includeInactive?: boolean; date?: string } = {}): Observable<MovieFunctionOut[]> {
    let params = new HttpParams().set('include_inactive', options.includeInactive ?? false);
    if (options.date) {
      params = params.set('date', options.date);
    }
    return this.http.get<MovieFunctionOut[]>(this.baseUrl, { params });
  }

  create(payload: MovieFunctionCreate): Observable<MovieFunctionOut> {
    return this.http.post<MovieFunctionOut>(this.baseUrl, payload);
  }

  disable(functionId: number): Observable<MovieFunctionOut> {
    return this.http.patch<MovieFunctionOut>(`${this.baseUrl}/${functionId}/disable`, {});
  }

  enable(functionId: number): Observable<MovieFunctionOut> {
    return this.http.patch<MovieFunctionOut>(`${this.baseUrl}/${functionId}/enable`, {});
  }

  getReport(functionId: number): Observable<MovieFunctionReportOut> {
    return this.http.get<MovieFunctionReportOut>(`${this.baseUrl}/${functionId}/report`);
  }

  getSeats(functionId: number): Observable<SeatAvailabilityOut[]> {
    return this.http.get<SeatAvailabilityOut[]>(`${this.baseUrl}/${functionId}/seats`);
  }
}
