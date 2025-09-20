import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { PaymentFormComponent } from './payment-form.component';
import { BookingService } from '../../booking/services/booking.service';
import { Booking } from '../../../core/models/booking.model';

@Component({
  selector: 'app-payment-page',
  standalone: true,
  imports: [CommonModule, RouterModule, PaymentFormComponent],
  template: `
    <div class="container mt-4">
      <!-- Loading State -->
      <div class="row justify-content-center" *ngIf="loading">
        <div class="col-md-8 text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-3">Loading booking details...</p>
        </div>
      </div>

      <!-- Error State -->
      <div class="row justify-content-center" *ngIf="errorMessage">
        <div class="col-md-8">
          <div class="alert alert-danger">
            <h5 class="alert-heading">Error</h5>
            <p class="mb-0">{{ errorMessage }}</p>
            <hr>
            <button class="btn btn-outline-danger" (click)="goBack()">
              <i class="fas fa-arrow-left me-2"></i>Go Back
            </button>
          </div>
        </div>
      </div>

      <!-- Payment Page Content -->
      <div class="row justify-content-center" *ngIf="!loading && !errorMessage && booking">
        <div class="col-md-8">
          <!-- Page Header -->
          <div class="card mb-4">
            <div class="card-header bg-primary text-white">
              <div class="d-flex justify-content-between align-items-center">
                <h4 class="mb-0">
                  <i class="fas fa-credit-card me-2"></i>
                  Payment Details
                </h4>
                <button class="btn btn-outline-light btn-sm" (click)="goBack()">
                  <i class="fas fa-arrow-left me-1"></i>Back
                </button>
              </div>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <h6 class="text-muted mb-2">Booking Reference</h6>
                  <p class="fw-bold">{{ booking.booking_reference }}</p>
                </div>
                <div class="col-md-6 text-md-end">
                  <h6 class="text-muted mb-2">Total Amount</h6>
                  <p class="fw-bold fs-4 text-success">\${{ booking.total_amount.toFixed(2) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Booking Summary -->
          <div class="card mb-4">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-info-circle me-2"></i>
                Booking Summary
              </h5>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Parking Lot:</span>
                    <span class="fw-bold">{{ booking.lot?.name || 'Parking Lot' }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Vehicle:</span>
                    <span class="fw-bold">{{ booking.vehicle_number }} ({{ booking.vehicle_type | titlecase }})</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Status:</span>
                    <span class="badge bg-warning">{{ booking.status | titlecase }}</span>
                  </div>
                </div>
                <div class="col-md-6 mb-3">
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Start Time:</span>
                    <span class="fw-bold">{{ formatDateTime(booking.start_time) }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">End Time:</span>
                    <span class="fw-bold">{{ formatDateTime(booking.end_time) }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Duration:</span>
                    <span class="fw-bold">{{ getDuration() }} hours</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Payment Form -->
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-lock me-2"></i>
                Secure Payment
              </h5>
            </div>
            <div class="card-body">
              <app-payment-form
                [bookingId]="booking.id"
                [bookingReference]="booking.booking_reference"
                [amount]="booking.total_amount"
                (paymentSuccess)="onPaymentSuccess($event)"
                (paymentCancel)="onPaymentCancel()"
              ></app-payment-form>
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

    .card-header {
      background-color: #f8f9fc;
      border-bottom: 1px solid #e3e6f0;
    }

    .text-success {
      color: #1cc88a !important;
    }

    .bg-primary {
      background-color: #4e73df !important;
    }

    .btn-outline-light {
      border-color: rgba(255, 255, 255, 0.3);
    }

    .btn-outline-light:hover {
      background-color: rgba(255, 255, 255, 0.1);
      border-color: rgba(255, 255, 255, 0.5);
    }
  `]
})
export class PaymentPageComponent implements OnInit, OnDestroy {
  booking: Booking | null = null;
  loading = true;
  errorMessage = '';
  private destroy$ = new Subject<void>();

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private bookingService: BookingService
  ) {}

  ngOnInit(): void {
    this.loadBookingDetails();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadBookingDetails(): void {
    // Check if we have state data from booking form navigation
    const navigationState = this.router.getCurrentNavigation()?.extras?.state || 
                           window.history.state;
    
    if (navigationState && navigationState.bookingData) {
      // Use state data from booking form
      const bookingData = navigationState.bookingData;
      console.log('🔍 Payment page booking data:', bookingData);
      
      // Calculate proper start and end times
      const now = new Date();
      const startTime = now.toISOString();
      const durationMinutes = bookingData.duration || 60; // Default to 60 minutes if not provided
      const endTime = new Date(now.getTime() + durationMinutes * 60 * 1000).toISOString();
      
      this.booking = {
        id: 'temp-' + Date.now(), // Temporary ID
        booking_reference: 'TEMP-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
        lot: { name: bookingData.lotName },
        vehicle_type: bookingData.vehicleType,
        vehicle_number: bookingData.vehicleNumber,
        start_time: startTime,
        end_time: endTime,
        // duration_hours: durationMinutes / 60, // Not part of Booking interface
        total_amount: bookingData.totalAmount || 0,
        status: 'pending',
        lot_id: '',
        user_id: '',
        slot_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      } as any;
      
      console.log('✅ Created booking object:', this.booking);
      this.loading = false;
      return;
    }

    // Fallback to booking ID from route params
    const bookingId = this.route.snapshot.paramMap.get('bookingId');
    
    if (!bookingId) {
      this.errorMessage = 'No booking data found. Please start a new booking.';
      this.loading = false;
      return;
    }

    this.bookingService.getBooking(bookingId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (booking) => {
          this.booking = booking;
          this.loading = false;
          
          // Check if booking is in correct status for payment
          if (booking.status !== 'pending') {
            this.errorMessage = `This booking cannot be paid for. Status: ${booking.status}`;
          }
        },
        error: (error) => {
          this.errorMessage = error.message || 'Failed to load booking details. Please try again.';
          this.loading = false;
        }
      });
  }

  onPaymentSuccess(paymentResult: any): void {
    // Navigate to success page or booking confirmation
    this.router.navigate(['/bookings', this.booking?.id], {
      queryParams: { 
        payment: 'success',
        transactionId: paymentResult.transactionId 
      }
    });
  }

  onPaymentCancel(): void {
    // Go back to booking form or user dashboard
    this.goBack();
  }

  goBack(): void {
    // Check if there's a referrer or go to booking form
    const navigationExtras = {
      queryParams: {
        lotId: this.booking?.lot_id,
        vehicleType: this.booking?.vehicle_type,
        vehicleNumber: this.booking?.vehicle_number
      }
    };
    
    this.router.navigate(['/booking'], navigationExtras);
  }

  formatDateTime(dateTime: string): string {
    return new Date(dateTime).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  getDuration(): string {
    if (!this.booking) return '0';
    
    console.log('🔍 getDuration() called, booking:', this.booking);
    
    // Calculate from start and end times
    const start = new Date(this.booking.start_time);
    const end = new Date(this.booking.end_time);
    const durationMs = end.getTime() - start.getTime();
    const hours = durationMs / (1000 * 60 * 60);
    console.log('✅ Calculated duration from times:', hours, 'hours');
    return this.formatDurationDisplay(hours);
  }

  formatDurationDisplay(hours: number): string {
    if (hours === 0) return '0';
    
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    
    if (wholeHours === 0) {
      return `${minutes} minutes`;
    } else if (minutes === 0) {
      return `${wholeHours} hour${wholeHours > 1 ? 's' : ''}`;
    } else {
      return `${wholeHours} hour${wholeHours > 1 ? 's' : ''} ${minutes} minutes`;
    }
  }
}
