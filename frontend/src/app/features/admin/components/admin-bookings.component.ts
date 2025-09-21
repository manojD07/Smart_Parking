import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';

// Services
import { ToastService } from '../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from './shared/loading-state.component';

// Pipes
import { AppCurrencyPipe } from '../../../shared/pipes/currency.pipe';

@Component({
  selector: 'app-admin-bookings',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingStateComponent, AppCurrencyPipe],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h2><i class="fas fa-calendar-check me-2"></i>Booking Management</h2>
              <p class="text-muted mb-0">Manage all parking bookings with filtering and sorting</p>
            </div>
            <button class="btn btn-outline-primary" (click)="refreshBookings()" [disabled]="loading">
              <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>Refresh
            </button>
          </div>
        </div>
      </div>

      <!-- Statistics -->
      <div class="row mb-4">
        <div class="col-md-3 mb-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingStats.total }}</h4>
                  <small>Total Bookings</small>
                </div>
                <i class="fas fa-calendar-check fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingStats.confirmed }}</h4>
                  <small>Confirmed</small>
                </div>
                <i class="fas fa-check-circle fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingStats.active }}</h4>
                  <small>Active</small>
                </div>
                <i class="fas fa-clock fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingStats.total_revenue | appCurrency }}</h4>
                  <small>Total Revenue</small>
                </div>
                <i class="fas fa-dollar-sign fa-2x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-filter me-2"></i>Filters
            <button class="btn btn-sm btn-outline-secondary ms-2" (click)="clearFilters()">
              <i class="fas fa-times me-1"></i>Clear
            </button>
          </h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-3 mb-3">
              <label class="form-label">Status</label>
              <select class="form-select" [(ngModel)]="filters.status" (change)="applyFilters()">
                <option value="">All Statuses</option>
                <option value="confirmed">Confirmed</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div class="col-md-3 mb-3">
              <label class="form-label">Vehicle Type</label>
              <select class="form-select" [(ngModel)]="filters.vehicle_type" (change)="applyFilters()">
                <option value="">All Types</option>
                <option value="car">Car</option>
                <option value="bike">Bike</option>
              </select>
            </div>
            <div class="col-md-3 mb-3">
              <label class="form-label">User Email</label>
              <input type="text" class="form-control" 
                     [(ngModel)]="filters.user_email" 
                     (keyup.enter)="applyFilters()"
                     placeholder="Search by email...">
            </div>
            <div class="col-md-3 mb-3">
              <label class="form-label">Date From</label>
              <input type="date" class="form-control" 
                     [(ngModel)]="filters.date_from" 
                     (change)="applyFilters()">
            </div>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <app-loading-state *ngIf="loading" message="Loading bookings..."></app-loading-state>

      <!-- Bookings Table -->
      <div class="card" *ngIf="!loading">
        <div class="card-header">
          <h5 class="mb-0">
            <i class="fas fa-list me-2"></i>Bookings ({{ filteredBookings.length }})
          </h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th (click)="sortBy('booking_reference')" class="sortable">
                    Reference <i class="fas fa-sort ms-1"></i>
                  </th>
                  <th (click)="sortBy('user_email')" class="sortable">
                    User <i class="fas fa-sort ms-1"></i>
                  </th>
                  <th>Vehicle</th>
                  <th (click)="sortBy('start_time')" class="sortable">
                    Date & Time <i class="fas fa-sort ms-1"></i>
                  </th>
                  <th (click)="sortBy('total_amount')" class="sortable">
                    Amount <i class="fas fa-sort ms-1"></i>
                  </th>
                  <th (click)="sortBy('status')" class="sortable">
                    Status <i class="fas fa-sort ms-1"></i>
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let booking of filteredBookings">
                  <td><code>{{ booking.booking_reference || booking.id?.slice(0, 8) }}</code></td>
                  <td>
                    <div>
                      <div class="fw-semibold">{{ booking.user?.first_name }} {{ booking.user?.last_name }}</div>
                      <small class="text-muted">{{ booking.user?.email }}</small>
                    </div>
                  </td>
                  <td>
                    <span class="badge" [class.bg-primary]="booking.vehicle_type === 'car'" [class.bg-success]="booking.vehicle_type === 'bike'">
                      <i class="fas" [class.fa-car]="booking.vehicle_type === 'car'" [class.fa-motorcycle]="booking.vehicle_type === 'bike'"></i>
                      {{ booking.vehicle_type | titlecase }}
                    </span>
                    <div><small>{{ booking.vehicle_number }}</small></div>
                  </td>
                  <td>
                    <div>{{ formatDate(booking.start_time) }}</div>
                    <small class="text-muted">{{ formatTime(booking.start_time) }} - {{ formatTime(booking.end_time) }}</small>
                  </td>
                  <td>
                    <span class="fw-bold text-success">{{ booking.total_amount | appCurrency }}</span>
                  </td>
                  <td>
                    <span class="badge" 
                          [class.bg-success]="booking.status === 'confirmed'"
                          [class.bg-primary]="booking.status === 'active'"
                          [class.bg-secondary]="booking.status === 'completed'"
                          [class.bg-danger]="booking.status === 'cancelled'">
                      {{ booking.status | titlecase }}
                    </span>
                  </td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" (click)="viewBooking(booking)" title="View">
                        <i class="fas fa-eye"></i>
                      </button>
                      <button class="btn btn-outline-warning" 
                              *ngIf="booking.status === 'confirmed' || booking.status === 'active'"
                              (click)="cancelBooking(booking)" title="Cancel">
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr *ngIf="filteredBookings.length === 0">
                  <td colspan="7" class="text-center py-4">
                    <i class="fas fa-inbox fa-2x text-muted mb-2"></i>
                    <div class="text-muted">No bookings found</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <style>
      .sortable {
        cursor: pointer;
        user-select: none;
      }
      .sortable:hover {
        background-color: #f8f9fa;
      }
    </style>
  `
})
export class AdminBookingsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  bookings: any[] = [];
  filteredBookings: any[] = [];
  bookingStats = {
    total: 0,
    confirmed: 0,
    active: 0,
    completed: 0,
    cancelled: 0,
    total_revenue: 0
  };

  filters = {
    status: '',
    vehicle_type: '',
    user_email: '',
    date_from: ''
  };

  sortConfig = {
    field: 'created_at',
    direction: 'desc' as 'asc' | 'desc'
  };

  loading = false;

  constructor(private toastService: ToastService) {}

  ngOnInit(): void {
    this.loadBookings();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  async loadBookings(): Promise<void> {
    this.loading = true;
    try {
      // Mock data for now
      this.bookings = [
        {
          id: '1',
          booking_reference: 'BK001',
          user: { first_name: 'John', last_name: 'Doe', email: 'john@example.com' },
          vehicle_type: 'car',
          vehicle_number: 'ABC123',
          start_time: new Date().toISOString(),
          end_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
          total_amount: 25.50,
          status: 'confirmed'
        },
        {
          id: '2',
          booking_reference: 'BK002',
          user: { first_name: 'Jane', last_name: 'Smith', email: 'jane@example.com' },
          vehicle_type: 'bike',
          vehicle_number: 'XYZ789',
          start_time: new Date(Date.now() + 1 * 60 * 60 * 1000).toISOString(),
          end_time: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
          total_amount: 15.25,
          status: 'active'
        }
      ];
      
      this.filteredBookings = [...this.bookings];
      this.calculateStats();
    } catch (error) {
      console.error('Error loading bookings:', error);
      this.toastService.showError('Failed to load bookings');
    } finally {
      this.loading = false;
    }
  }

  applyFilters(): void {
    this.filteredBookings = this.bookings.filter(booking => {
      if (this.filters.status && booking.status !== this.filters.status) return false;
      if (this.filters.vehicle_type && booking.vehicle_type !== this.filters.vehicle_type) return false;
      if (this.filters.user_email && !booking.user?.email?.toLowerCase().includes(this.filters.user_email.toLowerCase())) return false;
      if (this.filters.date_from && new Date(booking.start_time) < new Date(this.filters.date_from)) return false;
      return true;
    });
  }

  sortBy(field: string): void {
    if (this.sortConfig.field === field) {
      this.sortConfig.direction = this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortConfig.field = field;
      this.sortConfig.direction = 'asc';
    }
    
    this.filteredBookings.sort((a, b) => {
      const aVal = this.getNestedValue(a, field);
      const bVal = this.getNestedValue(b, field);
      if (aVal < bVal) return this.sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return this.sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }

  getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((o, p) => o?.[p], obj);
  }

  clearFilters(): void {
    this.filters = { status: '', vehicle_type: '', user_email: '', date_from: '' };
    this.filteredBookings = [...this.bookings];
  }

  calculateStats(): void {
    this.bookingStats = {
      total: this.bookings.length,
      confirmed: this.bookings.filter(b => b.status === 'confirmed').length,
      active: this.bookings.filter(b => b.status === 'active').length,
      completed: this.bookings.filter(b => b.status === 'completed').length,
      cancelled: this.bookings.filter(b => b.status === 'cancelled').length,
      total_revenue: this.bookings.reduce((sum, b) => sum + (b.total_amount || 0), 0)
    };
  }

  async refreshBookings(): Promise<void> {
    await this.loadBookings();
    this.toastService.showSuccess('Bookings refreshed');
  }

  viewBooking(booking: any): void {
    this.toastService.showInfo('View booking details coming soon');
  }

  async cancelBooking(booking: any): Promise<void> {
    if (confirm(`Cancel booking ${booking.booking_reference}?`)) {
      booking.status = 'cancelled';
      this.calculateStats();
      this.toastService.showSuccess('Booking cancelled');
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  formatTime(dateString: string): string {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
