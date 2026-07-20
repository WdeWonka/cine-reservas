import { ChangeDetectionStrategy, Component, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

export interface CustomerInfo {
  name: string;
  email: string;
  phone: string;
}

@Component({
  selector: 'app-step-customer',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './step-customer.html',
  styleUrl: './step-customer.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class StepCustomer {
  readonly customerConfirmed = output<CustomerInfo>();

  protected name = '';
  protected email = '';
  protected phone = '';

  confirm(): void {
    if (!this.name || !this.email) return;
    this.customerConfirmed.emit({ name: this.name, email: this.email, phone: this.phone });
  }
}
