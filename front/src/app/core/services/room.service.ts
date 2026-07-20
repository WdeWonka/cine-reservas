import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { RoomCreate, RoomOut, RoomUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class RoomService {
  private readonly baseUrl = `${environment.apiUrl}/rooms`;

  constructor(private readonly http: HttpClient) {}

  list(includeInactive = false): Observable<RoomOut[]> {
    const params = new HttpParams().set('include_inactive', includeInactive);
    return this.http.get<RoomOut[]>(this.baseUrl, { params });
  }

  create(payload: RoomCreate): Observable<RoomOut> {
    return this.http.post<RoomOut>(this.baseUrl, payload);
  }

  update(roomId: number, payload: RoomUpdate): Observable<RoomOut> {
    return this.http.patch<RoomOut>(`${this.baseUrl}/${roomId}`, payload);
  }

  disable(roomId: number): Observable<RoomOut> {
    return this.http.patch<RoomOut>(`${this.baseUrl}/${roomId}/disable`, {});
  }

  enable(roomId: number): Observable<RoomOut> {
    return this.http.patch<RoomOut>(`${this.baseUrl}/${roomId}/enable`, {});
  }
}
