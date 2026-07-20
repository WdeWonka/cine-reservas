import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { RoomOut } from '../../../core/models';
import { RoomService } from '../../../core/services/room.service';
import { RoomLayout, SeatMap } from '../../../shared/components/seat-map/seat-map';
import { ToastService } from '../../../shared/components/toast/toast.service';

@Component({
  selector: 'app-room-list',
  standalone: true,
  imports: [FormsModule, SeatMap],
  templateUrl: './room-list.html',
  styleUrl: './room-list.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RoomList {
  private readonly roomService = inject(RoomService);
  private readonly toast = inject(ToastService);

  protected readonly rooms = signal<RoomOut[]>([]);
  protected readonly search = signal('');
  protected readonly includeInactive = signal(false);
  protected readonly showForm = signal(false);
  protected readonly editingId = signal<number | null>(null);

  protected readonly filteredRooms = computed(() => {
    const term = this.search().trim().toLowerCase();
    if (!term) return this.rooms();
    return this.rooms().filter((r) => r.name.toLowerCase().includes(term));
  });

  protected newName = '';
  protected pendingLayout: RoomLayout | null = null;
  protected editName = '';

  constructor() {
    this.load();
  }

  private load(): void {
    this.roomService.list(this.includeInactive()).subscribe((rooms) => this.rooms.set(rooms));
  }

  toggleIncludeInactive(): void {
    this.includeInactive.update((v) => !v);
    this.load();
  }

  toggleForm(): void {
    this.showForm.update((v) => !v);
  }

  onLayoutChange(layout: RoomLayout): void {
    this.pendingLayout = layout;
  }

  createRoom(): void {
    if (!this.newName || !this.pendingLayout || this.pendingLayout.rowLabels.length === 0) return;

    this.roomService
      .create({
        name: this.newName,
        row_labels: this.pendingLayout.rowLabels,
        seats_per_row: this.pendingLayout.seatsPerRow,
      })
      .subscribe((room) => {
        this.rooms.update((rooms) => [...rooms, room]);
        this.toast.success(`Sala "${room.name}" creada.`);
        this.newName = '';
        this.pendingLayout = null;
        this.showForm.set(false);
      });
  }

  startEdit(room: RoomOut): void {
    this.editingId.set(room.room_id);
    this.editName = room.name;
  }

  cancelEdit(): void {
    this.editingId.set(null);
  }

  saveEdit(room: RoomOut): void {
    this.roomService.update(room.room_id, { name: this.editName }).subscribe((updated) => {
      this.rooms.update((rooms) =>
        rooms.map((r) => (r.room_id === updated.room_id ? updated : r)),
      );
      this.editingId.set(null);
      this.toast.success('Sala actualizada.');
    });
  }

  toggleActive(room: RoomOut): void {
    const action = room.is_active
      ? this.roomService.disable(room.room_id)
      : this.roomService.enable(room.room_id);

    action.subscribe((updated) => {
      this.rooms.update((rooms) =>
        rooms.map((r) => (r.room_id === updated.room_id ? updated : r)),
      );
      this.toast.success(updated.is_active ? 'Sala habilitada.' : 'Sala deshabilitada.');
    });
  }
}
