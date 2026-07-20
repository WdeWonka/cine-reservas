import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ScanResultOut, TicketScanRequest } from '../models';

@Injectable({ providedIn: 'root' })
export class TicketService {
  private readonly baseUrl = `${environment.apiUrl}/tickets`;

  constructor(private readonly http: HttpClient) {}

  scan(payload: TicketScanRequest): Observable<ScanResultOut> {
    return this.http.post<ScanResultOut>(`${this.baseUrl}/scan`, payload);
  }
}
