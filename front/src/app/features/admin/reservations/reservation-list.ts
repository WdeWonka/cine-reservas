import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieFunctionOut, ReservationOut, ReservationStatus } from '../../../core/models';
import { MovieFunctionService } from '../../../core/services/movie-function.service';
import { ReservationService } from '../../../core/services/reservation.service';
import { GUATEMALA_TIMEZONE, parseUtcIso } from '../../../core/utils/datetime.util';

const STATUSES: ReservationStatus[] = [
  'Reservada',
  'Confirmada',
  'Utilizada',
  'Cancelada',
  'Expirada',
];

@Component({
  selector: 'app-reservation-list',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './reservation-list.html',
  styleUrl: './reservation-list.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReservationList {
  private readonly reservationService = inject(ReservationService);
  private readonly functionService = inject(MovieFunctionService);

  protected readonly statuses = STATUSES;
  protected readonly reservations = signal<ReservationOut[]>([]);
  protected readonly functions = signal<MovieFunctionOut[]>([]);

  protected selectedFunctionId: number | null = null;
  protected selectedStatus: ReservationStatus | null = null;

  constructor() {
    this.functionService
      .list({ includeInactive: true })
      .subscribe((functions) => this.functions.set(functions));
    this.load();
  }

  load(): void {
    this.reservationService
      .list({
        functionId: this.selectedFunctionId ?? undefined,
        status: this.selectedStatus ?? undefined,
      })
      .subscribe((reservations) => this.reservations.set(reservations));
  }

  formatDateTime(iso: string): string {
    return parseUtcIso(iso).toLocaleString('es-GT', {
      timeZone: GUATEMALA_TIMEZONE,
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  }
}
