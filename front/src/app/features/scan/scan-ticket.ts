import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ScanResultOut } from '../../core/models';
import { TicketService } from '../../core/services/ticket.service';

@Component({
  selector: 'app-scan-ticket',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './scan-ticket.html',
  styleUrl: './scan-ticket.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScanTicket {
  private readonly ticketService = inject(TicketService);

  protected ticketCode = '';
  protected readonly result = signal<ScanResultOut | null>(null);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly scanning = signal(false);

  scan(): void {
    if (!this.ticketCode || this.scanning()) return;

    this.scanning.set(true);
    this.result.set(null);
    this.errorMessage.set(null);

    this.ticketService.scan({ ticket_code: this.ticketCode }).subscribe({
      next: (result) => {
        this.result.set(result);
        this.scanning.set(false);
        this.ticketCode = '';
      },
      error: (err) => {
        // El toast global ya avisa el error; acá lo dejamos también fijo
        // en pantalla (no un mensaje genérico) para que el operador lo
        // vea claramente sin que se le escape entre reservas.
        this.errorMessage.set(
          typeof err.error?.detail === 'string' ? err.error.detail : 'No se pudo procesar el ticket.',
        );
        this.scanning.set(false);
      },
    });
  }

  seatLabels(result: ScanResultOut): string {
    return result.tickets.map((t) => t.seat_label).join(', ');
  }
}
