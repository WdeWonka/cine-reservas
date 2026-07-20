import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import { MovieFunctionOut, MovieOut, TicketOut } from '../../../../core/models';
import { GUATEMALA_TIMEZONE, parseUtcIso } from '../../../../core/utils/datetime.util';
import { QrCode } from '../../../../shared/components/qr-code/qr-code';
import { CustomerInfo } from '../step-customer/step-customer';

@Component({
  selector: 'app-step-tickets',
  standalone: true,
  imports: [QrCode],
  templateUrl: './step-tickets.html',
  styleUrl: './step-tickets.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepTickets {
  readonly movie = input.required<MovieOut>();
  readonly fn = input.required<MovieFunctionOut>();
  readonly customer = input.required<CustomerInfo>();
  readonly tickets = input.required<TicketOut[]>();
  readonly startOver = output<void>();

  formatDateTime(iso: string): string {
    return parseUtcIso(iso).toLocaleString('es-GT', {
      timeZone: GUATEMALA_TIMEZONE,
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  }
}
