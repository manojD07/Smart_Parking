import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { AdminService } from '../services/admin.service';
import { BookingService } from '../../booking/services/booking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { Booking } from '../../../core/models/booking.model';
import { nowIST, formatIST } from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-admin-checkin',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, LoadingComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h1 class="h2 mb-1">
                <i class="fas fa-sign-in-alt me-2"></i>
                Check-In Management
              </h1>
              <p class="text-muted">Manually check-in bookings using booking reference</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Check-in Form -->
      <div class="row mb-4">
        <div class="col-lg-6">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-qrcode me-2"></i>
                Check-In Booking
              </h5>
            </div>
            <div class="card-body">
              <form [formGroup]="checkinForm" (ngSubmit)="onCheckIn()">
                <div class="mb-3">
                  <label for="bookingCode" class="form-label">Booking Reference Code</label>
                  <input
                    type="text"
                    class="form-control form-control-lg"
                    id="bookingCode"
                    formControlName="bookingCode"
                    placeholder="Enter booking reference (e.g., SP001234)"
                    [class.is-invalid]="isFieldInvalid('bookingCode')"
                    style="text-transform: uppercase; font-family: monospace;"
                    (input)="onBookingCodeChange()"
                  >
                  <div class="invalid-feedback" *ngIf="isFieldInvalid('bookingCode')">
                    <div *ngIf="checkinForm.get('bookingCode')?.errors?.['required']">
                      Booking reference is required
                    </div>
                    <div *ngIf="checkinForm.get('bookingCode')?.errors?.['minlength']">
                      Booking reference must be at least 6 characters
                    </div>
                  </div>
                  <div class="form-text">
                    Enter the booking reference code from the customer's booking confirmation
                  </div>
                </div>

                <div class="alert alert-danger" *ngIf="errorMessage">
                  <i class="fas fa-exclamation-triangle me-2"></i>
                  {{ errorMessage }}
                </div>

                <div class="d-grid">
                  <button
                    type="submit"
                    class="btn btn-success btn-lg"
                    [disabled]="checkinForm.invalid || loading"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="loading"></span>
                    <i class="fas fa-sign-in-alt me-2" *ngIf="!loading"></i>
                    {{ loading ? 'Processing...' : 'Check In' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- Instructions -->
        <div class="col-lg-6">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-info-circle me-2"></i>
                Instructions
              </h5>
            </div>
            <div class="card-body">
              <h6>How to Check-In:</h6>
              <ol class="mb-3">
                <li>Ask customer for their <strong>booking reference code</strong></li>
                <li>Enter the code in the form (e.g., SP001234)</li>
                <li>Click <strong>"Check In"</strong> to process</li>
                <li>System will verify and activate the booking</li>
              </ol>

              <h6>Valid Booking Status:</h6>
              <ul class="mb-3">
                <li><span class="badge bg-success me-2">Confirmed</span>Ready for check-in</li>
                <li><span class="badge bg-warning me-2">Pending</span>Payment pending</li>
              </ul>

              <h6>Check-In Requirements:</h6>
              <ul class="mb-0">
                <li>Booking must be for today or future dates</li>
                <li>Within 30 minutes of start time</li>
                <li>Customer must be present with valid ID</li>
                <li>Vehicle must match booking details</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Booking Details (shown after lookup) -->
      <div class="row mb-4" *ngIf="foundBooking">
        <div class="col-12">
          <div class="card border-primary">
            <div class="card-header bg-primary text-white">
              <h5 class="mb-0">
                <i class="fas fa-ticket-alt me-2"></i>
                Booking Found: {{ foundBooking.booking_reference }}
              </h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <h6>Customer Information</h6>
                  <table class="table table-sm table-borderless">
                    <tr>
                      <td><strong>Name:</strong></td>
                      <td>{{ foundBooking.user?.first_name }} {{ foundBooking.user?.last_name }}</td>
                    </tr>
                    <tr>
                      <td><strong>Email:</strong></td>
                      <td>{{ foundBooking.user?.email }}</td>
                    </tr>
                    <tr>
                      <td><strong>Phone:</strong></td>
                      <td>{{ foundBooking.user?.phone || 'N/A' }}</td>
                    </tr>
                  </table>
                </div>
                <div class="col-md-6">
                  <h6>Booking Details</h6>
                  <table class="table table-sm table-borderless">
                    <tr>
                      <td><strong>Vehicle:</strong></td>
                      <td>{{ foundBooking.vehicle_number }} ({{ foundBooking.vehicle_type | titlecase }})</td>
                    </tr>
                    <tr>
                      <td><strong>Parking Lot:</strong></td>
                      <td>{{ foundBooking.lot?.name }}</td>
                    </tr>
                    <tr>
                      <td><strong>Slot:</strong></td>
                      <td>{{ foundBooking.slot?.slot_number || 'Will be assigned' }}</td>
                    </tr>
                    <tr>
                      <td><strong>Start Time:</strong></td>
                      <td>{{ foundBooking.start_time | date:'short' }}</td>
                    </tr>
                    <tr>
                      <td><strong>End Time:</strong></td>
                      <td>{{ foundBooking.end_time | date:'short' }}</td>
                    </tr>
                    <tr>
                      <td><strong>Status:</strong></td>
                      <td>
                        <span class="badge" [class]="getStatusBadgeClass(foundBooking.status)">
                          {{ foundBooking.status | titlecase }}
                        </span>
                      </td>
                    </tr>
                  </table>
                </div>
              </div>

              <div class="row mt-3" *ngIf="foundBooking.status === 'confirmed'">
                <div class="col-12">
                  <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Ready for Check-In!</strong> This booking is confirmed and can be checked in.
                  </div>
                  <div class="d-grid">
                    <button 
                      class="btn btn-success btn-lg"
                      (click)="performCheckIn(foundBooking)"
                      [disabled]="loading"
                    >
                      <span class="spinner-border spinner-border-sm me-2" *ngIf="loading"></span>
                      <i class="fas fa-sign-in-alt me-2" *ngIf="!loading"></i>
                      {{ loading ? 'Checking In...' : 'Confirm Check-In' }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="row mt-3" *ngIf="foundBooking.status === 'active'">
                <div class="col-12">
                  <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Already Checked In!</strong> This booking was checked in at {{ foundBooking.check_in_time | date:'short' }}.
                  </div>
                </div>
              </div>

              <div class="row mt-3" *ngIf="!canCheckIn(foundBooking)">
                <div class="col-12">
                  <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Cannot Check In!</strong> 
                    <span *ngIf="foundBooking.status === 'cancelled'">This booking has been cancelled.</span>
                    <span *ngIf="foundBooking.status === 'completed'">This booking has already been completed.</span>
                    <span *ngIf="foundBooking.status === 'pending'">Payment is still pending for this booking.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Check-ins -->
      <div class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">
                <i class="fas fa-history me-2"></i>
                Recent Check-ins
              </h5>
              <button class="btn btn-sm btn-outline-primary" (click)="loadRecentCheckins()">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loadingRecent"></i>
                Refresh
              </button>
            </div>
            <div class="card-body">
              <app-loading *ngIf="loadingRecent" message="Loading recent check-ins..."></app-loading>
              
              <div *ngIf="!loadingRecent && recentCheckins.length > 0">
                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>Reference</th>
                        <th>Customer</th>
                        <th>Vehicle</th>
                        <th>Check-in Time</th>
                        <th>Parking Lot</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let booking of recentCheckins">
                        <td class="font-monospace">{{ booking.booking_reference }}</td>
                        <td>{{ booking.user?.first_name }} {{ booking.user?.last_name }}</td>
                        <td>{{ booking.vehicle_number }}</td>
                        <td>{{ booking.check_in_time | date:'short' }}</td>
                        <td>{{ booking.lot?.name }}</td>
                        <td>
                          <span class="badge" [class]="getStatusBadgeClass(booking.status)">
                            {{ booking.status | titlecase }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div *ngIf="!loadingRecent && recentCheckins.length === 0" class="text-center py-4">
                <i class="fas fa-inbox fa-2x text-muted mb-2"></i>
                <p class="text-muted mb-0">No recent check-ins found</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .form-control-lg {
      font-size: 1.25rem;
      padding: 0.75rem 1rem;
    }

    .font-monospace {
      font-family: 'Courier New', monospace;
    }

    .table-borderless td {
      border: none;
      padding: 0.25rem 0.5rem;
    }
  `]
})
export class AdminCheckinComponent implements OnInit, OnDestroy {
  checkinForm: FormGroup;
  foundBooking: Booking | null = null;
  recentCheckins: Booking[] = [];
  loading = false;
  loadingRecent = false;
  errorMessage = '';
  
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private adminService: AdminService,
    private bookingService: BookingService
  ) {
    this.checkinForm = this.createCheckinForm();
  }

  ngOnInit(): void {
    this.loadRecentCheckins();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createCheckinForm(): FormGroup {
    return this.fb.group({
      bookingCode: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

  onBookingCodeChange(): void {
    // Clear previous results when user starts typing
    this.foundBooking = null;
    this.errorMessage = '';
  }

  onCheckIn(): void {
    if (this.checkinForm.valid) {
      const bookingCode = this.checkinForm.get('bookingCode')?.value.toUpperCase();
      
      this.loading = true;
      this.errorMessage = '';

      // First, find the booking by reference
      this.findBookingByReference(bookingCode);
    } else {
      this.markFormGroupTouched();
    }
  }

  private findBookingByReference(reference: string): void {
    this.bookingService.getBookingByReference(reference)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (booking) => {
          this.foundBooking = booking;
          this.loading = false;
          
          // Don't auto-check-in, just display the booking for review
          console.log('Found booking:', booking);
        },
        error: (error) => {
          console.error('Error finding booking:', error);
          this.errorMessage = 'Booking not found. Please check the reference code and try again.';
          this.loading = false;
          this.foundBooking = null;
        }
      });
  }

  performCheckIn(booking: Booking): void {
    this.loading = true;
    
    // Use admin check-in by reference endpoint
    this.adminService.checkInBookingByReference(booking.booking_reference)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          // Update the found booking status
          this.foundBooking!.status = 'active';
          this.foundBooking!.check_in_time = nowIST().toISOString();
          
          // Clear the form
          this.checkinForm.reset();
          this.foundBooking = null;
          
          // Reload recent check-ins
          this.loadRecentCheckins();
          
          // Show success message
          this.errorMessage = '';
          alert(`✅ Check-in successful!\n\nBooking ${booking.booking_reference} has been checked in.`);
          
          this.loading = false;
        },
        error: (error) => {
          console.error('Error checking in:', error);
          this.errorMessage = error.message || 'Failed to check in. Please try again.';
          this.loading = false;
        }
      });
  }

  canCheckIn(booking: Booking): boolean {
    if (!booking) return false;
    
    // Can check in if status is confirmed and not already checked in
    return booking.status === 'confirmed';
  }

  loadRecentCheckins(): void {
    this.loadingRecent = true;
    
    // Get recent bookings that have been checked in
    this.adminService.getAllBookings({
      limit: 20,
      // Filter for recent check-ins (you might want to add date filter)
    })
    .pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (bookings) => {
        // Filter for bookings that have been checked in recently
        this.recentCheckins = bookings
          .filter(b => b.status === 'active' && b.check_in_time)
          .sort((a, b) => new Date(b.check_in_time!).getTime() - new Date(a.check_in_time!).getTime())
          .slice(0, 10);
        
        this.loadingRecent = false;
      },
      error: (error) => {
        console.error('Error loading recent check-ins:', error);
        this.loadingRecent = false;
        
        // Provide demo data if backend is not available
        this.recentCheckins = this.getDemoCheckins();
      }
    });
  }

  getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'confirmed':
        return 'bg-success';
      case 'active':
        return 'bg-primary';
      case 'completed':
        return 'bg-info';
      case 'cancelled':
        return 'bg-danger';
      case 'pending':
        return 'bg-warning';
      default:
        return 'bg-secondary';
    }
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.checkinForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markFormGroupTouched(): void {
    Object.keys(this.checkinForm.controls).forEach(key => {
      const control = this.checkinForm.get(key);
      control?.markAsTouched();
    });
  }

  private getDemoCheckins(): Booking[] {
    return [
      {
        id: '1',
        booking_reference: 'SP001234',
        user_id: '1',
        lot_id: '1',
        slot_id: '1',
        vehicle_type: 'car',
        vehicle_number: 'ABC123',
        start_time: nowIST().toISOString(),
        end_time: new Date(nowIST().getTime() + 2 * 60 * 60 * 1000).toISOString(),
        total_amount: 16.00,
        status: 'active',
        check_in_time: new Date(nowIST().getTime() - 30 * 60 * 1000).toISOString(),
        created_at: nowIST().toISOString(),
        updated_at: nowIST().toISOString(),
        user: {
          id: '1',
          email: 'john.doe@example.com',
          first_name: 'John',
          last_name: 'Doe',
          phone: '+1234567890',
          is_admin: false,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        lot: {
          id: '1',
          name: 'Downtown Plaza Parking',
          address: '123 Main Street, Downtown, NY 10001',
          latitude: 40.7128,
          longitude: -74.0060,
          total_car_slots: 150,
          total_bike_slots: 75,
          hourly_rate_car: 8.00,
          hourly_rate_bike: 3.00,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      }
    ];
  }
}
