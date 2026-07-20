import { ChangeDetectionStrategy, Component, computed, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieFunctionOut, MovieOut } from '../../../../core/models';
import { MovieFunctionService } from '../../../../core/services/movie-function.service';
import {
  GUATEMALA_TIMEZONE,
  guatemalaDayUtcRange,
  parseUtcIso,
  todayInGuatemala,
} from '../../../../core/utils/datetime.util';

@Component({
  selector: 'app-step-date-functions',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './step-date-functions.html',
  styleUrl: './step-date-functions.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepDateFunctions {
  private readonly functionService = inject(MovieFunctionService);

  readonly movie = input.required<MovieOut>();
  readonly functionSelected = output<MovieFunctionOut>();

  protected readonly selectedDate = signal(todayInGuatemala());
  protected readonly allFunctions = signal<MovieFunctionOut[]>([]);

  /**
   * Filtro autoritativo: el rango UTC de "hoy en Guatemala" puede caer en
   * dos días calendario UTC distintos (Guatemala es UTC-6), así que NO
   * usamos ?date= del backend (que filtra por día calendario UTC) para
   * esto — traemos todas las funciones activas una sola vez y filtramos
   * acá por película + el rango UTC real calculado con Intl.
   */
  protected readonly functionsForDay = computed(() => {
    const { start, end } = guatemalaDayUtcRange(this.selectedDate());
    const movieId = this.movie().movie_id;

    return this.allFunctions()
      .filter((fn) => fn.movie_id === movieId)
      .filter((fn) => {
        const startsAt = parseUtcIso(fn.start_datetime);
        return startsAt >= start && startsAt < end;
      })
      .sort((a, b) => a.start_datetime.localeCompare(b.start_datetime));
  });

  constructor() {
    this.functionService.list().subscribe((functions) => this.allFunctions.set(functions));
  }

  formatTime(iso: string): string {
    return parseUtcIso(iso).toLocaleTimeString('es-GT', {
      timeZone: GUATEMALA_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
