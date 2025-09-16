import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth.service';
import { take } from 'rxjs/operators';

@Component({
  selector: 'app-dashboard-redirect',
  standalone: true,
  template: `
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-6 text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-3">Redirecting to dashboard...</p>
        </div>
      </div>
    </div>
  `
})
export class DashboardRedirectComponent implements OnInit {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$
      .pipe(take(1))
      .subscribe(user => {
        if (user) {
          if (user.is_admin) {
            // Redirect admins to admin dashboard
            console.log('Admin user detected, redirecting to /admin/dashboard');
            this.router.navigate(['/admin/dashboard']);
          } else {
            // Load regular user dashboard
            console.log('Regular user detected, loading user dashboard');
            this.router.navigate(['/user-dashboard']);
          }
        } else {
          // Not authenticated, redirect to login
          this.router.navigate(['/auth/login']);
        }
      });
  }
}
