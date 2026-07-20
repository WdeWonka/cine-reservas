import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { MovieFunctionOut, MovieOut, ReservationOut, TicketOut } from '../../../core/models';
import { AuthService } from '../../../core/services/auth.service';
import { ReservationService } from '../../../core/services/reservation.service';
import { StepCustomer, CustomerInfo } from './step-customer/step-customer';
import { StepDateFunctions } from './step-date-functions/step-date-functions';
import { StepMovies } from './step-movies/step-movies';
import { StepPayment } from './step-payment/step-payment';
import { StepSeats } from './step-seats/step-seats';
import { StepTicketCount } from './step-ticket-count/step-ticket-count';
import { StepTickets } from './step-tickets/step-tickets';

type WizardStep = 'movie' | 'date' | 'ticket-count' | 'seats' | 'customer' | 'payment' | 'tickets';

@Component({
  selector: 'app-booking-flow',
  standalone: true,
  imports: [
    RouterLink,
    StepMovies,
    StepDateFunctions,
    StepTicketCount,
    StepSeats,
    StepCustomer,
    StepPayment,
    StepTickets,
  ],
  templateUrl: './booking-flow.html',
  styleUrl: './booking-flow.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BookingFlow {
  private readonly reservationService = inject(ReservationService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  // MovieFunctionService no se usa directo acá: cada step trae lo suyo.

  protected readonly step = signal<WizardStep>('movie');

  protected readonly selectedMovie = signal<MovieOut | null>(null);
  protected readonly selectedFunction = signal<MovieFunctionOut | null>(null);
  protected readonly ticketCount = signal(1);
  protected readonly selectedSeatIds = signal<number[]>([]);
  protected readonly customer = signal<CustomerInfo | null>(null);
  protected readonly tickets = signal<TicketOut[]>([]);
  protected readonly submitting = signal(false);

  onMovieSelected(movie: MovieOut): void {
    this.selectedMovie.set(movie);
    this.step.set('date');
  }

  onFunctionSelected(fn: MovieFunctionOut): void {
    this.selectedFunction.set(fn);
    this.step.set('ticket-count');
  }

  onTicketCountConfirmed(count: number): void {
    this.ticketCount.set(count);
    this.step.set('seats');
  }

  onSeatsSelected(seatIds: number[]): void {
    this.selectedSeatIds.set(seatIds);
    this.step.set('customer');
  }

  onCustomerConfirmed(customer: CustomerInfo): void {
    this.customer.set(customer);
    this.step.set('payment');
  }

  onPaymentConfirmed(): void {
    const fn = this.selectedFunction();
    const customer = this.customer();
    if (!fn || !customer || this.submitting()) return;

    this.submitting.set(true);

    // POST /reservations, seguido de inmediato por el PATCH a "Confirmada"
    // — no hay un endpoint separado para generar tickets, los genera el
    // backend como efecto de esa transición.
    this.reservationService
      .create({
        function_id: fn.function_id,
        seat_ids: this.selectedSeatIds(),
        customer_name: customer.name,
        customer_email: customer.email,
        customer_phone: customer.phone || null,
      })
      .subscribe({
        next: (reservation) => this.confirmAndFetchTickets(reservation.reservation_id),
        error: () => this.submitting.set(false),
      });
  }

  private confirmAndFetchTickets(reservationId: number): void {
    this.reservationService
      .changeStatus(reservationId, { new_status: 'Confirmada' })
      .subscribe({
        next: () => {
          this.reservationService.getTickets(reservationId).subscribe((tickets) => {
            this.tickets.set(tickets);
            this.submitting.set(false);
            this.step.set('tickets');
          });
        },
        error: () => this.submitting.set(false),
      });
  }

  startOver(): void {
    this.step.set('movie');
    this.selectedMovie.set(null);
    this.selectedFunction.set(null);
    this.ticketCount.set(1);
    this.selectedSeatIds.set([]);
    this.customer.set(null);
    this.tickets.set([]);
  }

  goBack(): void {
    const order: WizardStep[] = ['movie', 'date', 'ticket-count', 'seats', 'customer', 'payment'];
    const idx = order.indexOf(this.step());
    if (idx > 0) this.step.set(order[idx - 1]);
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
