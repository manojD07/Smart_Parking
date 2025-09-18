import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Services
import { AnalyticsService, RevenueAnalytics, LotRevenue } from '../../../../core/services/analytics.service';
import { ParkingLotService, ParkingLot } from '../../../../core/services/parking-lot.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from '../shared/loading-state.component';
import { ChartPlaceholderComponent } from './shared/chart-placeholder.component';

@Component({
  selector: 'app-revenue-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingStateComponent, ChartPlaceholderComponent],
  template: `
    <div class="container-fluid">
      <!-- Header with Filters -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h3>
                <i class="fas fa-chart-line me-2 text-success"></i>
                Revenue Analytics
              </h3>
              <p class="text-muted mb-0">Track revenue performance and trends</p>
            </div>
            <div class="d-flex gap-2">
              <button 
                class="btn btn-outline-primary btn-sm"
                (click)="refreshData()"
                [disabled]="loading">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-outline-secondary btn-sm">
                <i class="fas fa-download me-1"></i>
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Date Range and Filters -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="row g-3">
                <div class="col-md-3">
                  <label class="form-label fw-semibold">Date Range</label>
                  <select class="form-select" [(ngModel)]="selectedPeriod" (ngModelChange)="onPeriodChange()">
                    <option value="today">Today</option>
                    <option value="week">Last 7 Days</option>
                    <option value="month">Last 30 Days</option>
                    <option value="year">Last Year</option>
                    <option value="custom">Custom Range</option>
                  </select>
                </div>
                
                <div class="col-md-3" *ngIf="selectedPeriod === 'custom'">
                  <label class="form-label fw-semibold">Start Date</label>
                  <input 
                    type="date" 
                    class="form-control"
                    [(ngModel)]="customStartDate"
                    (ngModelChange)="onCustomDateChange()">
                </div>
                
                <div class="col-md-3" *ngIf="selectedPeriod === 'custom'">
                  <label class="form-label fw-semibold">End Date</label>
                  <input 
                    type="date" 
                    class="form-control"
                    [(ngModel)]="customEndDate"
                    (ngModelChange)="onCustomDateChange()">
                </div>
                
                <div class="col-md-3">
                  <label class="form-label fw-semibold">Parking Lot</label>
                  <select class="form-select" [(ngModel)]="selectedLotId" (ngModelChange)="onLotFilterChange()">
                    <option value="">All Parking Lots</option>
                    <option *ngFor="let lot of parkingLots" [value]="lot.id">
                      {{ lot.name }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading && !revenueData" class="row">
        <div class="col-12">
          <app-loading-state 
            type="spinner" 
            loadingText="Loading revenue analytics..."
            size="lg">
          </app-loading-state>
        </div>
      </div>

      <!-- Revenue KPI Cards -->
      <div *ngIf="!loading && revenueData" class="row mb-4">
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ formatCurrency(revenueData.metrics.total_revenue) }}</h4>
                  <small>Total Revenue</small>
                </div>
                <i class="fas fa-rupee-sign fa-2x opacity-75"></i>
              </div>
              <div class="progress mt-2" style="height: 4px;">
                <div class="progress-bar bg-white" style="width: 100%"></div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ formatCurrency(revenueData.metrics.today_revenue) }}</h4>
                  <small>Today's Revenue</small>
                </div>
                <i class="fas fa-calendar-day fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  <i class="fas fa-arrow-up me-1"></i>
                  {{ revenueData.metrics.revenue_growth_daily.toFixed(1) }}% vs yesterday
                </small>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ formatCurrency(revenueData.metrics.average_revenue_per_booking) }}</h4>
                  <small>Avg per Booking</small>
                </div>
                <i class="fas fa-calculator fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  {{ revenueData.metrics.total_bookings }} total bookings
                </small>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-warning text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ formatCurrency(revenueData.metrics.week_revenue) }}</h4>
                  <small>This Week</small>
                </div>
                <i class="fas fa-chart-bar fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  <i class="fas fa-arrow-up me-1"></i>
                  {{ revenueData.metrics.revenue_growth_weekly.toFixed(1) }}% growth
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div *ngIf="!loading && revenueData" class="row mb-4">
        <!-- Daily Revenue Trends -->
        <div class="col-md-8 mb-3">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-chart-line me-2"></i>
                Revenue Trends
              </h5>
            </div>
            <div class="card-body">
              <div class="chart-container" style="height: 300px;">
                <app-chart-placeholder
                  title="Daily Revenue Trends"
                  subtitle="Revenue performance over time"
                  icon="fa-chart-line"
                  [dataPoints]="revenueData.daily_revenue.length">
                </app-chart-placeholder>
              </div>
            </div>
          </div>
        </div>

        <!-- Vehicle Revenue Breakdown -->
        <div class="col-md-4 mb-3">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-car me-2"></i>
                Vehicle Revenue
              </h5>
            </div>
            <div class="card-body">
              <div class="vehicle-revenue-stats">
                <!-- Car Revenue -->
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <div class="d-flex align-items-center">
                    <i class="fas fa-car fa-lg text-primary me-2"></i>
                    <div>
                      <div class="fw-semibold">Cars</div>
                      <small class="text-muted">{{ revenueData.vehicle_revenue.car.bookings }} bookings</small>
                    </div>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold text-success">{{ formatCurrency(revenueData.vehicle_revenue.car.revenue) }}</div>
                    <small class="text-muted">{{ revenueData.vehicle_revenue.car.percentage.toFixed(1) }}%</small>
                  </div>
                </div>
                
                <!-- Car Progress Bar -->
                <div class="progress mb-3" style="height: 8px;">
                  <div 
                    class="progress-bar bg-primary" 
                    [style.width.%]="revenueData.vehicle_revenue.car.percentage">
                  </div>
                </div>

                <!-- Bike Revenue -->
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <div class="d-flex align-items-center">
                    <i class="fas fa-motorcycle fa-lg text-success me-2"></i>
                    <div>
                      <div class="fw-semibold">Bikes</div>
                      <small class="text-muted">{{ revenueData.vehicle_revenue.bike.bookings }} bookings</small>
                    </div>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold text-success">{{ formatCurrency(revenueData.vehicle_revenue.bike.revenue) }}</div>
                    <small class="text-muted">{{ revenueData.vehicle_revenue.bike.percentage.toFixed(1) }}%</small>
                  </div>
                </div>
                
                <!-- Bike Progress Bar -->
                <div class="progress" style="height: 8px;">
                  <div 
                    class="progress-bar bg-success" 
                    [style.width.%]="revenueData.vehicle_revenue.bike.percentage">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Revenue by Lot Table -->
      <div *ngIf="!loading && lotRevenueData && lotRevenueData.length > 0" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-building me-2"></i>
                Revenue by Parking Lot
              </h5>
            </div>
            <div class="card-body">
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>Parking Lot</th>
                      <th>Total Revenue</th>
                      <th>Bookings</th>
                      <th>Avg per Booking</th>
                      <th>Revenue per Slot</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let lot of lotRevenueData; trackBy: trackByLotId">
                      <td>
                        <strong>{{ lot.lot_name }}</strong>
                      </td>
                      <td>
                        <span class="fw-bold text-success">{{ formatCurrency(lot.total_revenue) }}</span>
                      </td>
                      <td>
                        <span class="badge bg-primary">{{ lot.total_bookings }}</span>
                      </td>
                      <td>
                        {{ formatCurrency(lot.average_revenue_per_booking) }}
                      </td>
                      <td>
                        {{ formatCurrency(lot.revenue_per_slot) }}
                      </td>
                      <td>
                        <div class="progress" style="width: 100px; height: 20px;">
                          <div 
                            class="progress-bar"
                            [class]="getPerformanceClass(lot)"
                            [style.width.%]="getPerformancePercentage(lot)"
                            [title]="getPerformanceTooltip(lot)">
                          </div>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div *ngIf="!loading && (!revenueData || revenueData.metrics.total_revenue === 0)" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-body text-center py-5">
              <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
              <h5>No Revenue Data</h5>
              <p class="text-muted">No revenue data found for the selected period.</p>
              <button class="btn btn-primary" (click)="refreshData()">
                <i class="fas fa-sync-alt me-2"></i>Refresh Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .bg-gradient-success {
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    }

    .bg-gradient-primary {
      background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
    }

    .bg-gradient-info {
      background: linear-gradient(135deg, #17a2b8 0%, #007bff 100%);
    }

    .bg-gradient-warning {
      background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
    }

    .card {
      border-radius: 12px;
      border: 1px solid #e9ecef;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
      border-radius: 12px 12px 0 0 !important;
    }

    .chart-container {
      position: relative;
      width: 100%;
    }

    .vehicle-revenue-stats {
      padding: 0.5rem 0;
    }

    .progress {
      border-radius: 10px;
    }

    .progress-bar {
      border-radius: 10px;
    }

    .table th {
      border-top: none;
      font-weight: 600;
      color: #495057;
      background-color: #f8f9fa;
    }

    .table td {
      vertical-align: middle;
    }

    @media (max-width: 768px) {
      .table-responsive {
        border-radius: 8px;
      }
      
      .chart-container {
        height: 250px !important;
      }
      
      .vehicle-revenue-stats {
        padding: 0.25rem 0;
      }
    }
  `]
})
export class RevenueAnalyticsComponent implements OnInit {
  // Data
  revenueData: RevenueAnalytics | null = null;
  lotRevenueData: LotRevenue[] = [];
  parkingLots: ParkingLot[] = [];

