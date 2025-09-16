import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { UserLogin } from '../../../core/models/user.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
          <div class="card shadow">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <h2 class="text-primary-custom">Welcome Back</h2>
                <p class="text-muted">Sign in to your account</p>
              </div>

              <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
                <div class="mb-3">
                  <label for="email" class="form-label">Email</label>
                  <input
                    type="email"
                    class="form-control"
                    id="email"
                    formControlName="email"
                    [class.is-invalid]="isFieldInvalid('email')"
                    placeholder="Enter your email"
                  />
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('email')">
                    <div *ngIf="loginForm.get('email')?.errors?.['required']">
                      Email is required
                    </div>
                    <div *ngIf="loginForm.get('email')?.errors?.['email']">
                      Please enter a valid email
                    </div>
                  </div>
                </div>

                <div class="mb-3">
                  <label for="password" class="form-label">Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    formControlName="password"
                    [class.is-invalid]="isFieldInvalid('password')"
                    placeholder="Enter your password"
                  />
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('password')">
                    Password is required
                  </div>
                </div>

                <div class="alert alert-danger" *ngIf="errorMessage">
                  {{ errorMessage }}
                </div>

                <button
                  type="submit"
                  class="btn btn-primary w-100 mb-3"
                  [disabled]="loading"
                >
                  <span
                    class="spinner-border spinner-border-sm me-2"
                    *ngIf="loading"
                  ></span>
                  {{ loading ? 'Signing in...' : 'Sign In' }}
                </button>
              </form>

              <div class="text-center">
                <p class="mb-0">
                  Don't have an account?
                  <a routerLink="/auth/register" class="text-primary">Sign up</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class LoginComponent implements OnDestroy {
  loginForm: FormGroup;
  loading = false;
  errorMessage = '';
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSubmit(): void {
    if (this.loginForm.valid) {
      this.loading = true;
      this.errorMessage = '';

      const credentials: UserLogin = this.loginForm.value;

        this.authService
          .login(credentials)
          .pipe(takeUntil(this.destroy$))
          .subscribe({
            next: () => {
              // Get the current user and redirect based on role
              const currentUser = this.authService.currentUser;
              if (currentUser?.is_admin) {
                this.router.navigate(['/admin/dashboard']);
              } else {
                const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/user-dashboard';
                this.router.navigate([returnUrl]);
              }
            },
          error: (error) => {
            console.error('Login error:', error);
            this.errorMessage = error.message || 'Login failed. Please try again.';
            this.loading = false;
          }
        });
    } else {
      this.markFormGroupTouched();
    }
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.loginForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markFormGroupTouched(): void {
    Object.keys(this.loginForm.controls).forEach(key => {
      const control = this.loginForm.get(key);
      control?.markAsTouched();
    });
  }
}
