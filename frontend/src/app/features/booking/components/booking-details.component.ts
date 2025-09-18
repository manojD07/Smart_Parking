import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { BookingService } from '../services/booking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { Booking } from '../../../core/models/booking.model';
import { 
  parseBackendDate, 
  formatIST 
} from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-booking-details',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  template: `
    <div class="container mt-4">
      <app-loading *ngIf="loading" message="Loading booking details..."></app-loading>

      <div *ngIf="!loading && booking">
        <!-- Header -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h1 class="h2 mb-1">
                  <i class="fas fa-ticket-alt me-2"></i>
                  Booking Details
                </h1>
                <p class="text-muted mb-0">
                  Reference: <span class="font-monospace fw-bold">{{ booking.booking_reference }}</span>
                </p>
              </div>
              <div>
                <span class="badge fs-6" [class]="getStatusBadgeClass(booking.status)">
                  {{ booking.status | titlecase }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Success Alert for New Bookings -->
        <div class="row mb-4" *ngIf="isNewBooking">
          <div class="col-12">
            <div class="alert alert-success alert-dismissible fade show">
              <h4 class="alert-heading">
                <i class="fas fa-check-circle me-2"></i>
                Booking Confirmed!
              </h4>
              <p class="mb-3">
                Your parking space has been successfully booked. You will receive a confirmation email shortly.
              </p>
              <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div class="row">
          <!-- Booking Information -->
          <div class="col-lg-8">
            <!-- Parking Lot Information -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-map-marker-alt me-2"></i>
                  Parking Location
                </h5>
              </div>
              <div class="card-body">
                <h5 class="card-title">{{ booking.lot?.name || 'Parking Lot' }}</h5>
                <p class="card-text">
                  <i class="fas fa-location-arrow me-2"></i>
                  {{ booking.lot?.address || 'Address not available' }}
                </p>
                <div class="row">
                  <div class="col-md-6">
                    <small class="text-muted">Slot Number:</small>
                    <div class="fw-bold">
                      {{ booking.slot_number || 'Will be assigned on arrival' }}
                    </div>
                  </div>
                  <div class="col-md-6">
                    <small class="text-muted">Slot Type:</small>
                    <div class="fw-bold text-capitalize">
                      {{ booking.vehicle_type }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Vehicle & Time Information -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-car me-2"></i>
                  Booking Information
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">Vehicle Number:</small>
                    <div class="fw-bold fs-5">{{ booking.vehicle_number }}</div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">Vehicle Type:</small>
                    <div class="fw-bold text-capitalize">{{ booking.vehicle_type }}</div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">Start Time:</small>
                    <div class="fw-bold">{{ formatDateTime(booking.start_time) }}</div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">End Time:</small>
                    <div class="fw-bold">{{ formatDateTime(booking.end_time) }}</div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">Duration:</small>
                    <div class="fw-bold">
                      {{ calculateDuration(booking.start_time, booking.end_time).toFixed(1) }} hours
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <small class="text-muted">Total Amount:</small>
                    <div class="fw-bold text-primary fs-5">\${{ booking.total_amount }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Check-in/Check-out Information -->
            <div class="card mb-4" *ngIf="booking.check_in_time || booking.check_out_time">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-clock me-2"></i>
                  Activity Timeline
                </h5>
              </div>
              <div class="card-body">
                <div class="timeline">
                  <div class="timeline-item" *ngIf="booking.check_in_time">
                    <div class="timeline-marker bg-success">
                      <i class="fas fa-sign-in-alt"></i>
                    </div>
                    <div class="timeline-content">
                      <h6 class="timeline-title">Checked In</h6>
                      <p class="timeline-time">{{ formatDateTime(booking.check_in_time) }}</p>
                    </div>
                  </div>
                  <div class="timeline-item" *ngIf="booking.check_out_time">
                    <div class="timeline-marker bg-warning">
                      <i class="fas fa-sign-out-alt"></i>
                    </div>
                    <div class="timeline-content">
                      <h6 class="timeline-title">Checked Out</h6>
                      <p class="timeline-time">{{ formatDateTime(booking.check_out_time) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- QR Code (for active bookings) -->
            <div class="card mb-4" *ngIf="booking.status === 'active' || booking.status === 'confirmed'">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-qrcode me-2"></i>
                  Access QR Code
                </h5>
              </div>
              <div class="card-body text-center">
                <div class="qr-code-placeholder bg-light d-flex align-items-center justify-content-center mb-3" 
                     style="height: 200px; border: 2px dashed #dee2e6;">
                  <div class="text-center">
                    <i class="fas fa-qrcode fa-3x text-muted mb-2"></i>
                    <p class="text-muted mb-0">QR Code for Entry/Exit</p>
                    <small class="text-muted">{{ booking.booking_reference }}</small>
                  </div>
                </div>
                <p class="text-muted mb-0">
                  <i class="fas fa-info-circle me-1"></i>
                  Show this QR code at the parking entrance and exit
                </p>
              </div>
            </div>
          </div>

          <!-- Actions Sidebar -->
          <div class="col-lg-4">
            <!-- Actions Card -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-cogs me-2"></i>
                  Actions
                </h5>
              </div>
              <div class="card-body">
                <div class="d-grid gap-2">
                  <!-- Check In -->
                  <button 
                    class="btn btn-success"
                    *ngIf="canCheckIn()"
                    (click)="checkIn()"
                    [disabled]="processing"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="processing"></span>
                    <i class="fas fa-sign-in-alt me-2" *ngIf="!processing"></i>
                    Check In
                  </button>

                  <!-- Check Out -->
                  <button 
                    class="btn btn-warning"
                    *ngIf="canCheckOut()"
                    (click)="checkOut()"
                    [disabled]="processing"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="processing"></span>
                    <i class="fas fa-sign-out-alt me-2" *ngIf="!processing"></i>
                    Check Out
                  </button>

                  <!-- Modify Booking -->
                  <button 
                    class="btn btn-outline-primary"
                    *ngIf="canModify()"
                    (click)="modifyBooking()"
                  >
                    <i class="fas fa-edit me-2"></i>
                    Modify Booking
                  </button>

                  <!-- Cancel Booking -->
                  <button 
                    class="btn btn-outline-danger"
                    *ngIf="canCancel()"
                    (click)="cancelBooking()"
                    [disabled]="processing"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="processing"></span>
                    <i class="fas fa-times me-2" *ngIf="!processing"></i>
                    Cancel Booking
                  </button>

                  <!-- Download Receipt -->
                  <button 
                    class="btn btn-outline-secondary"
                    *ngIf="booking.status === 'completed'"
                    (click)="downloadReceipt()"
                  >
                    <i class="fas fa-download me-2"></i>
                    Download Receipt
                  </button>

                  <!-- Contact Support -->
                  <button class="btn btn-outline-info" (click)="contactSupport()">
                    <i class="fas fa-headset me-2"></i>
                    Contact Support
                  </button>
                </div>
              </div>
            </div>

            <!-- Booking Timeline -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-history me-2"></i>
                  Booking History
                </h5>
              </div>
              <div class="card-body">
                <div class="timeline">
                  <div class="timeline-item">
                    <div class="timeline-marker bg-primary">
                      <i class="fas fa-plus"></i>
                    </div>
                    <div class="timeline-content">
                      <h6 class="timeline-title">Booking Created</h6>
                      <p class="timeline-time">{{ formatDateTime(booking.created_at) }}</p>
                    </div>
                  </div>
                  <div class="timeline-item" *ngIf="booking.status !== 'pending'">
                    <div class="timeline-marker bg-success">
                      <i class="fas fa-check"></i>
                    </div>
                    <div class="timeline-content">
                      <h6 class="timeline-title">Booking Confirmed</h6>
                      <p class="timeline-time">{{ formatDateTime(booking.updated_at) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Important Information -->
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-info-circle me-2"></i>
                  Important Information
                </h5>
              </div>
              <div class="card-body">
                <ul class="list-unstyled mb-0">
                  <li class="mb-2">
                    <i class="fas fa-clock text-warning me-2"></i>
                    <small>Arrive within 30 minutes of start time</small>
                  </li>
                  <li class="mb-2">
                    <i class="fas fa-mobile-alt text-info me-2"></i>
                    <small>Use QR code for contactless entry</small>
                  </li>
                  <li class="mb-2">
                    <i class="fas fa-shield-alt text-success me-2"></i>
                    <small>Your spot is guaranteed once confirmed</small>
                  </li>
                  <li>
                    <i class="fas fa-phone text-primary me-2"></i>
                    <small>24/7 support: (555) 123-PARK</small>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Back Button -->
        <div class="row mt-4">
          <div class="col-12">
            <button class="btn btn-outline-primary" (click)="goBack()">
              <i class="fas fa-arrow-left me-2"></i>
              Back to Bookings
            </button>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div class="row" *ngIf="!loading && !booking">
        <div class="col-12">
          <div class="text-center py-5">
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h4>Booking Not Found</h4>
            <p class="text-muted mb-4">
              {{ errorMessage || 'The booking you are looking for could not be found.' }}
            </p>
            <button class="btn btn-primary" routerLink="/bookings">
              <i class="fas fa-list me-2"></i>
              View All Bookings
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom CSS for timeline -->
    <style>
      .timeline {
        position: relative;
        padding-left: 2rem;
      }

      .timeline::before {
        content: '';
        position: absolute;
        left: 1rem;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #dee2e6;
      }

      .timeline-item {
        position: relative;
        margin-bottom: 1.5rem;
      }

      .timeline-marker {
        position: absolute;
        left: -2rem;
        top: 0;
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 0.8rem;
      }

      .timeline-content {
        padding-left: 1rem;
      }

      .timeline-title {
        margin-bottom: 0.25rem;
        font-size: 0.9rem;
      }

      .timeline-time {
        margin-bottom: 0;
        font-size: 0.8rem;
        color: #6c757d;
      }
    </style>
  `
})
export class BookingDetailsComponent implements OnInit, OnDestroy {
  booking: Booking | null = null;
  loading = true;
  processing = false;
  errorMessage = '';
  isNewBooking = false;
  
  private destroy$ = new Subject<void>();

  constructor(
    private bookingService: BookingService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.isNewBooking = this.route.snapshot.queryParams['newBooking'] === 'true';
    this.loadBookingDetails();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadBookingDetails(): void {
    const bookingId = this.route.snapshot.params['id'];
    
    if (bookingId) {
      this.bookingService.getBooking(bookingId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (booking) => {
            this.booking = booking;
            this.loading = false;
          },
          error: (error) => {
            this.errorMessage = error.message || 'Failed to load booking details';
            this.loading = false;
          }
        });
    }
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

  formatDateTime(dateTime: string): string {
    return formatIST(parseBackendDate(dateTime));
  }

  calculateDuration(startTime: string, endTime: string): number {
    return this.bookingService.calculateDuration(startTime, endTime);
  }

  canCheckIn(): boolean {
    if (!this.booking) return false;
    const now = new Date();
    const startTime = parseBackendDate(this.booking.start_time);
    const timeDiff = Math.abs(now.getTime() - startTime.getTime()) / (1000 * 60); // minutes
    
    return this.booking.status === 'confirmed' && timeDiff <= 30; // 30 minutes window
  }

  canCheckOut(): boolean {
    if (!this.booking) return false;
    return this.booking.status === 'active' && !!this.booking.check_in_time;
  }

  canModify(): boolean {
    if (!this.booking) return false;
    return this.bookingService.canModifyBooking(this.booking);
  }

  canCancel(): boolean {
    if (!this.booking) return false;
    return this.bookingService.canCancelBooking(this.booking);
  }

  checkIn(): void {
    if (!this.booking) return;
    
    this.processing = true;
    this.bookingService.checkInBooking(this.booking.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loadBookingDetails(); // Reload to get updated data
          this.processing = false;
        },
        error: (error) => {
          alert('Failed to check in: ' + error.message);
          this.processing = false;
        }
      });
  }

  checkOut(): void {
    if (!this.booking) return;
    
    this.processing = true;
    this.bookingService.checkOutBooking(this.booking.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loadBookingDetails(); // Reload to get updated data
          this.processing = false;
        },
        error: (error) => {
          alert('Failed to check out: ' + error.message);
          this.processing = false;
        }
      });
  }

  modifyBooking(): void {
    // TODO: Implement modify booking functionality
    console.log('Modify booking:', this.booking?.id);
  }

  cancelBooking(): void {
    if (!this.booking) return;
    
    const confirmed = confirm(
      `Are you sure you want to cancel your booking at ${this.booking.lot?.name}?\\n\\n` +
      `This action cannot be undone.`
    );
    
    if (confirmed) {
      this.processing = true;
      this.bookingService.cancelBooking(this.booking.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            alert('Booking cancelled successfully! Your slot has been released and is now available for others.');
            this.router.navigate(['/bookings']);
          },
          error: (error) => {
            alert('Failed to cancel booking: ' + error.message);
            this.processing = false;
          }
        });
    }
  }

  downloadReceipt(): void {
    // TODO: Implement receipt download
    console.log('Download receipt for booking:', this.booking?.id);
  }

  contactSupport(): void {
    // TODO: Implement contact support
    alert('Support contact feature coming soon!\\nFor immediate assistance, call: (555) 123-PARK');
  }

  goBack(): void {
    this.router.navigate(['/bookings']);
  }
}