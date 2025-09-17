import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { BookingService } from '../services/booking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { Booking, BookingStatus } from '../../../core/models/booking.model';

@Component({
  selector: 'app-booking-list',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="h2 mb-0">
              <i class="fas fa-ticket-alt me-2"></i>
              My Bookings
            </h1>
            <button class="btn btn-primary" routerLink="/parking">
              <i class="fas fa-plus me-2"></i>
              New Booking
            </button>
          </div>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="row mb-4">
        <div class="col-12">
          <ul class="nav nav-pills">
            <li class="nav-item">
              <button 
                class="nav-link" 
                [class.active]="selectedFilter === 'all'"
                (click)="filterBookings('all')"
              >
                All Bookings
                <span class="badge bg-secondary ms-2" *ngIf="bookingCounts.all > 0">
                  {{ bookingCounts.all }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link" 
                [class.active]="selectedFilter === 'active'"
                (click)="filterBookings('active')"
              >
                Active
                <span class="badge bg-success ms-2" *ngIf="bookingCounts.active > 0">
                  {{ bookingCounts.active }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link" 
                [class.active]="selectedFilter === 'upcoming'"
                (click)="filterBookings('upcoming')"
              >
                Upcoming
                <span class="badge bg-info ms-2" *ngIf="bookingCounts.upcoming > 0">
                  {{ bookingCounts.upcoming }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link" 
                [class.active]="selectedFilter === 'completed'"
                (click)="filterBookings('completed')"
              >
                Completed
                <span class="badge bg-primary ms-2" *ngIf="bookingCounts.completed > 0">
                  {{ bookingCounts.completed }}
                </span>
              </button>
            </li>
            <li class="nav-item">
              <button 
                class="nav-link" 
                [class.active]="selectedFilter === 'cancelled'"
                (click)="filterBookings('cancelled')"
              >
                Cancelled
                <span class="badge bg-danger ms-2" *ngIf="bookingCounts.cancelled > 0">
                  {{ bookingCounts.cancelled }}
                </span>
              </button>
            </li>
          </ul>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading your bookings..."></app-loading>

      <!-- Error Message -->
      <div class="alert alert-danger" *ngIf="errorMessage">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>

      <!-- Bookings List -->
      <div class="row" *ngIf="!loading && filteredBookings.length > 0">
        <div class="col-12">
          <div class="card" *ngFor="let booking of filteredBookings">
            <div class="card-body">
              <div class="row align-items-center">
                <div class="col-lg-3">
                  <h5 class="card-title mb-1">
                    {{ booking.lot?.name || 'Parking Lot' }}
                  </h5>
                  <p class="text-muted mb-2">
                    <i class="fas fa-map-marker-alt me-1"></i>
                    {{ booking.lot?.address || 'Address not available' }}
                  </p>
                  <span class="badge" [class]="getStatusBadgeClass(booking.status)">
                    {{ booking.status | titlecase }}
                  </span>
                </div>

                <div class="col-lg-3">
                  <div class="mb-2">
                    <small class="text-muted">Vehicle:</small>
                    <div class="fw-bold">
                      {{ booking.vehicle_number }} 
                      <span class="text-capitalize">({{ booking.vehicle_type }})</span>
                    </div>
                  </div>
                  <div class="mb-2">
                    <small class="text-muted">Booking Reference:</small>
                    <div class="fw-bold font-monospace">{{ booking.booking_reference }}</div>
                  </div>
                </div>

                <div class="col-lg-3">
                  <div class="mb-2">
                    <small class="text-muted">Duration:</small>
                    <div class="fw-bold">
                      {{ formatDateTime(booking.start_time) }}
                      <br>
                      <i class="fas fa-arrow-down text-muted"></i>
                      <br>
                      {{ formatDateTime(booking.end_time) }}
                    </div>
                  </div>
                  <div>
                    <small class="text-muted">Total Duration:</small>
                    <div class="fw-bold">
                      {{ calculateDuration(booking.start_time, booking.end_time).toFixed(1) }} hours
                    </div>
                  </div>
                </div>

                <div class="col-lg-3">
                  <div class="mb-3">
                    <small class="text-muted">Total Amount:</small>
                    <div class="h5 text-primary fw-bold mb-0">
                      \${{ booking.total_amount }}
                    </div>
                  </div>

                  <div class="d-grid gap-2">
                    <button 
                      class="btn btn-outline-primary btn-sm"
                      [routerLink]="['/bookings', booking.id]"
                    >
                      <i class="fas fa-eye me-1"></i>
                      View Details
                    </button>
                    
                    <div class="btn-group" role="group" *ngIf="canModifyBooking(booking)">
                      <button 
                        class="btn btn-outline-warning btn-sm"
                        *ngIf="canModifyBooking(booking)"
                        (click)="modifyBooking(booking.id)"
                      >
                        <i class="fas fa-edit me-1"></i>
                        Modify
                      </button>
                      <button 
                        class="btn btn-outline-danger btn-sm"
                        *ngIf="canCancelBooking(booking)"
                        (click)="cancelBooking(booking)"
                      >
                        <i class="fas fa-times me-1"></i>
                        Cancel
                      </button>
                    </div>

                    <button 
                      class="btn btn-success btn-sm"
                      *ngIf="canCheckIn(booking)"
                      (click)="checkInBooking(booking.id)"
                    >
                      <i class="fas fa-sign-in-alt me-1"></i>
                      Check In
                    </button>

                    <button 
                      class="btn btn-warning btn-sm"
                      *ngIf="canCheckOut(booking)"
                      (click)="checkOutBooking(booking.id)"
                    >
                      <i class="fas fa-sign-out-alt me-1"></i>
                      Check Out
                    </button>
                  </div>
                </div>
              </div>

              <!-- Time indicators for active bookings -->
              <div class="row mt-3" *ngIf="booking.status === 'active'">
                <div class="col-12">
                  <div class="alert alert-info mb-0">
                    <div class="row">
                      <div class="col-md-6" *ngIf="booking.check_in_time">
                        <small>
                          <i class="fas fa-sign-in-alt me-1"></i>
                          Checked in: {{ formatDateTime(booking.check_in_time) }}
                        </small>
                      </div>
                      <div class="col-md-6">
                        <small>
                          <i class="fas fa-clock me-1"></i>
                          {{ getTimeStatus(booking) }}
                        </small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div class="row" *ngIf="!loading && filteredBookings.length === 0">
        <div class="col-12">
          <div class="text-center py-5">
            <i class="fas fa-ticket-alt fa-3x text-muted mb-3"></i>
            <h4>{{ getEmptyStateMessage() }}</h4>
            <p class="text-muted mb-4">
              {{ getEmptyStateDescription() }}
            </p>
            <button class="btn btn-primary" routerLink="/parking">
              <i class="fas fa-search me-2"></i>
              Find Parking
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class BookingListComponent implements OnInit, OnDestroy {
  bookings: Booking[] = [];
  filteredBookings: Booking[] = [];
  selectedFilter = 'all';
  loading = true;
  errorMessage = '';
  
  bookingCounts = {
    all: 0,
    active: 0,
    upcoming: 0,
    completed: 0,
    cancelled: 0
  };

  private destroy$ = new Subject<void>();

  constructor(private bookingService: BookingService) {}

  ngOnInit(): void {
    this.loadBookings();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadBookings(): void {
    this.bookingService.getMyBookings({ limit: 100 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bookings) => {
          this.bookings = bookings.sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
          this.calculateBookingCounts();
          this.filterBookings(this.selectedFilter);
          this.loading = false;
        },
        error: (error) => {
          this.errorMessage = error.message || 'Failed to load bookings';
          this.loading = false;
        }
      });
  }

  private calculateBookingCounts(): void {
    this.bookingCounts = {
      all: this.bookings.length,
      active: this.bookings.filter(b => ['confirmed', 'active'].includes(b.status)).length,
      upcoming: this.bookings.filter(b => this.isUpcoming(b)).length,
      completed: this.bookings.filter(b => b.status === 'completed').length,
      cancelled: this.bookings.filter(b => b.status === 'cancelled').length
    };
  }

  filterBookings(filter: string): void {
    this.selectedFilter = filter;
    
    switch (filter) {
      case 'active':
        this.filteredBookings = this.bookings.filter(b => 
          ['confirmed', 'active'].includes(b.status)
        );
        break;
      case 'upcoming':
        this.filteredBookings = this.bookings.filter(b => this.isUpcoming(b));
        break;
      case 'completed':
        this.filteredBookings = this.bookings.filter(b => b.status === 'completed');
        break;
      case 'cancelled':
        this.filteredBookings = this.bookings.filter(b => b.status === 'cancelled');
        break;
      default:
        this.filteredBookings = [...this.bookings];
    }
  }

  private isUpcoming(booking: Booking): boolean {
    const now = new Date();
    const startTime = new Date(booking.start_time);
    return startTime > now && booking.status === 'confirmed';
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
    return new Date(dateTime).toLocaleString();
  }

  calculateDuration(startTime: string, endTime: string): number {
    return this.bookingService.calculateDuration(startTime, endTime);
  }

  canModifyBooking(booking: Booking): boolean {
    return this.bookingService.canModifyBooking(booking);
  }

  canCancelBooking(booking: Booking): boolean {
    return this.bookingService.canCancelBooking(booking);
  }

  canCheckIn(booking: Booking): boolean {
    const now = new Date();
    const startTime = new Date(booking.start_time);
    const timeDiff = Math.abs(now.getTime() - startTime.getTime()) / (1000 * 60); // minutes
    
    return booking.status === 'confirmed' && timeDiff <= 30; // 30 minutes window
  }

  canCheckOut(booking: Booking): boolean {
    return booking.status === 'active' && !!booking.check_in_time;
  }

  getTimeStatus(booking: Booking): string {
    const now = new Date();
    const endTime = new Date(booking.end_time);
    const timeDiff = endTime.getTime() - now.getTime();
    const hoursLeft = timeDiff / (1000 * 60 * 60);
    
    if (hoursLeft > 1) {
      return `${hoursLeft.toFixed(1)} hours remaining`;
    } else if (hoursLeft > 0) {
      const minutesLeft = Math.floor(timeDiff / (1000 * 60));
      return `${minutesLeft} minutes remaining`;
    } else {
      return 'Time expired';
    }
  }

  modifyBooking(bookingId: string): void {
    // TODO: Implement modify booking functionality
    console.log('Modify booking:', bookingId);
  }

  cancelBooking(booking: Booking): void {
    if (confirm(`Are you sure you want to cancel your booking at ${booking.lot?.name}?`)) {
      this.bookingService.cancelBooking(booking.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            // Instant UI update - mark booking as cancelled
            const bookingIndex = this.bookings.findIndex(b => b.id === booking.id);
            if (bookingIndex !== -1) {
              this.bookings[bookingIndex].status = 'cancelled';
            }
            
            // Show success message
            alert('Booking cancelled successfully! Your slot has been released.');
            
            // Reload bookings to ensure consistency
            this.loadBookings();
          },
          error: (error) => {
            alert('Failed to cancel booking: ' + error.message);
          }
        });
    }
  }

  checkInBooking(bookingId: string): void {
    this.bookingService.checkInBooking(bookingId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loadBookings(); // Reload bookings
        },
        error: (error) => {
          alert('Failed to check in: ' + error.message);
        }
      });
  }

  checkOutBooking(bookingId: string): void {
    this.bookingService.checkOutBooking(bookingId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.loadBookings(); // Reload bookings
        },
        error: (error) => {
          alert('Failed to check out: ' + error.message);
        }
      });
  }

  getEmptyStateMessage(): string {
    switch (this.selectedFilter) {
      case 'active': return 'No active bookings';
      case 'upcoming': return 'No upcoming bookings';
      case 'completed': return 'No completed bookings';
      case 'cancelled': return 'No cancelled bookings';
      default: return 'No bookings found';
    }
  }

  getEmptyStateDescription(): string {
    switch (this.selectedFilter) {
      case 'active': return 'You don\'t have any active parking bookings right now.';
      case 'upcoming': return 'You don\'t have any upcoming parking bookings.';
      case 'completed': return 'You haven\'t completed any parking bookings yet.';
      case 'cancelled': return 'You don\'t have any cancelled bookings.';
      default: return 'You haven\'t made any parking bookings yet. Start by finding a parking spot!';
    }
  }
}