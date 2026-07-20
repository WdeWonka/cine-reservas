import { ChangeDetectionStrategy, Component, computed, inject, input, OnInit, output, signal } from '@angular/core';

import { MovieFunctionService } from '../../../../core/services/movie-function.service';
import { SeatMap, SeatMapSeat } from '../../../../shared/components/seat-map/seat-map';

@Component({
  selector: 'app-step-seats',
  standalone: true,
  imports: [SeatMap],
  templateUrl: './step-seats.html',
  styleUrl: './step-seats.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepSeats implements OnInit {
  private readonly functionService = inject(MovieFunctionService);

  readonly functionId = input.required<number>();
  readonly requiredSeatCount = input.required<number>();
  readonly seatsSelected = output<number[]>();

  protected readonly seats = signal<SeatMapSeat[]>([]);
  protected readonly selection = signal<number[]>([]);

  protected readonly isComplete = computed(
    () => this.selection().length === this.requiredSeatCount(),
  );

  ngOnInit(): void {
    // Los required input signals recién quedan garantizados con valor a
    // partir de ngOnInit, no en el constructor.
    this.functionService.getSeats(this.functionId()).subscribe((seats) => {
      this.seats.set(
        seats.map((s) => ({
          seatId: s.seat_id,
          rowLabel: s.row_label,
          seatNumber: s.seat_number,
          seatLabel: s.seat_label,
          ocupado: s.ocupado,
        })),
      );
    });
  }

  onSelectionChange(seatIds: number[]): void {
    this.selection.set(seatIds);
  }

  confirm(): void {
    if (this.isComplete()) {
      this.seatsSelected.emit(this.selection());
    }
  }
}
