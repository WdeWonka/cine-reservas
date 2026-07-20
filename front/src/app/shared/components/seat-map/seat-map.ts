import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

export type SeatMapMode = 'layout' | 'selection';

/** Forma interna del componente — desacoplada del wire format de la API.
 *  El mapeo SeatAvailabilityOut -> SeatMapSeat lo hace el componente padre
 *  (booking-flow), no este componente, para que sea reusable sin conocer
 *  el endpoint del que vinieron los datos. */
export interface SeatMapSeat {
  seatId: number;
  rowLabel: string;
  seatNumber: number;
  seatLabel: string;
  ocupado: boolean;
}

export interface RoomLayout {
  rowLabels: string[];
  seatsPerRow: number;
}

@Component({
  selector: 'app-seat-map',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './seat-map.html',
  styleUrl: './seat-map.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SeatMap {
  // --- Común a ambos modos ---
  readonly mode = input.required<SeatMapMode>();

  // --- Modo "selection" (usado por el taquillero) ---
  readonly seats = input<SeatMapSeat[]>([]);
  readonly requiredSeatCount = input<number>(1);
  readonly selectionChange = output<number[]>();

  // --- Modo "layout" (usado por el admin al crear una sala) ---
  readonly initialLayout = input<RoomLayout | null>(null);
  readonly layoutChange = output<RoomLayout>();

  protected readonly selectedSeatIds = signal<Set<number>>(new Set());
  protected readonly rowLabels = signal<string[]>([]);
  protected readonly seatsPerRow = signal<number>(5);
  protected newRowLabel = '';

  readonly isSelectionComplete = computed(
    () => this.selectedSeatIds().size === this.requiredSeatCount(),
  );

  protected readonly seatsByRow = computed(() => {
    const groups = new Map<string, SeatMapSeat[]>();
    for (const seat of this.seats()) {
      const group = groups.get(seat.rowLabel) ?? [];
      group.push(seat);
      groups.set(seat.rowLabel, group);
    }
    return Array.from(groups.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([rowLabel, seats]) => ({
        rowLabel,
        seats: seats.sort((a, b) => a.seatNumber - b.seatNumber),
      }));
  });

  protected readonly layoutPreviewRows = computed(() =>
    this.rowLabels().map((label) => ({
      label,
      seatNumbers: Array.from({ length: this.seatsPerRow() }, (_, i) => i + 1),
    })),
  );

  constructor() {
    const initial = this.initialLayout();
    if (initial) {
      this.rowLabels.set(initial.rowLabels);
      this.seatsPerRow.set(initial.seatsPerRow);
    }
  }

  toggleSeat(seat: SeatMapSeat): void {
    if (seat.ocupado) return;

    const current = new Set(this.selectedSeatIds());
    if (current.has(seat.seatId)) {
      current.delete(seat.seatId);
    } else {
      if (current.size >= this.requiredSeatCount()) return;
      current.add(seat.seatId);
    }
    this.selectedSeatIds.set(current);
    this.selectionChange.emit(Array.from(current));
  }

  isSelected(seat: SeatMapSeat): boolean {
    return this.selectedSeatIds().has(seat.seatId);
  }

  addRow(): void {
    const label = this.newRowLabel.trim().toUpperCase();
    if (!label || label.length !== 1 || this.rowLabels().includes(label)) return;

    this.rowLabels.update((rows) => [...rows, label].sort());
    this.newRowLabel = '';
    this.emitLayout();
  }

  removeRow(label: string): void {
    this.rowLabels.update((rows) => rows.filter((r) => r !== label));
    this.emitLayout();
  }

  setSeatsPerRow(count: number): void {
    if (count < 1) return;
    this.seatsPerRow.set(count);
    this.emitLayout();
  }

  private emitLayout(): void {
    this.layoutChange.emit({
      rowLabels: this.rowLabels(),
      seatsPerRow: this.seatsPerRow(),
    });
  }
}
