import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { MovieCreate, MovieOut, MovieUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class MovieService {
  private readonly baseUrl = `${environment.apiUrl}/movies`;

  constructor(private readonly http: HttpClient) {}

  list(includeInactive = false): Observable<MovieOut[]> {
    const params = new HttpParams().set('include_inactive', includeInactive);
    return this.http.get<MovieOut[]>(this.baseUrl, { params });
  }

  create(payload: MovieCreate): Observable<MovieOut> {
    return this.http.post<MovieOut>(this.baseUrl, payload);
  }

  update(movieId: number, payload: MovieUpdate): Observable<MovieOut> {
    return this.http.patch<MovieOut>(`${this.baseUrl}/${movieId}`, payload);
  }

  disable(movieId: number): Observable<MovieOut> {
    return this.http.patch<MovieOut>(`${this.baseUrl}/${movieId}/disable`, {});
  }

  enable(movieId: number): Observable<MovieOut> {
    return this.http.patch<MovieOut>(`${this.baseUrl}/${movieId}/enable`, {});
  }
}
