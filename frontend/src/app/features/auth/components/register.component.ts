import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { UserRegistration } from '../../../core/models/user.model';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
          <div class="card shadow">
            <div class="card-body p-4">
              <div class="text-center mb-4">
                <h2 class="text-primary-custom">Create Account</h2>
                <p class="text-muted">Join Smart Parking today</p>
              </div>

              <form [formGroup]="registerForm" (ngSubmit)="onSubmit()">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="first_name" class="form-label">First Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="first_name"
                      formControlName="first_name"
                      [class.is-invalid]="isFieldInvalid('first_name')"
                      placeholder="First name"
                    />
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('first_name')">
                      <div *ngIf="registerForm.get('first_name')?.errors?.['required']">
                        First name is required
                      </div>
                      <div *ngIf="registerForm.get('first_name')?.errors?.['minlength']">
                        First name must be at least 2 characters
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6 mb-3">
                    <label for="last_name" class="form-label">Last Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="last_name"
                      formControlName="last_name"
                      [class.is-invalid]="isFieldInvalid('last_name')"
                      placeholder="Last name"
                    />
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('last_name')">
                      <div *ngIf="registerForm.get('last_name')?.errors?.['required']">
                        Last name is required
                      </div>
                      <div *ngIf="registerForm.get('last_name')?.errors?.['minlength']">
                        Last name must be at least 2 characters
                      </div>
                    </div>
                  </div>
                </div>

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
                    <div *ngIf="registerForm.get('email')?.errors?.['required']">
                      Email is required
                    </div>
                    <div *ngIf="registerForm.get('email')?.errors?.['email']">
                      Please enter a valid email
                    </div>
                  </div>
                </div>

                <div class="mb-3">
                  <label for="phone" class="form-label">Phone Number (Optional)</label>
                  <input
                    type="tel"
                    class="form-control"
                    id="phone"
                    formControlName="phone"
                    placeholder="Phone number"
                  />
                </div>

                <div class="mb-3">
                  <label for="password" class="form-label">Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="password"
                    formControlName="password"
                    [class.is-invalid]="isFieldInvalid('password')"
                    placeholder="Create a password"
                  />
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('password')">
                    <div *ngIf="registerForm.get('password')?.errors?.['required']">
                      Password is required
                    </div>
                    <div *ngIf="registerForm.get('password')?.errors?.['minlength']">
                      Password must be at least 8 characters
                    </div>
                    <div *ngIf="registerForm.get('password')?.errors?.['passwordStrength']">
                      Password must contain uppercase, lowercase, number, and special character
                    </div>
                  </div>
                  <div class="form-text">
                    Password must contain at least 8 characters with uppercase, lowercase, numbers, and special characters
                  </div>
                </div>

                <div class="mb-3">
                  <label for="confirmPassword" class="form-label">Confirm Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="confirmPassword"
                    formControlName="confirmPassword"
                    [class.is-invalid]="isFieldInvalid('confirmPassword')"
                    placeholder="Confirm your password"
                  />
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('confirmPassword')">
                    <div *ngIf="registerForm.get('confirmPassword')?.errors?.['required']">
                      Please confirm your password
                    </div>
                    <div *ngIf="registerForm.get('confirmPassword')?.errors?.['passwordMismatch']">
                      Passwords do not match
                    </div>
                  </div>
                </div>

                <div class="alert alert-danger" *ngIf="errorMessage">
                  {{ errorMessage }}
                </div>

                <div class="alert alert-success" *ngIf="successMessage">
                  {{ successMessage }}
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
                  {{ loading ? 'Creating Account...' : 'Create Account' }}
                </button>
              </form>

              <div class="text-center">
                <p class="mb-0">
                  Already have an account?
                  <a routerLink="/auth/login" class="text-primary">Sign in</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class RegisterComponent implements OnDestroy {
  registerForm: FormGroup;
  loading = false;
  errorMessage = '';
  successMessage = '';
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      password: ['', [Validators.required, Validators.minLength(8), this.passwordValidator]],
      confirmPassword: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  passwordValidator(control: any) {
    const value = control.value;
    if (!value) return null;
    
    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumeric = /[0-9]/.test(value);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);
    
    const valid = hasUpperCase && hasLowerCase && hasNumeric && hasSpecialChar;
    
    if (!valid) {
      return { passwordStrength: true };
    }
    return null;
  }

  passwordMatchValidator(form: FormGroup) {
    const password = form.get('password');
    const confirmPassword = form.get('confirmPassword');
    
    if (password && confirmPassword && password.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
    } else {
      confirmPassword?.setErrors(null);
    }
    return null;
  }

  onSubmit(): void {
    if (this.registerForm.valid) {
      this.loading = true;
      this.errorMessage = '';
      this.successMessage = '';

      const { confirmPassword, ...userData }: UserRegistration & { confirmPassword: string } = this.registerForm.value;

      this.authService
        .register(userData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.successMessage = 'Account created successfully! Redirecting to login...';
            setTimeout(() => {
              this.router.navigate(['/auth/login']);
            }, 2000);
          },
          error: (error) => {
            this.errorMessage = error.message || 'Registration failed. Please try again.';
            this.loading = false;
          }
        });
    } else {
      this.markFormGroupTouched();
    }
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.registerForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markFormGroupTouched(): void {
    Object.keys(this.registerForm.controls).forEach(key => {
      const control = this.registerForm.get(key);
      control?.markAsTouched();
    });
  }
}
