import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { AdminService } from '../services/admin.service';
import { LoadingComponent } from '../../../shared/components/loading.component';

@Component({
  selector: 'app-admin-analytics',
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
                <i class="fas fa-chart-line me-2"></i>
                Analytics & Reports
              </h1>
              <p class="text-muted">System analytics and performance metrics</p>
            </div>
            <div>
              <button class="btn btn-primary me-2" (click)="loadAnalytics()">
                <i class="fas fa-sync-alt me-2" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-outline-success">
                <i class="fas fa-download me-2"></i>
                Export Report
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Date Range Filter -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="row align-items-end">
                <div class="col-md-3">
                  <label for="dateRange" class="form-label">Date Range</label>
                  <select 
                    class="form-select" 
                    id="dateRange"
                    [(ngModel)]="selectedDateRange"
                    (change)="onDateRangeChange()"
                  >
                    <option value="7">Last 7 Days</option>
                    <option value="30">Last 30 Days</option>
                    <option value="90">Last 3 Months</option>
                    <option value="365">Last Year</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label for="startDate" class="form-label">Custom Start Date</label>
                  <input
                    type="date"
                    class="form-control"
                    id="startDate"
                    [(ngModel)]="startDate"
                    (change)="loadAnalytics()"
                  >
                </div>
                <div class="col-md-3">
                  <label for="endDate" class="form-label">Custom End Date</label>
                  <input
                    type="date"
                    class="form-control"
                    id="endDate"
                    [(ngModel)]="endDate"
                    (change)="loadAnalytics()"
                  >
                </div>
                <div class="col-md-3">
                  <label for="granularity" class="form-label">Granularity</label>
                  <select 
                    class="form-select" 
                    id="granularity"
                    [(ngModel)]="granularity"
                    (change)="loadAnalytics()"
                  >
                    <option value="hour">Hourly</option>
                    <option value="day">Daily</option>
                    <option value="week">Weekly</option>
                    <option value="month">Monthly</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading analytics..."></app-loading>

      <div *ngIf="!loading">
        <!-- KPI Cards -->
        <div class="row mb-4">
          <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-primary">
              <div class="card-body">
                <div class="row no-gutters align-items-center">
                  <div class="col mr-2">
                    <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                      Total Revenue
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      \${{ totalRevenue | number:'1.2-2' }}
                    </div>
                    <div class="small text-success" *ngIf="revenueGrowth > 0">
                      <i class="fas fa-arrow-up me-1"></i>
                      +{{ revenueGrowth.toFixed(1) }}% vs last period
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-dollar-sign fa-2x text-primary"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-success">
              <div class="card-body">
                <div class="row no-gutters align-items-center">
                  <div class="col mr-2">
                    <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                      Total Bookings
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      {{ totalBookings | number }}
                    </div>
                    <div class="small text-success" *ngIf="bookingGrowth > 0">
                      <i class="fas fa-arrow-up me-1"></i>
                      +{{ bookingGrowth.toFixed(1) }}% vs last period
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-ticket-alt fa-2x text-success"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-info">
              <div class="card-body">
                <div class="row no-gutters align-items-center">
                  <div class="col mr-2">
                    <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                      Avg. Occupancy
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      {{ averageOccupancy.toFixed(1) }}%
                    </div>
                    <div class="progress mt-2" style="height: 4px;">
                      <div
                        class="progress-bar bg-info"
                        [style.width.%]="averageOccupancy"
                      ></div>
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-chart-pie fa-2x text-info"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-warning">
              <div class="card-body">
                <div class="row no-gutters align-items-center">
                  <div class="col mr-2">
                    <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                      Avg. Duration
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      {{ averageDuration.toFixed(1) }}h
                    </div>
                    <div class="small text-muted">
                      Per booking session
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-clock fa-2x text-warning"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
          <!-- Revenue Chart -->
          <div class="col-lg-8">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-chart-line me-2"></i>
                  Revenue Trends
                </h5>
              </div>
              <div class="card-body">
                <div class="chart-placeholder">
                  <canvas id="revenueChart" width="400" height="200"></canvas>
                  <!-- Placeholder for chart -->
                  <div class="text-center py-5">
                    <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                    <h5>Revenue Chart</h5>
                    <p class="text-muted">Chart visualization would be implemented here using Chart.js or similar</p>
                    <div class="row">
                      <div class="col-md-6" *ngFor="let point of mockChartData.revenue">
                        <div class="border rounded p-2 mb-2">
                          <strong>{{ point.date | date:'short' }}</strong>: \${{ point.value }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Occupancy Chart -->
          <div class="col-lg-4">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-chart-pie me-2"></i>
                  Lot Utilization
                </h5>
              </div>
              <div class="card-body">
                <div class="text-center">
                  <!-- Placeholder for pie chart -->
                  <div class="mb-3">
                    <canvas id="occupancyChart" width="200" height="200"></canvas>
                    <div class="row">
                      <div class="col-12" *ngFor="let lot of mockChartData.occupancy">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                          <span class="small">{{ lot.name }}</span>
                          <div>
                            <span class="badge bg-primary">{{ lot.occupancy }}%</span>
                          </div>
                        </div>
                        <div class="progress mb-2" style="height: 6px;">
                          <div
                            class="progress-bar"
                            [style.width.%]="lot.occupancy"
                            [class.bg-success]="lot.occupancy < 70"
                            [class.bg-warning]="lot.occupancy >= 70 && lot.occupancy < 90"
                            [class.bg-danger]="lot.occupancy >= 90"
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tables Row -->
        <div class="row mb-4">
          <!-- Top Performing Lots -->
          <div class="col-lg-6">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-trophy me-2"></i>
                  Top Performing Lots
                </h5>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-striped mb-0">
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Parking Lot</th>
                        <th>Revenue</th>
                        <th>Bookings</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let lot of topPerformingLots; index as i">
                        <td>
                          <span class="badge" 
                            [class.bg-warning]="i === 0"
                            [class.bg-secondary]="i === 1"
                            [class.bg-dark]="i === 2"
                            [class.bg-light]="i > 2"
                            [class.text-dark]="i > 2"
                          >
                            #{{ i + 1 }}
                          </span>
                        </td>
                        <td>{{ lot.name }}</td>
                        <td class="text-success fw-bold">\${{ lot.revenue }}</td>
                        <td>{{ lot.bookings }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Peak Hours Analysis -->
          <div class="col-lg-6">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-clock me-2"></i>
                  Peak Hours Analysis
                </h5>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-striped mb-0">
                    <thead>
                      <tr>
                        <th>Time Period</th>
                        <th>Avg. Occupancy</th>
                        <th>Bookings</th>
                        <th>Revenue</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let period of peakHours">
                        <td>{{ period.timeRange }}</td>
                        <td>
                          <div class="d-flex align-items-center">
                            <span class="me-2">{{ period.occupancy }}%</span>
                            <div class="progress flex-grow-1" style="height: 6px;">
                              <div
                                class="progress-bar"
                                [style.width.%]="period.occupancy"
                                [class.bg-success]="period.occupancy < 70"
                                [class.bg-warning]="period.occupancy >= 70 && period.occupancy < 90"
                                [class.bg-danger]="period.occupancy >= 90"
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td>{{ period.bookings }}</td>
                        <td class="text-success">\${{ period.revenue }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Summary Reports -->
        <div class="row">
          <div class="col-12">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <i class="fas fa-file-alt me-2"></i>
                  Available Reports
                </h5>
                <div>
                  <button class="btn btn-outline-primary btn-sm me-2" (click)="generateReport('revenue')">
                    Revenue Report
                  </button>
                  <button class="btn btn-outline-success btn-sm me-2" (click)="generateReport('usage')">
                    Usage Report
                  </button>
                  <button class="btn btn-outline-info btn-sm" (click)="generateReport('users')">
                    User Report
                  </button>
                </div>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-4">
                    <h6>Revenue Report</h6>
                    <p class="text-muted small">
                      Detailed breakdown of revenue by lot, time period, and vehicle type.
                    </p>
                  </div>
                  <div class="col-md-4">
                    <h6>Usage Report</h6>
                    <p class="text-muted small">
                      Parking lot utilization patterns, peak hours, and occupancy trends.
                    </p>
                  </div>
                  <div class="col-md-4">
                    <h6>User Report</h6>
                    <p class="text-muted small">
                      User behavior analysis, frequent customers, and booking patterns.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .text-xs {
      font-size: 0.7rem;
    }

    .font-weight-bold {
      font-weight: 700;
    }

    .text-gray-800 {
      color: #5a5c69;
    }

    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .chart-placeholder canvas {
      display: none;
    }

    .progress {
      background-color: #e9ecef;
    }
  `]
})
export class AdminAnalyticsComponent implements OnInit, OnDestroy {
  loading = true;
  selectedDateRange = '30';
  startDate = '';
  endDate = '';
  granularity = 'day';
  
  // KPI Data
  totalRevenue = 15420.50;
  totalBookings = 1847;
  averageOccupancy = 68.5;
  averageDuration = 2.3;
  revenueGrowth = 12.5;
  bookingGrowth = 8.2;
  
  // Chart Data (mock)
  mockChartData = {
    revenue: [
      { date: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000), value: 250 },
      { date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), value: 380 },
      { date: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000), value: 420 },
      { date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), value: 300 },
      { date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), value: 450 },
      { date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), value: 380 }
    ],
    occupancy: [
      { name: 'Downtown Plaza', occupancy: 85 },
      { name: 'Airport Parking', occupancy: 72 },
      { name: 'Shopping Mall', occupancy: 45 },
      { name: 'University Campus', occupancy: 60 }
    ]
  };
  
  // Table Data
  topPerformingLots = [
    { name: 'Downtown Plaza Parking', revenue: 5420, bookings: 425 },
    { name: 'Airport Long-Term Parking', revenue: 4850, bookings: 312 },
    { name: 'Shopping Mall Parking', revenue: 3200, bookings: 520 },
    { name: 'University Campus Parking', revenue: 1950, bookings: 590 }
  ];
  
  peakHours = [
    { timeRange: '07:00 - 09:00', occupancy: 92, bookings: 245, revenue: 1850 },
    { timeRange: '12:00 - 14:00', occupancy: 78, bookings: 189, revenue: 1420 },
    { timeRange: '17:00 - 19:00', occupancy: 88, bookings: 267, revenue: 2010 },
    { timeRange: '20:00 - 22:00', occupancy: 45, bookings: 98, revenue: 740 }
  ];
  
  private destroy$ = new Subject<void>();

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.loadAnalytics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadAnalytics(): void {
    this.loading = true;
    
    const params: any = {
      granularity: this.granularity
    };
    
    if (this.startDate) {
      params.start_date = this.startDate;
    }
    
    if (this.endDate) {
      params.end_date = this.endDate;
    }

    this.adminService.getSystemAnalytics(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (analytics) => {
          // Process analytics data
          console.log('Analytics loaded:', analytics);
          this.loading = false;
        },
        error: (error) => {
          console.error('Error loading analytics:', error);
          this.loading = false;
          // Use demo data when backend is not available
        }
      });
  }

  onDateRangeChange(): void {
    const days = parseInt(this.selectedDateRange);
    const endDate = new Date();
    const startDate = new Date(endDate.getTime() - days * 24 * 60 * 60 * 1000);
    
    this.startDate = startDate.toISOString().split('T')[0];
    this.endDate = endDate.toISOString().split('T')[0];
    
    this.loadAnalytics();
  }

  generateReport(reportType: 'revenue' | 'usage' | 'users'): void {
    this.adminService.generateReport(reportType, {
      start_date: this.startDate,
      end_date: this.endDate,
      granularity: this.granularity
    })
    .pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (report) => {
        console.log(`${reportType} report generated:`, report);
        // Handle report download or display
        alert(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report generated successfully!`);
      },
      error: (error) => {
        console.error(`Error generating ${reportType} report:`, error);
        alert(`Failed to generate ${reportType} report`);
      }
    });
  }
}
