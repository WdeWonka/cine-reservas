import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
  },
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard('admin')],
    loadComponent: () =>
      import('./features/admin/admin-shell/admin-shell').then((m) => m.AdminShell),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'movies' },
      {
        path: 'movies',
        loadComponent: () =>
          import('./features/admin/movies/movie-list').then((m) => m.MovieList),
      },
      {
        path: 'rooms',
        loadComponent: () => import('./features/admin/rooms/room-list').then((m) => m.RoomList),
      },
      {
        path: 'movie-functions',
        loadComponent: () =>
          import('./features/admin/movie-functions/function-list').then((m) => m.FunctionList),
      },
      {
        path: 'reservations',
        loadComponent: () =>
          import('./features/admin/reservations/reservation-list').then(
            (m) => m.ReservationList,
          ),
      },
    ],
  },
  {
    path: 'taquillero',
    canActivate: [authGuard, roleGuard('taquillero')],
    loadComponent: () =>
      import('./features/taquillero/booking-flow/booking-flow').then((m) => m.BookingFlow),
  },
  {
    path: 'scan',
    canActivate: [authGuard],
    loadComponent: () => import('./features/scan/scan-ticket').then((m) => m.ScanTicket),
  },
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  { path: '**', redirectTo: 'login' },
];
