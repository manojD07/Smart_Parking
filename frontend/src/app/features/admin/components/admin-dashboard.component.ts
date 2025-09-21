import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { AdminService, DashboardResponse } from '../services/admin.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container-fluid mt-4">
      <div class="row mb-4">
        <div class="col-12">
          <h2>
            <i class="fas fa-tachometer-alt me-2"></i>
            Admin Dashboard
          </h2>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading dashboard data...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="errorMessage" class="alert alert-danger">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
      </div>

      <!-- Dashboard Content -->
      <div *ngIf="!loading && dashboardData">
        <!-- Overview Cards -->
        <div class="row mb-4">
          <div class="col-md-3 mb-3">
            <div class="card bg-primary text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ dashboardData.overview.total_users || 0 }}</h4>
                    <small>Total Users</small>
                  </div>
                  <i class="fas fa-users fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card bg-success text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ dashboardData.overview.total_parking_lots || 0 }}</h4>
                    <small>Parking Lots</small>
                  </div>
                  <i class="fas fa-parking fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card bg-info text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">{{ dashboardData.overview.today_bookings || 0 }}</h4>
                    <small>Today's Bookings</small>
                  </div>
                  <i class="fas fa-calendar-alt fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-3 mb-3">
            <div class="card bg-warning text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <div>
                    <h4 class="mb-0">$ {{ dashboardData.overview.today_revenue || 0 | number:'1.2-2' }}</h4>
                    <small>Today's Revenue</small>
                  </div>
                  <i class="fas fa-dollar-sign fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Statistics Row -->
        <div class="row mb-4">
          <!-- Booking Status Breakdown -->
          <div class="col-md-6 mb-3">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-chart-pie me-2"></i>
                  Booking Status
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-6 mb-2">
                    <div class="d-flex justify-content-between">
                      <span>Confirmed:</span>
                      <span class="badge bg-success">{{ dashboardData.today_statistics.status_breakdown.confirmed || 0 }}</span>
                    </div>
                  </div>
                  <div class="col-6 mb-2">
                    <div class="d-flex justify-content-between">
                      <span>Active:</span>
                      <span class="badge bg-primary">{{ dashboardData.today_statistics.status_breakdown.active || 0 }}</span>
                    </div>
                  </div>
                  <div class="col-6 mb-2">
                    <div class="d-flex justify-content-between">
                      <span>Completed:</span>
                      <span class="badge bg-info">{{ dashboardData.today_statistics.status_breakdown.completed || 0 }}</span>
                    </div>
                  </div>
                  <div class="col-6 mb-2">
                    <div class="d-flex justify-content-between">
                      <span>Pending:</span>
                      <span class="badge bg-warning">{{ dashboardData.today_statistics.status_breakdown.pending || 0 }}</span>
                    </div>
                  </div>
                  <div class="col-6 mb-2">
                    <div class="d-flex justify-content-between">
                      <span>Cancelled:</span>
                      <span class="badge bg-danger">{{ dashboardData.today_statistics.status_breakdown.cancelled || 0 }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Vehicle Type Breakdown -->
          <div class="col-md-6 mb-3">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-car me-2"></i>
                  Vehicle Types
                </h5>
              </div>
              <div class="card-body">
                <div class="row text-center">
                  <div class="col-6">
                    <i class="fas fa-car fa-2x text-primary mb-2"></i>
                    <h4>{{ dashboardData.today_statistics.vehicle_type_breakdown.car.count || 0 }}</h4>
                    <small class="text-muted">Cars</small>
                    <div class="text-success mt-1">
                      $ {{ dashboardData.today_statistics.vehicle_type_breakdown.car.revenue || 0 | number:'1.2-2' }}
                    </div>
                  </div>
                  <div class="col-6">
                    <i class="fas fa-motorcycle fa-2x text-success mb-2"></i>
                    <h4>{{ dashboardData.today_statistics.vehicle_type_breakdown.bike.count || 0 }}</h4>
                    <small class="text-muted">Bikes</small>
                    <div class="text-success mt-1">
                      $ {{ dashboardData.today_statistics.vehicle_type_breakdown.bike.revenue || 0 | number:'1.2-2' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Additional Statistics -->
        <div class="row">
          <div class="col-md-12">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-info-circle me-2"></i>
                  Summary Statistics
                </h5>
              </div>
              <div class="card-body">
                <div class="row text-center">
                  <div class="col-md-3">
                    <h4 class="text-primary">{{ dashboardData.today_statistics.total_bookings || 0 }}</h4>
                    <small class="text-muted">Total Bookings</small>
                  </div>
                  <div class="col-md-3">
                    <h4 class="text-success">$ {{ dashboardData.today_statistics.total_revenue || 0 | number:'1.2-2' }}</h4>
                    <small class="text-muted">Total Revenue</small>
                  </div>
                  <div class="col-md-3">
                    <h4 class="text-info">$ {{ dashboardData.today_statistics.average_booking_value || 0 | number:'1.2-2' }}</h4>
                    <small class="text-muted">Average Booking</small>
                  </div>
                  <div class="col-md-3">
                    <h4 class="text-warning">{{ getOccupancyRate() }}%</h4>
                    <small class="text-muted">Occupancy Rate</small>
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
export class AdminDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  dashboardData: DashboardResponse | null = null;
  loading = true;
  errorMessage = '';

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    this.loading = true;
    this.errorMessage = '';

    this.adminService.getDashboardData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          console.log('✅ Dashboard data received:', data);
          console.log('🔍 Vehicle type breakdown:', data?.today_statistics?.vehicle_type_breakdown);
          this.dashboardData = data;
          this.loading = false;
        },
        error: (error) => {
          console.error('❌ Dashboard API error:', error);
          this.errorMessage = 'Failed to load dashboard data';
          this.loading = false;
        }
      });
  }

  getOccupancyRate(): number {
    if (!this.dashboardData) return 0;
    
    const activeBookings = this.dashboardData.today_statistics?.status_breakdown?.active || 0;
    const totalLots = this.dashboardData.overview?.total_parking_lots || 0;
    
    // Rough calculation: assume each lot has ~100 slots
    const estimatedSlots = totalLots * 100;
    return estimatedSlots > 0 ? Math.round((activeBookings / estimatedSlots) * 100) : 0;
  }
}