  // Filters
  selectedPeriod: string = 'month';
  selectedLotId: string = '';
  customStartDate: string = '';
  customEndDate: string = '';

  // UI State
  loading = false;

  constructor(
    private analyticsService: AnalyticsService,
    private parkingLotService: ParkingLotService,
    private toastService: ToastService
  ) {}

  async ngOnInit(): Promise<void> {
    await this.loadParkingLots();
    await this.loadRevenueData();
  }

  async loadParkingLots(): Promise<void> {
    try {
      this.parkingLots = await this.parkingLotService.getAllLots({ is_active: true });
    } catch (error) {
      console.error('Error loading parking lots:', error);
      this.toastService.showError('Failed to load parking lots');
    }
  }

  async loadRevenueData(): Promise<void> {
    try {
      this.loading = true;
      
      const dateRange = this.getDateRange();
      console.log('📊 Loading revenue data for:', dateRange);
      
      // Load main revenue analytics
      this.revenueData = await this.analyticsService.getRevenueAnalytics(
        dateRange.start, 
        dateRange.end, 
        this.selectedLotId || undefined
      );
      
      // Load revenue by lot (only if not filtering by specific lot)
      if (!this.selectedLotId) {
        this.lotRevenueData = await this.analyticsService.getRevenueByLot(
          dateRange.start, 
          dateRange.end
        );
      } else {
        this.lotRevenueData = [];
      }
      
      console.log('📊 Revenue data loaded:', this.revenueData);
      
    } catch (error) {
      console.error('Error loading revenue data:', error);
      this.toastService.showError('Failed to load revenue analytics');
      this.revenueData = null;
      this.lotRevenueData = [];
    } finally {
      this.loading = false;
    }
  }

