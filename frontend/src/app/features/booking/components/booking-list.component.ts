import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { BookingService } from '../services/booking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { Booking, BookingStatus } from '../../../core/models/booking.model';
import { 
  parseBackendDate, 
  formatIST 
} from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-booking-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, LoadingComponent],
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

      <!-- Search and Sort Controls -->
      <div class="row mb-4" *ngIf="!loading && allBookings.length > 0">
        <div class="col-md-6">
          <div class="input-group">
            <span class="input-group-text">
              <i class="fas fa-search"></i>
            </span>
            <input 
              type="text" 
              class="form-control" 
              placeholder="Search by lot name, vehicle number, or reference..."
              [(ngModel)]="searchTerm"
              (input)="onSearchChange()"
            >
            <button class="btn btn-outline-secondary" type="button" (click)="clearSearch()" *ngIf="searchTerm">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <div class="col-md-6">
          <div class="row">
            <div class="col-md-6">
              <select class="form-select" [(ngModel)]="sortBy" (change)="onSortChange()">
                <option value="created_at">Sort by Date</option>
                <option value="start_time">Sort by Start Time</option>
                <option value="lot_name">Sort by Location</option>
                <option value="vehicle_number">Sort by Vehicle</option>
                <option value="total_amount">Sort by Amount</option>
                <option value="status">Sort by Status</option>
              </select>
            </div>
            <div class="col-md-6">
              <select class="form-select" [(ngModel)]="sortOrder" (change)="onSortChange()">
                <option value="desc">Newest First</option>
                <option value="asc">Oldest First</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Results Summary -->
      <div class="row mb-3" *ngIf="!loading && allBookings.length > 0">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <small class="text-muted">
              Showing {{ paginatedBookings.length }} of {{ filteredBookings.length }} bookings
              <span *ngIf="searchTerm">(filtered from {{ allBookings.length }} total)</span>
            </small>
            <div class="btn-group btn-group-sm" role="group">
              <button type="button" class="btn btn-outline-secondary" 
                      [class.active]="itemsPerPage === 10" 
                      (click)="changeItemsPerPage(10)">10</button>
              <button type="button" class="btn btn-outline-secondary" 
                      [class.active]="itemsPerPage === 25" 
                      (click)="changeItemsPerPage(25)">25</button>
              <button type="button" class="btn btn-outline-secondary" 
                      [class.active]="itemsPerPage === 50" 
                      (click)="changeItemsPerPage(50)">50</button>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading your bookings..."></app-loading>

      <!-- Error Message -->
      <div class="alert alert-danger" *ngIf="errorMessage">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>

      <!-- Bookings List -->
      <div class="row" *ngIf="!loading && paginatedBookings.length > 0">
        <div class="col-12">
          <div class="card" *ngFor="let booking of paginatedBookings">
            <div class="card-body">
              <div class="row align-items-center">
                <div class="col-lg-3">
                  <h5 class="card-title mb-1">
                    {{ booking.lot_name || booking.lot?.name || 'Parking Lot' }}
                  </h5>
                  <p class="text-muted mb-2">
                    <i class="fas fa-map-marker-alt me-1"></i>
                    {{ booking.lot_address || booking.lot?.address || 'Address not available' }}
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
                    <small class="text-muted">Slot Number:</small>
                    <div class="fw-bold">
                      <i class="fas fa-parking me-1"></i>
                      {{ booking.slot_number || 'Will be assigned' }}
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
                    
                    <!-- Check-in Button -->
                    <button 
                      class="btn btn-success btn-sm"
                      *ngIf="canCheckIn(booking)"
                      (click)="checkInBooking(booking.id)"
                    >
                      <i class="fas fa-sign-in-alt me-1"></i>
                      Check In
                    </button>

                    <!-- Check-out Button -->
                    <button 
                      class="btn btn-warning btn-sm"
                      *ngIf="canCheckOut(booking)"
                      (click)="checkOutBooking(booking.id)"
                    >
                      <i class="fas fa-sign-out-alt me-1"></i>
                      Check Out
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

      <!-- Pagination -->
      <div class="row mt-4" *ngIf="!loading && filteredBookings.length > itemsPerPage">
        <div class="col-12">
          <nav aria-label="Bookings pagination">
            <ul class="pagination justify-content-center">
              <li class="page-item" [class.disabled]="currentPage === 1">
                <button class="page-link" (click)="goToPage(1)" [disabled]="currentPage === 1">
                  <i class="fas fa-angle-double-left"></i>
                </button>
              </li>
              <li class="page-item" [class.disabled]="currentPage === 1">
                <button class="page-link" (click)="goToPage(currentPage - 1)" [disabled]="currentPage === 1">
                  <i class="fas fa-angle-left"></i>
                </button>
              </li>
              
              <li class="page-item" 
                  *ngFor="let page of getVisiblePages()" 
                  [class.active]="page === currentPage">
                <button class="page-link" (click)="goToPage(page)">{{ page }}</button>
              </li>
              
              <li class="page-item" [class.disabled]="currentPage === totalPages">
                <button class="page-link" (click)="goToPage(currentPage + 1)" [disabled]="currentPage === totalPages">
                  <i class="fas fa-angle-right"></i>
                </button>
              </li>
              <li class="page-item" [class.disabled]="currentPage === totalPages">
                <button class="page-link" (click)="goToPage(totalPages)" [disabled]="currentPage === totalPages">
                  <i class="fas fa-angle-double-right"></i>
                </button>
              </li>
            </ul>
          </nav>
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
  allBookings: Booking[] = [];
  filteredBookings: Booking[] = [];
  paginatedBookings: Booking[] = [];
  selectedFilter = 'all';
  loading = true;
  errorMessage = '';
  
  // Search and sorting
  searchTerm = '';
  sortBy = 'created_at';
  sortOrder: 'asc' | 'desc' = 'desc';
  
  // Pagination
  currentPage = 1;
  itemsPerPage = 10;
  totalPages = 1;
  
  bookingCounts = {
    all: 0,
    active: 0,
    upcoming: 0,
    completed: 0,
    cancelled: 0
  };

  private destroy$ = new Subject<void>();

  constructor(
    private bookingService: BookingService,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    // Check for filter query parameter
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
      const filter = params['filter'];
      if (filter && ['all', 'active', 'upcoming', 'completed', 'cancelled'].includes(filter)) {
        this.selectedFilter = filter;
      }
    });
    
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
          this.allBookings = bookings;
          this.bookings = [...bookings];
          this.calculateBookingCounts();
          this.applyFiltersAndSorting();
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
    this.currentPage = 1; // Reset to first page when filtering
    this.applyFiltersAndSorting();
  }

  private isUpcoming(booking: Booking): boolean {
    const now = new Date();
    const startTime = parseBackendDate(booking.start_time);
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
    return formatIST(parseBackendDate(dateTime));
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
    return this.bookingService.canCheckIn(booking);
  }

  canCheckOut(booking: Booking): boolean {
    return this.bookingService.canCheckOut(booking);
  }

  getTimeStatus(booking: Booking): string {
    const now = new Date();
    const endTime = parseBackendDate(booking.end_time);
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
    if (confirm('Are you sure you want to check in to this booking?')) {
      this.bookingService.checkInBooking(bookingId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            alert('✅ Check-in successful!\n\nEnjoy your parking. Remember to check out when you leave.');
            this.loadBookings(); // Reload bookings
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
            this.loadBookings(); // Reload bookings
          },
          error: (error) => {
            console.error('Error checking out:', error);
            alert('Failed to check out. Please try again or contact support.');
          }
        });
    }
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

  // Search, Sort, and Pagination Methods
  onSearchChange(): void {
    this.currentPage = 1; // Reset to first page when searching
    this.applyFiltersAndSorting();
  }

  clearSearch(): void {
    this.searchTerm = '';
    this.onSearchChange();
  }

  onSortChange(): void {
    this.currentPage = 1; // Reset to first page when sorting
    this.applyFiltersAndSorting();
  }

  changeItemsPerPage(items: number): void {
    this.itemsPerPage = items;
    this.currentPage = 1; // Reset to first page
    this.applyFiltersAndSorting();
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePagination();
    }
  }

  getVisiblePages(): number[] {
    const pages: number[] = [];
    const maxVisible = 5;
    const half = Math.floor(maxVisible / 2);
    
    let start = Math.max(1, this.currentPage - half);
    let end = Math.min(this.totalPages, start + maxVisible - 1);
    
    // Adjust start if we're near the end
    if (end - start + 1 < maxVisible) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  }

  private applyFiltersAndSorting(): void {
    // Start with all bookings
    let filtered = [...this.allBookings];

    // Apply status filter
    if (this.selectedFilter !== 'all') {
      filtered = this.getFilteredBookings(filtered, this.selectedFilter);
    }

    // Apply search filter
    if (this.searchTerm.trim()) {
      const searchLower = this.searchTerm.toLowerCase().trim();
      filtered = filtered.filter(booking => 
        (booking.lot_name || booking.lot?.name || '').toLowerCase().includes(searchLower) ||
        booking.vehicle_number.toLowerCase().includes(searchLower) ||
        booking.booking_reference.toLowerCase().includes(searchLower) ||
        (booking.lot_address || booking.lot?.address || '').toLowerCase().includes(searchLower)
      );
    }

    // Apply sorting
    filtered = this.sortBookings(filtered);

    this.filteredBookings = filtered;
    this.updatePagination();
  }

  private getFilteredBookings(bookings: Booking[], filter: string): Booking[] {
    switch (filter) {
      case 'active':
        return bookings.filter(b => ['confirmed', 'active'].includes(b.status));
      case 'upcoming':
        return bookings.filter(b => b.status === 'pending');
      case 'completed':
        return bookings.filter(b => b.status === 'completed');
      case 'cancelled':
        return bookings.filter(b => b.status === 'cancelled');
      default:
        return bookings;
    }
  }

  private sortBookings(bookings: Booking[]): Booking[] {
    return bookings.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (this.sortBy) {
        case 'created_at':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        case 'start_time':
          aValue = new Date(a.start_time);
          bValue = new Date(b.start_time);
          break;
        case 'lot_name':
          aValue = (a.lot_name || a.lot?.name || '').toLowerCase();
          bValue = (b.lot_name || b.lot?.name || '').toLowerCase();
          break;
        case 'vehicle_number':
          aValue = a.vehicle_number.toLowerCase();
          bValue = b.vehicle_number.toLowerCase();
          break;
        case 'total_amount':
          aValue = a.total_amount;
          bValue = b.total_amount;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
      }

      if (aValue < bValue) return this.sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return this.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }

  private updatePagination(): void {
    this.totalPages = Math.ceil(this.filteredBookings.length / this.itemsPerPage);
    
    // Ensure current page is valid
    if (this.currentPage > this.totalPages && this.totalPages > 0) {
      this.currentPage = this.totalPages;
    }
    
    // Calculate paginated bookings
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    this.paginatedBookings = this.filteredBookings.slice(startIndex, endIndex);
  }
}