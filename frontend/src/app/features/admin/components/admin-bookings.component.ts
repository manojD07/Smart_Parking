import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';
import { AdminService } from '../services/admin.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { Booking } from '../../../core/models/booking.model';

@Component({
  selector: 'app-admin-bookings',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h1 class="h2 mb-1">
                <i class="fas fa-ticket-alt me-2"></i>
                Booking Management
              </h1>
              <p class="text-muted">Monitor and manage all bookings</p>
            </div>
            <div>
              <button class="btn btn-outline-primary me-2" (click)="loadBookings()">
                <i class="fas fa-sync-alt me-2" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-outline-success">
                <i class="fas fa-download me-2"></i>
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="row">
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="searchInput" class="form-label">Search</label>
                    <input
                      type="text"
                      class="form-control"
                      id="searchInput"
                      placeholder="Search by reference, user, or lot..."
                      [(ngModel)]="searchTerm"
                      (input)="onSearchChange()"
                    >
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label for="statusFilter" class="form-label">Status</label>
                    <select 
                      class="form-select" 
                      id="statusFilter"
                      [(ngModel)]="statusFilter"
                      (change)="loadBookings()"
                    >
                      <option value="">All Status</option>
                      <option value="pending">Pending</option>
                      <option value="confirmed">Confirmed</option>
                      <option value="active">Active</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label for="dateFilter" class="form-label">Date Range</label>
                    <select 
                      class="form-select" 
                      id="dateFilter"
                      [(ngModel)]="dateFilter"
                      (change)="loadBookings()"
                    >
                      <option value="">All Time</option>
                      <option value="today">Today</option>
                      <option value="week">This Week</option>
                      <option value="month">This Month</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="startDate" class="form-label">Start Date</label>
                    <input
                      type="date"
                      class="form-control"
                      id="startDate"
                      [(ngModel)]="startDate"
                      (change)="loadBookings()"
                    >
                  </div>
                </div>
                <div class="col-md-2">
                  <div class="form-group">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-outline-secondary w-100" (click)="resetFilters()">
                      <i class="fas fa-undo me-1"></i>
                      Reset
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="row mb-4">
        <div class="col-md-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <h5 class="card-title">{{ getTotalBookings() }}</h5>
              <p class="card-text">Total Bookings</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <h5 class="card-title">{{ getActiveBookings() }}</h5>
              <p class="card-text">Active Bookings</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <h5 class="card-title">\${{ getTotalRevenue().toFixed(2) }}</h5>
              <p class="card-text">Total Revenue</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <h5 class="card-title">{{ getCancelledBookings() }}</h5>
              <p class="card-text">Cancelled</p>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading bookings..."></app-loading>

      <!-- Bookings Table -->
      <div class="row" *ngIf="!loading">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h5 class="mb-0">Bookings ({{ bookings.length }})</h5>
              <div class="d-flex gap-2">
                <select class="form-select form-select-sm" style="width: auto;">
                  <option>10 per page</option>
                  <option>25 per page</option>
                  <option>50 per page</option>
                </select>
              </div>
            </div>
            <div class="card-body p-0">
              <div class="table-responsive">
                <table class="table table-striped table-hover mb-0">
                  <thead class="table-dark">
                    <tr>
                      <th>Reference</th>
                      <th>User</th>
                      <th>Parking Lot</th>
                      <th>Vehicle</th>
                      <th>Time Slot</th>
                      <th>Amount</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let booking of bookings">
                      <td>
                        <span class="font-monospace fw-bold">{{ booking.booking_reference }}</span>
                        <br>
                        <small class="text-muted">{{ booking.created_at | date:'short' }}</small>
                      </td>
                      <td>
                        <div>
                          <strong>{{ booking.user?.first_name }} {{ booking.user?.last_name }}</strong>
                          <br>
                          <small class="text-muted">{{ booking.user?.email }}</small>
                        </div>
                      </td>
                      <td>
                        <div>
                          <strong>{{ booking.lot?.name }}</strong>
                          <br>
                          <small class="text-muted">Slot: {{ booking.slot?.slot_number || 'TBA' }}</small>
                        </div>
                      </td>
                      <td>
                        <span class="badge bg-secondary">{{ booking.vehicle_type | uppercase }}</span>
                        <br>
                        <small class="text-muted">{{ booking.vehicle_number }}</small>
                      </td>
                      <td>
                        <div class="small">
                          <strong>Start:</strong> {{ booking.start_time | date:'short' }}
                          <br>
                          <strong>End:</strong> {{ booking.end_time | date:'short' }}
                          <br>
                          <span class="text-muted">
                            {{ calculateDuration(booking.start_time, booking.end_time).toFixed(1) }}h
                          </span>
                        </div>
                      </td>
                      <td>
                        <strong class="text-success">\${{ booking.total_amount }}</strong>
                      </td>
                      <td>
                        <span 
                          class="badge" 
                          [class]="getStatusBadgeClass(booking.status)"
                        >
                          {{ booking.status | titlecase }}
                        </span>
                      </td>
                      <td>
                        <div class="btn-group" role="group">
                          <button 
                            class="btn btn-sm btn-outline-primary"
                            (click)="viewBookingDetails(booking)"
                            title="View Details"
                          >
                            <i class="fas fa-eye"></i>
                          </button>
                          <button 
                            class="btn btn-sm btn-outline-danger"
                            *ngIf="canCancelBooking(booking)"
                            (click)="cancelBooking(booking)"
                            title="Cancel Booking"
                          >
                            <i class="fas fa-times"></i>
                          </button>
                          <button 
                            class="btn btn-sm btn-outline-warning"
                            *ngIf="canRefundBooking(booking)"
                            (click)="refundBooking(booking)"
                            title="Process Refund"
                          >
                            <i class="fas fa-undo"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Empty State -->
              <div class="text-center py-5" *ngIf="bookings.length === 0 && !loading">
                <i class="fas fa-ticket-alt fa-3x text-muted mb-3"></i>
                <h5>No bookings found</h5>
                <p class="text-muted">Try adjusting your search criteria</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Booking Details Modal -->
      <div class="modal fade" id="bookingDetailsModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
          <div class="modal-content" *ngIf="selectedBooking">
            <div class="modal-header">
              <h5 class="modal-title">Booking Details</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <div class="row">
                <div class="col-md-6">
                  <h6>Booking Information</h6>
                  <table class="table table-sm">
                    <tr>
                      <td><strong>Reference:</strong></td>
                      <td>{{ selectedBooking.booking_reference }}</td>
                    </tr>
                    <tr>
                      <td><strong>Status:</strong></td>
                      <td>
                        <span 
                          class="badge" 
                          [class]="getStatusBadgeClass(selectedBooking.status)"
                        >
                          {{ selectedBooking.status | titlecase }}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Created:</strong></td>
                      <td>{{ selectedBooking.created_at | date:'full' }}</td>
                    </tr>
                    <tr>
                      <td><strong>Total Amount:</strong></td>
                      <td><strong class="text-success">\${{ selectedBooking.total_amount }}</strong></td>
                    </tr>
                  </table>
                </div>
                <div class="col-md-6">
                  <h6>User Information</h6>
                  <table class="table table-sm">
                    <tr>
                      <td><strong>Name:</strong></td>
                      <td>{{ selectedBooking.user?.first_name }} {{ selectedBooking.user?.last_name }}</td>
                    </tr>
                    <tr>
                      <td><strong>Email:</strong></td>
                      <td>{{ selectedBooking.user?.email }}</td>
                    </tr>
                    <tr>
                      <td><strong>Phone:</strong></td>
                      <td>{{ selectedBooking.user?.phone || 'N/A' }}</td>
                    </tr>
                  </table>
                </div>
              </div>
              
              <div class="row">
                <div class="col-md-6">
                  <h6>Parking Details</h6>
                  <table class="table table-sm">
                    <tr>
                      <td><strong>Lot:</strong></td>
                      <td>{{ selectedBooking.lot?.name }}</td>
                    </tr>
                    <tr>
                      <td><strong>Address:</strong></td>
                      <td>{{ selectedBooking.lot?.address }}</td>
                    </tr>
                    <tr>
                      <td><strong>Slot:</strong></td>
                      <td>{{ selectedBooking.slot?.slot_number || 'TBA' }}</td>
                    </tr>
                  </table>
                </div>
                <div class="col-md-6">
                  <h6>Vehicle & Timing</h6>
                  <table class="table table-sm">
                    <tr>
                      <td><strong>Vehicle:</strong></td>
                      <td>{{ selectedBooking.vehicle_number }} ({{ selectedBooking.vehicle_type }})</td>
                    </tr>
                    <tr>
                      <td><strong>Start Time:</strong></td>
                      <td>{{ selectedBooking.start_time | date:'full' }}</td>
                    </tr>
                    <tr>
                      <td><strong>End Time:</strong></td>
                      <td>{{ selectedBooking.end_time | date:'full' }}</td>
                    </tr>
                    <tr>
                      <td><strong>Duration:</strong></td>
                      <td>{{ calculateDuration(selectedBooking.start_time, selectedBooking.end_time).toFixed(1) }} hours</td>
                    </tr>
                  </table>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Close
              </button>
              <button 
                type="button" 
                class="btn btn-danger"
                *ngIf="canCancelBooking(selectedBooking)"
                (click)="cancelBooking(selectedBooking)"
              >
                Cancel Booking
              </button>
              <button 
                type="button" 
                class="btn btn-warning"
                *ngIf="canRefundBooking(selectedBooking)"
                (click)="refundBooking(selectedBooking)"
              >
                Process Refund
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .btn-group .btn {
      border-radius: 0.25rem;
      margin-right: 0.25rem;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      font-size: 0.9rem;
    }

    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }
  `]
})
export class AdminBookingsComponent implements OnInit, OnDestroy {
  bookings: Booking[] = [];
  selectedBooking: Booking | null = null;
  loading = true;
  
  searchTerm = '';
  statusFilter = '';
  dateFilter = '';
  startDate = '';
  
  private destroy$ = new Subject<void>();
  private searchSubject = new Subject<string>();

  constructor(private adminService: AdminService) {
    // Setup search debouncing
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(() => {
      this.loadBookings();
    });
  }

  ngOnInit(): void {
    this.loadBookings();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadBookings(): void {
    this.loading = true;
    
    const params: any = {
      limit: 100
    };
    
    if (this.statusFilter) {
      params.status = this.statusFilter;
    }
    
    if (this.startDate) {
      params.start_date = this.startDate;
    }
    
    // Add date filter logic
    if (this.dateFilter) {
      const now = new Date();
      switch (this.dateFilter) {
        case 'today':
          params.start_date = now.toISOString().split('T')[0];
          break;
        case 'week':
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          params.start_date = weekAgo.toISOString().split('T')[0];
          break;
        case 'month':
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          params.start_date = monthAgo.toISOString().split('T')[0];
          break;
      }
    }

    this.adminService.getAllBookings(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (bookings) => {
          this.bookings = bookings;
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading bookings:', error);
          this.loading = false;
          // Provide demo data if backend is not available
          this.bookings = this.getDemoBookings();
        }
      });
  }

  onSearchChange(): void {
    this.searchSubject.next(this.searchTerm);
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.statusFilter = '';
    this.dateFilter = '';
    this.startDate = '';
    this.loadBookings();
  }

  viewBookingDetails(booking: Booking): void {
    this.selectedBooking = booking;
    // Open modal (you might want to use a proper modal service)
    console.log('Viewing details for booking:', booking.booking_reference);
  }

  cancelBooking(booking: Booking): void {
    const reason = prompt('Reason for cancellation (optional):');
    if (reason !== null) {
      this.adminService.cancelBooking(booking.id, reason)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            booking.status = 'cancelled';
            console.log('Booking cancelled successfully');
          },
          error: (error) => {
            console.error('Error cancelling booking:', error);
            alert('Failed to cancel booking');
          }
        });
    }
  }

  refundBooking(booking: Booking): void {
    if (confirm(`Process refund of $${booking.total_amount} for booking ${booking.booking_reference}?`)) {
      this.adminService.refundBooking(booking.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => {
            console.log('Refund processed successfully');
            alert('Refund processed successfully');
          },
          error: (error) => {
            console.error('Error processing refund:', error);
            alert('Failed to process refund');
          }
        });
    }
  }

  canCancelBooking(booking: Booking): boolean {
    return ['pending', 'confirmed'].includes(booking.status);
  }

  canRefundBooking(booking: Booking): boolean {
    return ['cancelled', 'completed'].includes(booking.status);
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

  calculateDuration(startTime: string, endTime: string): number {
    const start = new Date(startTime);
    const end = new Date(endTime);
    return Math.abs(end.getTime() - start.getTime()) / (1000 * 60 * 60);
  }

  getTotalBookings(): number {
    return this.bookings.length;
  }

  getActiveBookings(): number {
    return this.bookings.filter(b => ['confirmed', 'active'].includes(b.status)).length;
  }

  getTotalRevenue(): number {
    return this.bookings
      .filter(b => b.status === 'completed')
      .reduce((sum, b) => sum + Number(b.total_amount), 0);
  }

  getCancelledBookings(): number {
    return this.bookings.filter(b => b.status === 'cancelled').length;
  }

  private getDemoBookings(): Booking[] {
    return [
      {
        id: '1',
        booking_reference: 'SP001234',
        user_id: '1',
        lot_id: '1',
        slot_id: '1',
        vehicle_type: 'car',
        vehicle_number: 'ABC123',
        start_time: new Date().toISOString(),
        end_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
        total_amount: 16.00,
        status: 'confirmed',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user: {
          id: '1',
          email: 'john.doe@example.com',
          first_name: 'John',
          last_name: 'Doe',
          phone: '+1234567890',
          is_admin: false,
          is_active: true,
          total_spent: 45.50,
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
