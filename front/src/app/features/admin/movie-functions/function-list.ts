import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieFunctionOut, MovieOut, RoomOut } from '../../../core/models';
import { MovieFunctionService } from '../../../core/services/movie-function.service';
import { MovieService } from '../../../core/services/movie.service';
import { RoomService } from '../../../core/services/room.service';
import { GUATEMALA_TIMEZONE, guatemalaWallClockToUtcIso, parseUtcIso } from '../../../core/utils/datetime.util';
import { ToastService } from '../../../shared/components/toast/toast.service';

@Component({
  selector: 'app-function-list',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './function-list.html',
  styleUrl: './function-list.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FunctionList {
  private readonly functionService = inject(MovieFunctionService);
  private readonly movieService = inject(MovieService);
  private readonly roomService = inject(RoomService);
  private readonly toast = inject(ToastService);

  protected readonly functions = signal<MovieFunctionOut[]>([]);
  protected readonly movies = signal<MovieOut[]>([]);
  protected readonly rooms = signal<RoomOut[]>([]);
  protected readonly includeInactive = signal(false);
  protected readonly showForm = signal(false);

  private readonly movieTitleById = computed(() => {
    const map = new Map<number, string>();
    for (const movie of this.movies()) map.set(movie.movie_id, movie.title);
    return map;
  });

  private readonly roomNameById = computed(() => {
    const map = new Map<number, string>();
    for (const room of this.rooms()) map.set(room.room_id, room.name);
    return map;
  });

  // GET /movie-functions no trae movie_title/room_name (solo /report lo
  // hace, y por función individual) — cruzamos contra las listas ya
  // cargadas de Movies/Rooms para armar la fila de la tabla.
  protected readonly rows = computed(() =>
    this.functions().map((fn) => ({
      fn,
      movieTitle: this.movieTitleById().get(fn.movie_id) ?? `#${fn.movie_id}`,
      roomName: this.roomNameById().get(fn.room_id) ?? `#${fn.room_id}`,
    })),
  );

  // --- Formulario "nueva función" ---
  protected newMovieId: number | null = null;
  protected newRoomId: number | null = null;
  protected newDate = '';
  protected newTime = '';

  constructor() {
    this.movieService.list().subscribe((movies) => this.movies.set(movies));
    this.roomService.list().subscribe((rooms) => this.rooms.set(rooms));
    this.load();
  }

  private load(): void {
    this.functionService
      .list({ includeInactive: this.includeInactive() })
      .subscribe((functions) => this.functions.set(functions));
  }

  toggleIncludeInactive(): void {
    this.includeInactive.update((v) => !v);
    this.load();
  }

  toggleForm(): void {
    this.showForm.update((v) => !v);
  }

  formatDateTime(iso: string): string {
    return parseUtcIso(iso).toLocaleString('es-GT', {
      timeZone: GUATEMALA_TIMEZONE,
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  }

  createFunction(): void {
    if (!this.newMovieId || !this.newRoomId || !this.newDate || !this.newTime) return;

    // El <input> de fecha/hora se piensa en hora de Guatemala (la que
    // tipea el taquillero/admin), no en la del browser ni en UTC — hay
    // que convertirla antes de mandarla, no asumir que ya está en UTC.
    const wallClock = new Date(`${this.newDate}T${this.newTime}:00`);
    const startDatetime = guatemalaWallClockToUtcIso(wallClock);

    // El 409 de solapamiento (si lo hay) lo muestra tal cual el
    // error.interceptor global — no lo revalidamos acá.
    this.functionService
      .create({ movie_id: this.newMovieId, room_id: this.newRoomId, start_datetime: startDatetime })
      .subscribe((fn) => {
        this.functions.update((functions) => [...functions, fn]);
        this.toast.success('Función creada.');
        this.newMovieId = null;
        this.newRoomId = null;
        this.newDate = '';
        this.newTime = '';
        this.showForm.set(false);
      });
  }

  toggleActive(fn: MovieFunctionOut): void {
    const action = fn.is_active
      ? this.functionService.disable(fn.function_id)
      : this.functionService.enable(fn.function_id);

    action.subscribe((updated) => {
      this.functions.update((functions) =>
        functions.map((f) => (f.function_id === updated.function_id ? updated : f)),
      );
      this.toast.success(updated.is_active ? 'Función habilitada.' : 'Función deshabilitada.');
    });
  }
}
