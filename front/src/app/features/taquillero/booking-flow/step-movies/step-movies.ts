import { ChangeDetectionStrategy, Component, inject, output, signal } from '@angular/core';

import { MovieOut } from '../../../../core/models';
import { MovieService } from '../../../../core/services/movie.service';

@Component({
  selector: 'app-step-movies',
  standalone: true,
  templateUrl: './step-movies.html',
  styleUrl: './step-movies.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepMovies {
  private readonly movieService = inject(MovieService);

  protected readonly movies = signal<MovieOut[]>([]);
  readonly movieSelected = output<MovieOut>();

  constructor() {
    this.movieService.list(false).subscribe((movies) => this.movies.set(movies));
  }
}
