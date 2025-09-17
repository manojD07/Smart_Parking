import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { AuthService } from '../auth/services/auth.service';
import { User, ChangePasswordRequest } from '../../core/models/user.model';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterModule, ReactiveFormsModule],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <h1 class="h2 mb-4">
            <i class="fas fa-user me-2"></i>
            My Profile
          </h1>
        </div>
      </div>

      <div class="row">
        <!-- Profile Information -->
        <div class="col-lg-8">
          <div class="card mb-4">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-edit me-2"></i>
                Profile Information
              </h5>
            </div>
            <div class="card-body">
              <form [formGroup]="profileForm" (ngSubmit)="updateProfile()">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="firstName" class="form-label">First Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="firstName"
                      formControlName="first_name"
                      [class.is-invalid]="isProfileFieldInvalid('first_name')"
                    />
                    <div class="invalid-feedback" *ngIf="isProfileFieldInvalid('first_name')">
                      <div *ngIf="profileForm.get('first_name')?.errors?.['required']">
                        First name is required
                      </div>
                      <div *ngIf="profileForm.get('first_name')?.errors?.['minlength']">
                        First name must be at least 2 characters
                      </div>
                    </div>
                  </div>

                  <div class="col-md-6 mb-3">
                    <label for="lastName" class="form-label">Last Name</label>
                    <input
                      type="text"
                      class="form-control"
                      id="lastName"
                      formControlName="last_name"
                      [class.is-invalid]="isProfileFieldInvalid('last_name')"
                    />
                    <div class="invalid-feedback" *ngIf="isProfileFieldInvalid('last_name')">
                      <div *ngIf="profileForm.get('last_name')?.errors?.['required']">
                        Last name is required
                      </div>
                      <div *ngIf="profileForm.get('last_name')?.errors?.['minlength']">
                        Last name must be at least 2 characters
                      </div>
                    </div>
                  </div>
                </div>

                <div class="mb-3">
                  <label for="email" class="form-label">Email Address</label>
                  <input
                    type="email"
                    class="form-control"
                    id="email"
                    formControlName="email"
                    [class.is-invalid]="isProfileFieldInvalid('email')"
                  />
                  <div class="invalid-feedback" *ngIf="isProfileFieldInvalid('email')">
                    Please enter a valid email address
                  </div>
                </div>

                <div class="mb-3">
                  <label for="phone" class="form-label">Phone Number (Optional)</label>
                  <input
                    type="tel"
                    class="form-control"
                    id="phone"
                    formControlName="phone"
                    placeholder="+1234567890"
                  />
                </div>

                <div class="alert alert-success" *ngIf="profileSuccessMessage">
                  <i class="fas fa-check-circle me-2"></i>
                  {{ profileSuccessMessage }}
                </div>

                <div class="alert alert-danger" *ngIf="profileErrorMessage">
                  <i class="fas fa-exclamation-circle me-2"></i>
                  {{ profileErrorMessage }}
                </div>

                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                  <button
                    type="button"
                    class="btn btn-outline-secondary"
                    (click)="resetProfileForm()"
                    [disabled]="updatingProfile"
                  >
                    Reset
                  </button>
                  <button
                    type="submit"
                    class="btn btn-primary"
                    [disabled]="profileForm.invalid || updatingProfile"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="updatingProfile"></span>
                    <i class="fas fa-save me-2" *ngIf="!updatingProfile"></i>
                    {{ updatingProfile ? 'Updating...' : 'Update Profile' }}
                  </button>
                </div>
              </form>
            </div>
          </div>

          <!-- Change Password -->
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-lock me-2"></i>
                Change Password
              </h5>
            </div>
            <div class="card-body">
              <form [formGroup]="passwordForm" (ngSubmit)="changePassword()">
                <div class="mb-3">
                  <label for="currentPassword" class="form-label">Current Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="currentPassword"
                    formControlName="current_password"
                    [class.is-invalid]="isPasswordFieldInvalid('current_password')"
                  />
                  <div class="invalid-feedback" *ngIf="isPasswordFieldInvalid('current_password')">
                    Current password is required
                  </div>
                </div>

                <div class="mb-3">
                  <label for="newPassword" class="form-label">New Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="newPassword"
                    formControlName="new_password"
                    [class.is-invalid]="isPasswordFieldInvalid('new_password')"
                  />
                  <div class="invalid-feedback" *ngIf="isPasswordFieldInvalid('new_password')">
                    <div *ngIf="passwordForm.get('new_password')?.errors?.['required']">
                      New password is required
                    </div>
                    <div *ngIf="passwordForm.get('new_password')?.errors?.['minlength']">
                      Password must be at least 8 characters
                    </div>
                    <div *ngIf="passwordForm.get('new_password')?.errors?.['passwordStrength']">
                      Password must contain uppercase, lowercase, number, and special character
                    </div>
                  </div>
                  <div class="form-text">
                    Password must contain: uppercase letter, lowercase letter, number, and special character (!@#$%^&*(),.?\":{{ '{' }}{{ '}' }}|&lt;&gt;)
                  </div>
                </div>

                <div class="mb-3">
                  <label for="confirmPassword" class="form-label">Confirm New Password</label>
                  <input
                    type="password"
                    class="form-control"
                    id="confirmPassword"
                    formControlName="confirm_password"
                    [class.is-invalid]="isPasswordFieldInvalid('confirm_password')"
                  />
                  <div class="invalid-feedback" *ngIf="isPasswordFieldInvalid('confirm_password')">
                    <div *ngIf="passwordForm.get('confirm_password')?.errors?.['required']">
                      Please confirm your new password
                    </div>
                    <div *ngIf="passwordForm.get('confirm_password')?.errors?.['passwordMismatch']">
                      Passwords do not match
                    </div>
                  </div>
                </div>

                <div class="alert alert-success" *ngIf="passwordSuccessMessage">
                  <i class="fas fa-check-circle me-2"></i>
                  {{ passwordSuccessMessage }}
                </div>

                <div class="alert alert-danger" *ngIf="passwordErrorMessage">
                  <i class="fas fa-exclamation-circle me-2"></i>
                  {{ passwordErrorMessage }}
                </div>

                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                  <button
                    type="button"
                    class="btn btn-outline-secondary"
                    (click)="resetPasswordForm()"
                    [disabled]="changingPassword"
                  >
                    Reset
                  </button>
                  <button
                    type="submit"
                    class="btn btn-primary"
                    [disabled]="passwordForm.invalid || changingPassword"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="changingPassword"></span>
                    <i class="fas fa-key me-2" *ngIf="!changingPassword"></i>
                    {{ changingPassword ? 'Changing...' : 'Change Password' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- Profile Summary -->
        <div class="col-lg-4">
          <div class="card mb-4">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-info-circle me-2"></i>
                Account Summary
              </h5>
            </div>
            <div class="card-body text-center" *ngIf="currentUser">
              <!-- Profile Avatar -->
              <div class="mb-3">
                <div class="avatar-lg mx-auto mb-3">
                  <div class="avatar-initials bg-primary text-white">
                    {{ getUserInitials() }}
                  </div>
                </div>
                <h5>{{ currentUser.first_name }} {{ currentUser.last_name }}</h5>
                <p class="text-muted mb-1">{{ currentUser.email }}</p>
                <span class="badge bg-success" *ngIf="!currentUser.is_admin">Regular User</span>
                <span class="badge bg-warning" *ngIf="currentUser.is_admin">Administrator</span>
              </div>

              <!-- Account Stats -->
              <div class="row text-center">
                <div class="col-6">
                  <div class="border-end">
                    <h6 class="text-muted">Total Spent</h6>
                    <h4 class="text-success">\${{ currentUser.total_spent.toFixed(2) || '0.00' }}</h4>
                  </div>
                </div>
                <div class="col-6">
                  <h6 class="text-muted">Member Since</h6>
                  <h6>{{ formatMemberSince(currentUser.created_at) }}</h6>
                </div>
              </div>
            </div>
          </div>

          <!-- Account Actions -->
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-cog me-2"></i>
                Account Actions
              </h5>
            </div>
            <div class="card-body">
              <div class="d-grid gap-2">
                <button class="btn btn-outline-primary" routerLink="/bookings">
                  <i class="fas fa-ticket-alt me-2"></i>
                  View My Bookings
                </button>
                <button class="btn btn-outline-info" routerLink="/parking">
                  <i class="fas fa-search me-2"></i>
                  Find Parking
                </button>
                <button class="btn btn-outline-secondary" routerLink="/dashboard">
                  <i class="fas fa-tachometer-alt me-2"></i>
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .avatar-lg {
      width: 80px;
      height: 80px;
    }

    .avatar-initials {
      width: 100%;
      height: 100%;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 1.5rem;
    }

    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .card-header {
      background-color: #f8f9fc;
      border-bottom: 1px solid #e3e6f0;
    }

    .border-end {
      border-right: 1px solid #e3e6f0 !important;
    }

    .text-success {
      color: #1cc88a !important;
    }
  `]
})
export class ProfileComponent implements OnInit, OnDestroy {
  profileForm: FormGroup;
  passwordForm: FormGroup;
  currentUser: User | null = null;
  
  updatingProfile = false;
  changingPassword = false;
  
  profileSuccessMessage = '';
  profileErrorMessage = '';
  passwordSuccessMessage = '';
  passwordErrorMessage = '';
  
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private authService: AuthService
  ) {
    this.profileForm = this.createProfileForm();
    this.passwordForm = this.createPasswordForm();
  }

  ngOnInit(): void {
    // Get current user and populate form
    this.authService.currentUser$
      .pipe(takeUntil(this.destroy$))
      .subscribe(user => {
        if (user) {
          this.currentUser = user;
          this.populateProfileForm(user);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createProfileForm(): FormGroup {
    return this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      phone: ['']
    });
  }

  private createPasswordForm(): FormGroup {
    return this.fb.group({
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(8), this.passwordValidator]],
      confirm_password: ['', Validators.required]
    }, { validators: this.passwordMatchValidator });
  }

  private populateProfileForm(user: User): void {
    this.profileForm.patchValue({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone: user.phone || ''
    });
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
    const newPassword = form.get('new_password');
    const confirmPassword = form.get('confirm_password');
    
    if (newPassword && confirmPassword && newPassword.value !== confirmPassword.value) {
      confirmPassword.setErrors({ passwordMismatch: true });
    } else {
      confirmPassword?.setErrors(null);
    }
    return null;
  }

  updateProfile(): void {
    if (this.profileForm.valid) {
      this.updatingProfile = true;
      this.profileErrorMessage = '';
      this.profileSuccessMessage = '';

      const profileData = this.profileForm.value;

      this.authService.updateProfile(profileData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (user) => {
            this.currentUser = user;
            this.updatingProfile = false;
            this.profileSuccessMessage = 'Profile updated successfully!';
            
            // Clear success message after 5 seconds
            setTimeout(() => {
              this.profileSuccessMessage = '';
            }, 5000);
          },
          error: (error) => {
            this.profileErrorMessage = error.message || 'Failed to update profile. Please try again.';
            this.updatingProfile = false;
          }
        });
    } else {
      this.markProfileFormTouched();
    }
  }

  changePassword(): void {
    if (this.passwordForm.valid) {
      this.changingPassword = true;
      this.passwordErrorMessage = '';
      this.passwordSuccessMessage = '';

      const passwordData: ChangePasswordRequest = {
        current_password: this.passwordForm.value.current_password,
        new_password: this.passwordForm.value.new_password
      };

      this.authService.changePassword(passwordData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            this.changingPassword = false;
            this.passwordSuccessMessage = 'Password changed successfully!';
            this.resetPasswordForm();
            
            // Clear success message after 5 seconds
            setTimeout(() => {
              this.passwordSuccessMessage = '';
            }, 5000);
          },
          error: (error) => {
            this.passwordErrorMessage = error.message || 'Failed to change password. Please try again.';
            this.changingPassword = false;
          }
        });
    } else {
      this.markPasswordFormTouched();
    }
  }

  resetProfileForm(): void {
    if (this.currentUser) {
      this.populateProfileForm(this.currentUser);
      this.profileErrorMessage = '';
      this.profileSuccessMessage = '';
    }
  }

  resetPasswordForm(): void {
    this.passwordForm.reset();
    this.passwordErrorMessage = '';
    this.passwordSuccessMessage = '';
  }

  isProfileFieldInvalid(fieldName: string): boolean {
    const field = this.profileForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  isPasswordFieldInvalid(fieldName: string): boolean {
    const field = this.passwordForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markProfileFormTouched(): void {
    Object.keys(this.profileForm.controls).forEach(key => {
      const control = this.profileForm.get(key);
      control?.markAsTouched();
    });
  }

  private markPasswordFormTouched(): void {
    Object.keys(this.passwordForm.controls).forEach(key => {
      const control = this.passwordForm.get(key);
      control?.markAsTouched();
    });
  }

  getUserInitials(): string {
    if (!this.currentUser) return 'U';
    return (this.currentUser.first_name.charAt(0) + this.currentUser.last_name.charAt(0)).toUpperCase();
  }

  formatMemberSince(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short' 
    });
  }
}
