import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { ToastService } from '../../shared/components/toast/toast.service';
import { AuthService } from '../services/auth.service';

/**
 * Traduce los errores {"detail": "..."} del exception handler global del
 * backend (src/exceptions.py) a un toast. Un 401 además cierra la sesión
 * local y redirige a /login — el token ya no sirve, no tiene sentido
 * seguir mostrando la app como si estuviera autenticado.
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  const auth = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        auth.logout();
        router.navigate(['/login']);
        toast.error('Tu sesión expiró. Iniciá sesión de nuevo.');
        return throwError(() => error);
      }

      const detail = typeof error.error?.detail === 'string' ? error.error.detail : null;
      toast.error(detail ?? 'Ocurrió un error inesperado. Intentá de nuevo.');

      return throwError(() => error);
    }),
  );
};
