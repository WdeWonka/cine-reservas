import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { firstValueFrom, Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Role, Token, UserOut } from '../models';

const TOKEN_STORAGE_KEY = 'cine_reservas_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly _currentUser = signal<UserOut | null>(null);

  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly role = computed<Role | null>(() => (this._currentUser()?.role as Role) ?? null);

  constructor(private readonly http: HttpClient) {}

  login(username: string, password: string): Observable<Token> {
    const body = new HttpParams()
      .set('grant_type', 'password')
      .set('username', username)
      .set('password', password);

    return this.http
      .post<Token>(`${environment.apiUrl}/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(tap((token) => this.storeToken(token.access_token)));
  }

  me(): Observable<UserOut> {
    return this.http
      .get<UserOut>(`${environment.apiUrl}/auth/me`)
      .pipe(tap((user) => this._currentUser.set(user)));
  }

  logout(): void {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    this._currentUser.set(null);
  }

  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_STORAGE_KEY);
  }

  /**
   * Se llama una sola vez al arrancar la app (provideAppInitializer en
   * app.config.ts) para restaurar la sesión si ya había un token guardado
   * de una carga anterior de la página.
   */
  async restoreSession(): Promise<void> {
    const token = this.getToken();
    if (!token) return;

    try {
      await firstValueFrom(this.me());
    } catch {
      this.logout();
    }
  }

  private storeToken(token: string): void {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}
