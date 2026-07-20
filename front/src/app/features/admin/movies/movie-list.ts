import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { MovieOut } from '../../../core/models';
import { MovieService } from '../../../core/services/movie.service';
import { ToastService } from '../../../shared/components/toast/toast.service';

@Component({
  selector: 'app-movie-list',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './movie-list.html',
  styleUrl: './movie-list.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MovieList {
  private readonly movieService = inject(MovieService);
  private readonly toast = inject(ToastService);

  protected readonly movies = signal<MovieOut[]>([]);
  protected readonly search = signal('');
  protected readonly includeInactive = signal(false);
  protected readonly showForm = signal(false);
  protected readonly editingId = signal<number | null>(null);

  protected readonly filteredMovies = computed(() => {
    const term = this.search().trim().toLowerCase();
    if (!term) return this.movies();
    return this.movies().filter((m) => m.title.toLowerCase().includes(term));
  });

  // --- Formulario "nueva película" ---
  protected newTitle = '';
  protected newDurationMin: number | null = null;
  protected newAgeRating = '';

  // --- Edición inline ---
  protected editTitle = '';
  protected editDurationMin: number | null = null;
  protected editAgeRating = '';

  constructor() {
    this.load();
  }

  private load(): void {
    this.movieService.list(this.includeInactive()).subscribe((movies) => this.movies.set(movies));
  }

  toggleIncludeInactive(): void {
    this.includeInactive.update((v) => !v);
    this.load();
  }

  toggleForm(): void {
    this.showForm.update((v) => !v);
  }

  createMovie(): void {
    if (!this.newTitle || !this.newDurationMin) return;

    this.movieService
      .create({
        title: this.newTitle,
        duration_min: this.newDurationMin,
        age_rating: this.newAgeRating || null,
      })
      .subscribe((movie) => {
        this.movies.update((movies) => [...movies, movie]);
        this.toast.success(`"${movie.title}" creada.`);
        this.newTitle = '';
        this.newDurationMin = null;
        this.newAgeRating = '';
        this.showForm.set(false);
      });
  }

  startEdit(movie: MovieOut): void {
    this.editingId.set(movie.movie_id);
    this.editTitle = movie.title;
    this.editDurationMin = movie.duration_min;
    this.editAgeRating = movie.age_rating ?? '';
  }

  cancelEdit(): void {
    this.editingId.set(null);
  }

  saveEdit(movie: MovieOut): void {
    this.movieService
      .update(movie.movie_id, {
        title: this.editTitle,
        duration_min: this.editDurationMin ?? undefined,
        age_rating: this.editAgeRating || null,
      })
      .subscribe((updated) => {
        this.movies.update((movies) =>
          movies.map((m) => (m.movie_id === updated.movie_id ? updated : m)),
        );
        this.editingId.set(null);
        this.toast.success('Película actualizada.');
      });
  }

  toggleActive(movie: MovieOut): void {
    const action = movie.is_active
      ? this.movieService.disable(movie.movie_id)
      : this.movieService.enable(movie.movie_id);

    action.subscribe((updated) => {
      this.movies.update((movies) =>
        movies.map((m) => (m.movie_id === updated.movie_id ? updated : m)),
      );
      this.toast.success(updated.is_active ? 'Película habilitada.' : 'Película deshabilitada.');
    });
  }
}