  async refreshData(): Promise<void> {
    await this.loadRevenueData();
    this.toastService.showSuccess('Revenue data refreshed');
  }

  onPeriodChange(): void {
    if (this.selectedPeriod !== 'custom') {
      this.loadRevenueData();
    }
  }

  onCustomDateChange(): void {
    if (this.customStartDate && this.customEndDate) {
      this.loadRevenueData();
    }
  }

  onLotFilterChange(): void {
    this.loadRevenueData();
  }

  private getDateRange(): { start: string; end: string } {
    if (this.selectedPeriod === 'custom' && this.customStartDate && this.customEndDate) {
      return {
        start: this.customStartDate,
        end: this.customEndDate
      };
    }
    
    return this.analyticsService.getDateRange(this.selectedPeriod as any);
  }

  // Helper methods
  formatCurrency(amount: number): string {
    return this.analyticsService.formatCurrency(amount);
  }

  trackByLotId(index: number, lot: LotRevenue): string {
    return lot.lot_id;
  }

  getPerformancePercentage(lot: LotRevenue): number {
    // Calculate performance based on revenue per slot compared to average
    if (!this.lotRevenueData || this.lotRevenueData.length === 0) return 0;
    
    const avgRevenuePerSlot = this.lotRevenueData.reduce((sum, l) => sum + l.revenue_per_slot, 0) / this.lotRevenueData.length;
    
    if (avgRevenuePerSlot === 0) return 0;
    
    return Math.min(100, (lot.revenue_per_slot / avgRevenuePerSlot) * 100);
  }

  getPerformanceClass(lot: LotRevenue): string {
    const percentage = this.getPerformancePercentage(lot);
    
    if (percentage >= 80) return 'bg-success';
    if (percentage >= 60) return 'bg-info';
    if (percentage >= 40) return 'bg-warning';
    return 'bg-danger';
  }

  getPerformanceTooltip(lot: LotRevenue): string {
    const percentage = this.getPerformancePercentage(lot);
    return `Performance: ${percentage.toFixed(1)}% of average`;
  }
}
