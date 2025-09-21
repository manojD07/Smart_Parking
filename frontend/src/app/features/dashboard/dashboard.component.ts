import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { AuthService } from '../auth/services/auth.service';
import { BookingService } from '../booking/services/booking.service';
import { ParkingService } from '../parking/services/parking.service';
import { SearchStateService } from '../../core/services/search-state.service';
import { LoadingComponent } from '../../shared/components/loading.component';
import { User } from '../../core/models/user.model';
import { Booking } from '../../core/models/booking.model';
import { ParkingLot } from '../../core/models/parking.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, LoadingComponent],
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
              <button class="btn btn-primary" routerLink="/bookings">
                <i class="fas fa-list me-2"></i>
                View Bookings
              </button>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading dashboard..."></app-loading>


      <div *ngIf="!loading">
        <!-- Main Dashboard Layout -->
        <div class="row mb-4">
          <!-- Left Side: Compact Search Form -->
          <div class="col-lg-6 mb-4">
            <div class="card h-100">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-search me-2"></i>
                  Find Parking
                </h5>
              </div>
              <div class="card-body">
                <form (ngSubmit)="onQuickSearch()" #searchForm="ngForm">
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="vehicleType" class="form-label">Vehicle Type</label>
                      <select class="form-select" id="vehicleType" [(ngModel)]="quickSearchData.vehicleType" name="vehicleType" required>
                        <option value="">Select Vehicle</option>
                        <option value="car">Car</option>
                        <option value="bike">Bike</option>
                      </select>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label for="currentLocation" class="form-label">Current Location</label>
                      <div class="input-group">
                        <input type="text" class="form-control" id="currentLocation" 
                               [(ngModel)]="quickSearchData.currentLocation" name="currentLocation" 
                               placeholder="Enter your current location" required>
                        <button type="button" class="btn btn-outline-secondary" 
                                (click)="getCurrentLocation()" [disabled]="gettingLocation">
                          <span class="spinner-border spinner-border-sm me-1" *ngIf="gettingLocation"></span>
                          <i class="fas fa-location-arrow" *ngIf="!gettingLocation"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="startTime" class="form-label">Start Time</label>
                      <input type="datetime-local" class="form-control" id="startTime" 
                             [(ngModel)]="quickSearchData.startTime" name="startTime" 
                             [min]="minStartTime" required>
                    </div>
                    <div class="col-md-6 mb-3">
                      <label for="endTime" class="form-label">End Time</label>
                      <input type="datetime-local" class="form-control" id="endTime" 
                             [(ngModel)]="quickSearchData.endTime" name="endTime" 
                             [min]="quickSearchData.startTime || minStartTime" required>
                    </div>
                  </div>
                  <!-- Validation Error -->
                  <div class="alert alert-danger mb-3" *ngIf="validationError">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    {{ validationError }}
                  </div>
                  
                  <div class="d-grid">
                    <button type="submit" class="btn btn-primary">
                      <span class="spinner-border spinner-border-sm me-2" *ngIf="searchLoading"></span>
                      <i class="fas fa-search me-2" *ngIf="!searchLoading"></i>
                      {{ searchLoading ? 'Searching...' : 'Search Parking' }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- Right Side: Quick Stats -->
          <div class="col-lg-6">
            <div class="row">
              <div class="col-md-6 col-sm-6 mb-3">
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
              <div class="col-md-6 col-sm-6 mb-3">
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
              <div class="col-md-6 col-sm-6 mb-3">
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
              <div class="col-md-6 col-sm-6 mb-3">
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
          </div>
        </div>


        <!-- Active Bookings -->
        <div class="row mb-4" *ngIf="activeBookings.length > 0">
          <div class="col-12">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Active Bookings</h5>
                <a [routerLink]="['/bookings']" [queryParams]="{filter: 'active'}" class="btn btn-sm btn-outline-primary">View All</a>
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
                              class="btn btn-sm btn-success me-1"
                              *ngIf="canCheckIn(booking)"
                              (click)="checkInBooking(booking.id)"
                            >
                              <i class="fas fa-sign-in-alt me-1"></i>Check In
                            </button>
                            <button 
                              class="btn btn-sm btn-warning me-1"
                              *ngIf="canCheckOut(booking)"
                              (click)="checkOutBooking(booking.id)"
                            >
                              <i class="fas fa-sign-out-alt me-1"></i>Check Out
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
  
  // Quick search form data
  quickSearchData = {
    vehicleType: '',
    currentLocation: '',
    startTime: '',
    endTime: ''
  };
  minStartTime = '';
  gettingLocation = false;
  
  // Search form validation
  searchLoading = false;
  validationError = '';
  searchError = '';
  
  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private bookingService: BookingService,
    private parkingService: ParkingService,
    private searchStateService: SearchStateService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.currentUser;
    console.log('Dashboard: Current user:', this.currentUser);
    
    // Initialize default times (current time and 1 hour from now)
    const now = new Date();
    const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);
    
    this.minStartTime = now.toISOString().slice(0, 16);
    this.quickSearchData.startTime = this.minStartTime;
    this.quickSearchData.endTime = oneHourLater.toISOString().slice(0, 16);
    
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
    // Load dashboard data directly
    this.loadFullDashboardData();
  }

  private loadFullDashboardData(): void {
    // Load ALL bookings to match My Bookings page counts
    this.bookingService.getMyBookings({ limit: 100 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bookings) => {
          console.log('Bookings loaded:', bookings);
          this.processBookingsData(bookings);
          this.loadParkingLots();
          this.loadUserProfile(); // Load accurate total spent from user profile
        },
        error: (error) => {
          console.error('Error loading bookings:', error);
          // Show empty state instead of demo data
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


  private processBookingsData(bookings: Booking[]): void {
    // Active bookings: confirmed or active status (matches My Bookings logic)
    this.activeBookings = bookings.filter(b => 
      ['confirmed', 'active'].includes(b.status)
    );
    
    // Recent bookings: bookings created in the last 30 days, sorted by creation date
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    this.recentBookings = bookings
      .filter(b => new Date(b.created_at) >= thirtyDaysAgo)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    
    // Calculate total spent from completed bookings (fallback if user profile fails)
    this.totalSpent = bookings
      .filter(b => b.status === 'completed')
      .reduce((sum, b) => sum + Number(b.total_amount), 0);
  }

  private loadUserProfile(): void {
    // Load user profile to get accurate total spent (includes prepaid payments)
    if (this.currentUser && this.currentUser.id) {
      this.authService.getCurrentUser()
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (user) => {
            if (user && user.total_spent !== undefined) {
              this.totalSpent = Number(user.total_spent);
              console.log('Total spent updated from user profile:', this.totalSpent);
            }
          },
          error: (error) => {
            console.warn('Failed to load user profile for total spent:', error);
            // Keep the calculated value from bookings as fallback
          }
        });
    }
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

  canCheckIn(booking: Booking): boolean {
    return this.bookingService.canCheckIn(booking);
  }

  canCheckOut(booking: Booking): boolean {
    return this.bookingService.canCheckOut(booking);
  }

  checkInBooking(bookingId: string): void {
    if (confirm('Are you sure you want to check in to this booking?')) {
      this.bookingService.checkInBooking(bookingId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            alert('✅ Check-in successful!\n\nEnjoy your parking. Remember to check out when you leave.');
            this.loadDashboardData(); // Reload data
          },
          error: (error) => {
            console.error('Error checking in:', error);
            alert('Failed to check in. Please try again or contact support.');
          }
        });
    }
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

  getCurrentLocation(): void {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by this browser.');
      return;
    }

    this.gettingLocation = true;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        // Use coordinates as location (simple and reliable)
        this.quickSearchData.currentLocation = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        this.gettingLocation = false;
      },
      (error) => {
        console.error('Error getting location:', error);
        this.gettingLocation = false;
        
        switch (error.code) {
          case error.PERMISSION_DENIED:
            alert('Location access denied. Please enable location permissions.');
            break;
          case error.POSITION_UNAVAILABLE:
            alert('Location information is unavailable.');
            break;
          case error.TIMEOUT:
            alert('Location request timed out.');
            break;
          default:
            alert('An unknown error occurred while getting location.');
            break;
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  }

  onQuickSearch(): void {
    // Clear previous errors
    this.validationError = '';
    this.searchError = '';
    
    // Validate form
    if (!this.quickSearchData.vehicleType) {
      this.validationError = 'Please select a vehicle type.';
      return;
    }
    
    if (!this.quickSearchData.currentLocation) {
      this.validationError = 'Please enter your current location.';
      return;
    }
    
    if (!this.quickSearchData.startTime) {
      this.validationError = 'Please select a start time.';
      return;
    }
    
    if (!this.quickSearchData.endTime) {
      this.validationError = 'Please select an end time.';
      return;
    }

    // Validate that end time is after start time
    const startTime = new Date(this.quickSearchData.startTime);
    const endTime = new Date(this.quickSearchData.endTime);
    
    if (endTime <= startTime) {
      this.validationError = 'End time must be after start time.';
      return;
    }
    
    // Save search parameters and redirect to parking page
    this.searchLoading = true;
    
    console.log('Redirecting to parking page with search data:', this.quickSearchData);
    
    // Save search state for the parking page to use
    const searchParams = {
      vehicleType: this.quickSearchData.vehicleType,
      currentLocation: this.quickSearchData.currentLocation,
      startTime: this.quickSearchData.startTime,
      endTime: this.quickSearchData.endTime
    };
    
    // Store search parameters temporarily for the parking page
    sessionStorage.setItem('dashboardSearchParams', JSON.stringify(searchParams));
    
    // Navigate to parking page with query parameters
    const queryParams: any = {
      vehicleType: this.quickSearchData.vehicleType,
      currentLocation: this.quickSearchData.currentLocation,
      startTime: this.quickSearchData.startTime,
      endTime: this.quickSearchData.endTime,
      autoSearch: 'true'  // Flag to trigger automatic search
    };
    
    this.router.navigate(['/parking'], { queryParams });
  }
}
