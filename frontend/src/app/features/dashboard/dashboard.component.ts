import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { AuthService } from '../auth/services/auth.service';
import { BookingService } from '../booking/services/booking.service';
import { ParkingService } from '../parking/services/parking.service';
import { LoadingComponent } from '../../shared/components/loading.component';
import { User } from '../../core/models/user.model';
import { Booking } from '../../core/models/booking.model';
import { ParkingLot } from '../../core/models/parking.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
              <h1 class="h2 mb-1">Welcome back, {{ currentUser?.first_name }}!</h1>
              <p class="text-muted">Manage your parking reservations</p>
            </div>
            <div>
              <button class="btn btn-primary" routerLink="/parking">
                <i class="fas fa-plus me-2"></i>
                New Booking
              </button>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading dashboard..."></app-loading>

      <!-- Backend Status Alert -->
      <div class="row mb-3" *ngIf="!loading && !backendAvailable">
        <div class="col-12">
          <div class="alert alert-warning alert-dismissible fade show">
            <h6 class="alert-heading">
              <i class="fas fa-exclamation-triangle me-2"></i>
              Backend Not Available
            </h6>
            <p class="mb-2">
              The Smart Parking backend service is currently not running. Some features may not work properly.
            </p>
            <hr>
            <p class="mb-0">
              <small>
                <strong>To start the backend:</strong> Run <code>cd backend && python -m uvicorn app.main:app --reload</code>
              </small>
            </p>
          </div>
        </div>
      </div>

      <div *ngIf="!loading">
        <!-- Quick Stats -->
        <div class="row mb-4">
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card bg-primary text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ activeBookings.length }}</h4>
                    <p class="mb-0">Active Bookings</p>
                  </div>
                  <div class="align-self-center">
                    <i class="fas fa-ticket-alt fa-2x"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card bg-success text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ recentBookings.length }}</h4>
                    <p class="mb-0">Recent Bookings</p>
                  </div>
                  <div class="align-self-center">
                    <i class="fas fa-history fa-2x"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card bg-info text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ nearbyLots.length }}</h4>
                    <p class="mb-0">Nearby Lots</p>
                  </div>
                  <div class="align-self-center">
                    <i class="fas fa-map-marker-alt fa-2x"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-3 col-sm-6 mb-3">
            <div class="card bg-warning text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">\${{ totalSpent.toFixed(2) }}</h4>
                    <p class="mb-0">Total Spent</p>
                  </div>
                  <div class="align-self-center">
                    <i class="fas fa-dollar-sign fa-2x"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Active Bookings -->
        <div class="row mb-4" *ngIf="activeBookings.length > 0">
          <div class="col-12">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Active Bookings</h5>
                <a routerLink="/bookings" class="btn btn-sm btn-outline-primary">View All</a>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6" *ngFor="let booking of activeBookings.slice(0, 2)">
                    <div class="card mb-3 border-start border-primary border-3">
                      <div class="card-body">
                        <h6 class="card-title">{{ booking.lot?.name || 'Parking Lot' }}</h6>
                        <p class="card-text">
                          <small class="text-muted">
                            <i class="fas fa-car me-1"></i>{{ booking.vehicle_number }} ({{ booking.vehicle_type }})
                          </small>
                        </p>
                        <p class="card-text" *ngIf="booking.slot_number">
                          <small class="text-muted">
                            <i class="fas fa-parking me-1"></i>Slot: <strong>{{ booking.slot_number }}</strong>
                          </small>
                        </p>
                        <p class="card-text" *ngIf="!booking.slot_number && booking.status === 'pending'">
                          <small class="text-warning">
                            <i class="fas fa-clock me-1"></i>Slot will be assigned at check-in
                          </small>
                        </p>
                        <p class="card-text">
                          <i class="fas fa-clock me-1"></i>
                          {{ formatDateTime(booking.start_time) }} - {{ formatDateTime(booking.end_time) }}
                        </p>
                        <div class="d-flex justify-content-between align-items-center">
                          <span class="badge bg-success">{{ booking.status | titlecase }}</span>
                          <div>
                            <button class="btn btn-sm btn-outline-primary me-1" [routerLink]="['/bookings', booking.id]">
                              View
                            </button>
                            <button 
                              class="btn btn-sm btn-outline-warning me-1"
                              *ngIf="canCheckOut(booking)"
                              (click)="checkOutBooking(booking.id)"
                            >
                              Check Out
                            </button>
                            <button 
                              class="btn btn-sm btn-outline-danger"
                              *ngIf="canCancel(booking)"
                              (click)="cancelBooking(booking.id)"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">Quick Actions</h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-4 mb-3">
                    <button class="btn btn-outline-primary w-100" routerLink="/parking">
                      <i class="fas fa-search fa-2x d-block mb-2"></i>
                      Find Parking
                    </button>
                  </div>
                  <div class="col-md-4 mb-3">
                    <button class="btn btn-outline-success w-100" routerLink="/bookings">
                      <i class="fas fa-list fa-2x d-block mb-2"></i>
                      View Bookings
                    </button>
                  </div>
                  <div class="col-md-4 mb-3">
                    <button class="btn btn-outline-info w-100" routerLink="/profile">
                      <i class="fas fa-user fa-2x d-block mb-2"></i>
                      Edit Profile
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="row" *ngIf="recentBookings.length > 0">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">Recent Activity</h5>
              </div>
              <div class="card-body">
                <div class="list-group list-group-flush">
                  <div class="list-group-item" *ngFor="let booking of recentBookings.slice(0, 5)">
                    <div class="d-flex justify-content-between align-items-start">
                      <div>
                        <h6 class="mb-1">{{ booking.lot?.name || 'Parking Booking' }}</h6>
                        <p class="mb-1">
                          {{ booking.vehicle_number }} - {{ formatDateTime(booking.start_time) }}
                        </p>
                        <small class="text-muted">\${{ booking.total_amount }}</small>
                      </div>
                      <span class="badge" [class]="getStatusBadgeClass(booking.status)">
                        {{ booking.status | titlecase }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  activeBookings: Booking[] = [];
  recentBookings: Booking[] = [];
  nearbyLots: ParkingLot[] = [];
  totalSpent = 0;
  loading = true;
  backendAvailable = true;
  
  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private bookingService: BookingService,
    private parkingService: ParkingService
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.currentUser;
    console.log('Dashboard: Current user:', this.currentUser);
    
    // Add a timeout to prevent infinite loading
    setTimeout(() => {
      if (this.loading) {
        console.warn('Dashboard: Loading timeout, showing empty state');
        this.loading = false;
      }
    }, 10000); // 10 second timeout
    
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    // Check if backend is running first
    this.bookingService.getMyBookings({ limit: 1 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bookings) => {
          // Backend is working, load full data
          console.log('Backend is running, loading full dashboard data');
          this.loadFullDashboardData();
        },
        error: (error) => {
          console.warn('Backend not accessible, showing demo dashboard:', error);
          this.backendAvailable = false;
          // Show demo/offline dashboard
          this.loadDemoData();
        }
      });
  }

  private loadFullDashboardData(): void {
    // Load bookings first
    this.bookingService.getMyBookings({ limit: 20 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bookings) => {
          console.log('Bookings loaded:', bookings);
          this.processBookingsData(bookings);
          this.loadParkingLots();
        },
        error: (error) => {
          console.error('Error loading bookings:', error);
          this.processBookingsData([]);
          this.loadParkingLots();
        }
      });
  }

  private loadParkingLots(): void {
    this.parkingService.getParkingLots({ limit: 10, is_active: true })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (lots) => {
          console.log('Parking lots loaded:', lots);
          this.nearbyLots = lots;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading parking lots:', error);
          this.nearbyLots = [];
          this.loading = false;
        }
      });
  }

  private loadDemoData(): void {
    // Show demo data when backend is not available
    console.log('Loading demo dashboard data');
    
    // Demo bookings
    this.activeBookings = [];
    this.recentBookings = [];
    this.nearbyLots = [];
    this.totalSpent = 0;
    
    this.loading = false;
  }

  private processBookingsData(bookings: Booking[]): void {
    this.activeBookings = bookings.filter(b => 
      ['confirmed', 'active'].includes(b.status)
    );
    
    this.recentBookings = bookings
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    
    this.totalSpent = bookings
      .filter(b => b.status === 'completed')
      .reduce((sum, b) => sum + Number(b.total_amount), 0);
  }

  formatDateTime(dateTime: string): string {
    return new Date(dateTime).toLocaleString();
  }

  getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'confirmed':
      case 'active':
        return 'bg-success';
      case 'completed':
        return 'bg-primary';
      case 'cancelled':
        return 'bg-danger';
      case 'pending':
        return 'bg-warning';
      default:
        return 'bg-secondary';
    }
  }

  canCancel(booking: Booking): boolean {
    return this.bookingService.canCancelBooking(booking);
  }

  canCheckOut(booking: Booking): boolean {
    // Can check out if booking is active and has been checked in
    return booking.status === 'active' && !!booking.check_in_time;
  }

  checkOutBooking(bookingId: string): void {
    if (confirm('Are you sure you want to check out of this booking?')) {
      this.bookingService.checkOutBooking(bookingId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            alert('✅ Check-out successful!\n\nThank you for using our parking service.');
            this.loadDashboardData(); // Reload data
          },
          error: (error) => {
            console.error('Error checking out:', error);
            alert('Failed to check out. Please try again or contact support.');
          }
        });
    }
  }

  cancelBooking(bookingId: string): void {
    if (confirm('Are you sure you want to cancel this booking?')) {
      this.bookingService.cancelBooking(bookingId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            // Instant UI update - remove cancelled booking from list
            this.activeBookings = this.activeBookings.filter((b: Booking) => b.id !== bookingId);
            this.recentBookings = this.recentBookings.filter((b: Booking) => b.id !== bookingId);
            
            // Show success message
            alert('Booking cancelled successfully! Your slot has been released.');
            
            // Reload data to ensure consistency
            this.loadDashboardData();
          },
          error: (error) => {
            console.error('Error cancelling booking:', error);
            alert('Failed to cancel booking. Please try again.');
          }
        });
    }
  }
}
