import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';

import { MovieFunctionOut, MovieOut } from '../../../../core/models';
import { GUATEMALA_TIMEZONE, parseUtcIso } from '../../../../core/utils/datetime.util';
import { CustomerInfo } from '../step-customer/step-customer';

@Component({
  selector: 'app-step-payment',
  standalone: true,
  templateUrl: './step-payment.html',
  styleUrl: './step-payment.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepPayment {
  readonly movie = input.required<MovieOut>();
  readonly fn = input.required<MovieFunctionOut>();
  readonly seatCount = input.required<number>();
  readonly customer = input.required<CustomerInfo>();
  readonly submitting = input<boolean>(false);
  readonly paymentConfirmed = output<void>();

  formatDateTime(iso: string): string {
    return parseUtcIso(iso).toLocaleString('es-GT', {
      timeZone: GUATEMALA_TIMEZONE,
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  }
}
