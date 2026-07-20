import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Role } from '../models';
import { AuthService } from '../services/auth.service';

export function roleGuard(...allowedRoles: Role[]): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    const role = auth.role();
    if (role && allowedRoles.includes(role)) {
      return true;
    }

    // Autenticado pero sin permiso para esta sección -> a su propia home,
    // no a /login (ya está logueado, solo no tiene el rol correcto).
    return router.createUrlTree([role === 'admin' ? '/admin' : '/taquillero']);
  };
}
