import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected username = '';
  protected password = '';
  protected readonly loading = signal(false);

  submit(): void {
    if (!this.username || !this.password || this.loading()) return;

    this.loading.set(true);
    this.auth.login(this.username, this.password).subscribe({
      next: () => {
        this.auth.me().subscribe({
          next: (user) => {
            this.loading.set(false);
            this.router.navigate([user.role === 'admin' ? '/admin' : '/taquillero']);
          },
          error: () => this.loading.set(false),
        });
      },
      error: () => this.loading.set(false),
    });
  }
}
