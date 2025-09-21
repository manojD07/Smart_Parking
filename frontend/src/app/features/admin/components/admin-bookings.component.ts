import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Subject, takeUntil } from 'rxjs';

// Services
import { ToastService } from '../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from './shared/loading-state.component';

// Pipes
import { AppCurrencyPipe } from '../../../shared/pipes/currency.pipe';
import { environment } from '../../../../environments/environment';

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
                  <small>Total Bookings (Today)</small>
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
                  <small>Total Revenue (Today)</small>
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
          
          <!-- Pagination Controls -->
          <div class="card-footer">
            <!-- Debug Info -->
            <div class="alert alert-info mb-3">
              <strong>Pagination Debug:</strong>
              Total Items: {{ pagination.totalItems }}, 
              Page Size: {{ pagination.pageSize }}, 
              Total Pages: {{ pagination.totalPages }}, 
              Current Page: {{ pagination.currentPage }}
            </div>
            <div class="row align-items-center">
              <div class="col-md-6">
                <div class="d-flex align-items-center gap-2">
                  <label class="form-label mb-0">Page Size:</label>
                  <select 
                    class="form-select form-select-sm" 
                    [(ngModel)]="pagination.pageSize" 
                    (change)="onPageSizeChange()"
                    [disabled]="loading"
                    style="width: auto;">
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                  <span class="text-muted">
                    Showing {{ getStartIndex() }}-{{ getEndIndex() }} of {{ pagination.totalItems }} bookings
                  </span>
                </div>
              </div>
              <div class="col-md-6">
                <nav aria-label="Bookings pagination">
                  <ul class="pagination justify-content-end mb-0">
                    <li class="page-item" [class.disabled]="pagination.currentPage === 1">
                      <a class="page-link" href="#" (click)="changePage(1); $event.preventDefault()">
                        <i class="fas fa-angle-double-left"></i>
                      </a>
                    </li>
                    <li class="page-item" [class.disabled]="pagination.currentPage === 1">
                      <a class="page-link" href="#" (click)="changePage(pagination.currentPage - 1); $event.preventDefault()">
                        <i class="fas fa-angle-left"></i>
                      </a>
                    </li>
                    
                    <!-- Page numbers -->
                    <li *ngFor="let page of getVisiblePages()" 
                        class="page-item" 
                        [class.active]="page === pagination.currentPage">
                      <a class="page-link" href="#" (click)="changePage(page); $event.preventDefault()">
                        {{ page }}
                      </a>
                    </li>
                    
                    <li class="page-item" [class.disabled]="pagination.currentPage === pagination.totalPages">
                      <a class="page-link" href="#" (click)="changePage(pagination.currentPage + 1); $event.preventDefault()">
                        <i class="fas fa-angle-right"></i>
                      </a>
                    </li>
                    <li class="page-item" [class.disabled]="pagination.currentPage === pagination.totalPages">
                      <a class="page-link" href="#" (click)="changePage(pagination.totalPages); $event.preventDefault()">
                        <i class="fas fa-angle-double-right"></i>
                      </a>
                    </li>
                  </ul>
                </nav>
              </div>
            </div>
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

  // Pagination
  pagination = {
    currentPage: 1,
    pageSize: 20,
    totalItems: 0,
    totalPages: 0
  };

  loading = false;
  errorMessage = '';

  constructor(
    private toastService: ToastService,
    private http: HttpClient
  ) {}

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
      // Load real bookings from API and separate metadata
      await Promise.all([
        this.loadBookingsList(),
        this.loadBookingsMetadata()
      ]);
      
      this.filteredBookings = [...this.bookings];
    } catch (error) {
      console.error('Error loading bookings:', error);
      this.toastService.showError('Failed to load bookings');
    } finally {
      this.loading = false;
    }
  }
  
  private async loadBookingsList(): Promise<void> {
    // Load paginated bookings for display
    const skip = (this.pagination.currentPage - 1) * this.pagination.pageSize;
    const limit = this.pagination.pageSize;
    
    let url = `${environment.apiUrl}/admin/bookings?skip=${skip}&limit=${limit}`;
    
    // Add filters to URL if they exist
    if (this.filters.status) url += `&status=${this.filters.status}`;
    if (this.filters.date_from) url += `&start_date=${this.filters.date_from}`;
    
    try {
      const response = await this.http.get<any[]>(url).toPromise();
      this.bookings = response || [];
      
      console.log(`Loaded page ${this.pagination.currentPage} (${this.bookings.length} bookings)`);
    } catch (error) {
      console.error('Failed to load bookings list:', error);
      this.bookings = [];
    }
  }
  
  private async loadBookingsMetadata(): Promise<void> {
    // Load total statistics (NOT affected by pagination)
    const url = `${environment.apiUrl}/admin/dashboard`;
    
    try {
      const response = await this.http.get<any>(url).toPromise();
      
      // Use the actual database totals for metadata
      this.bookingStats = {
        total: response?.today_statistics?.total_bookings || 0,
        confirmed: response?.today_statistics?.status_breakdown?.confirmed || 0,
        active: response?.today_statistics?.status_breakdown?.active || 0,
        completed: response?.today_statistics?.status_breakdown?.completed || 0,
        cancelled: response?.today_statistics?.status_breakdown?.cancelled || 0,
        total_revenue: parseFloat(response?.today_statistics?.total_revenue || 0)
      };
      
      // Update pagination metadata
      this.pagination.totalItems = this.bookingStats.total;
      this.pagination.totalPages = Math.ceil(this.pagination.totalItems / this.pagination.pageSize);
      
      console.log('Loaded metadata stats (NOT affected by pagination):', this.bookingStats);
      console.log('Pagination info:', this.pagination);
    } catch (error) {
      console.error('Failed to load bookings metadata:', error);
      // DO NOT fallback to paginated data - show error instead
      this.bookingStats = {
        total: 0,
        confirmed: 0,
        active: 0,
        completed: 0,
        cancelled: 0,
        total_revenue: 0
      };
      this.errorMessage = 'Failed to load booking statistics. Totals unavailable.';
    }
  }
  
  // REMOVED: This method was causing incorrect totals based on paginated data
  // Totals should ALWAYS come from database queries, never from UI pagination

  applyFilters(): void {
    // Reset to first page when applying filters
    this.pagination.currentPage = 1;
    
    // Reload data with filters applied
    this.loadBookings();
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
    this.pagination.currentPage = 1;
    this.loadBookings();
  }


  async refreshBookings(): Promise<void> {
    await this.loadBookings();
    this.toastService.showSuccess('Bookings refreshed');
  }

  // Pagination methods
  changePage(page: number): void {
    if (page >= 1 && page <= this.pagination.totalPages && page !== this.pagination.currentPage) {
      this.pagination.currentPage = page;
      this.loadBookingsList();
    }
  }

  async onPageSizeChange(): Promise<void> {
    console.log(`Page size changed to: ${this.pagination.pageSize}`);
    
    // Show loading state
    this.loading = true;
    
    try {
      // Reset to first page
      this.pagination.currentPage = 1;
      
      // Recalculate total pages
      this.pagination.totalPages = Math.ceil(this.pagination.totalItems / this.pagination.pageSize);
      
      console.log(`Auto-refreshing with new pagination: Page 1 of ${this.pagination.totalPages}`);
      
      // Auto-refresh data with new page size
      await this.loadBookingsList();
      
      this.toastService.showSuccess(`Page size changed to ${this.pagination.pageSize}`);
    } catch (error) {
      console.error('Error changing page size:', error);
      this.toastService.showError('Failed to change page size');
    } finally {
      this.loading = false;
    }
  }

  getVisiblePages(): number[] {
    const current = this.pagination.currentPage;
    const total = this.pagination.totalPages;
    const visible: number[] = [];
    
    // Show up to 5 page numbers around current page
    const start = Math.max(1, current - 2);
    const end = Math.min(total, current + 2);
    
    for (let i = start; i <= end; i++) {
      visible.push(i);
    }
    
    return visible;
  }

  getStartIndex(): number {
    return (this.pagination.currentPage - 1) * this.pagination.pageSize + 1;
  }

  getEndIndex(): number {
    return Math.min(
      this.pagination.currentPage * this.pagination.pageSize, 
      this.pagination.totalItems
    );
  }

  viewBooking(booking: any): void {
    this.toastService.showInfo('View booking details coming soon');
  }

  async cancelBooking(booking: any): Promise<void> {
    if (confirm(`Cancel booking ${booking.booking_reference}?`)) {
      try {
        // Call the actual cancel API
        const url = `${environment.apiUrl}/admin/bookings/${booking.id}/cancel`;
        await this.http.put(url, {}).toPromise();
        
        // Update local data
        booking.status = 'cancelled';
        
        // Reload metadata to get accurate totals
        await this.loadBookingsMetadata();
        
        this.toastService.showSuccess('Booking cancelled');
      } catch (error) {
        console.error('Failed to cancel booking:', error);
        this.toastService.showError('Failed to cancel booking');
      }
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  formatTime(dateString: string): string {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
