import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';

@Component({
  selector: 'app-step-ticket-count',
  standalone: true,
  templateUrl: './step-ticket-count.html',
  styleUrl: './step-ticket-count.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepTicketCount {
  readonly initialCount = input<number>(1);
  readonly countConfirmed = output<number>();

  protected readonly count = signal(this.initialCount());

  increment(): void {
    this.count.update((c) => c + 1);
  }

  decrement(): void {
    this.count.update((c) => Math.max(1, c - 1));
  }

  confirm(): void {
    this.countConfirmed.emit(this.count());
  }
}
