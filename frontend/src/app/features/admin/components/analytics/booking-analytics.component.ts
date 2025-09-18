import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Services
import { AnalyticsService, BookingAnalytics, BookingTrend, BookingPatterns } from '../../../../core/services/analytics.service';
import { ParkingLotService, ParkingLot } from '../../../../core/services/parking-lot.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from '../shared/loading-state.component';
import { ChartPlaceholderComponent } from './shared/chart-placeholder.component';

@Component({
  selector: 'app-booking-analytics',
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
                <i class="fas fa-ticket-alt me-2 text-primary"></i>
                Booking Analytics
              </h3>
              <p class="text-muted mb-0">Track booking trends, patterns, and performance</p>
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
      <div *ngIf="loading && !bookingData" class="row">
        <div class="col-12">
          <app-loading-state 
            type="spinner" 
            loadingText="Loading booking analytics..."
            size="lg">
          </app-loading-state>
        </div>
      </div>

      <!-- Booking KPI Cards -->
      <div *ngIf="!loading && bookingData" class="row mb-4">
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingData.total_bookings.toLocaleString() }}</h4>
                  <small>Total Bookings</small>
                </div>
                <i class="fas fa-ticket-alt fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  <i class="fas fa-arrow-up me-1"></i>
                  {{ bookingData.booking_growth.toFixed(1) }}% growth
                </small>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-3 mb-3">
          <div class="card bg-gradient-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h4 class="mb-0">{{ bookingData.success_rate.toFixed(1) }}%</h4>
                  <small>Success Rate</small>
                </div>
                <i class="fas fa-check-circle fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  {{ (bookingData.status_breakdown.completed || 0).toLocaleString() }} completed bookings
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
                  <h4 class="mb-0">{{ bookingData.cancellation_rate.toFixed(1) }}%</h4>
                  <small>Cancellation Rate</small>
                </div>
                <i class="fas fa-times-circle fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  {{ (bookingData.status_breakdown.cancelled || 0).toLocaleString() }} cancelled bookings
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
                  <h4 class="mb-0">{{ formatDuration(bookingData.average_duration) }}</h4>
                  <small>Avg Duration</small>
                </div>
                <i class="fas fa-clock fa-2x opacity-75"></i>
              </div>
              <div class="mt-1">
                <small class="opacity-75">
                  Per booking session
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts and Analysis Row -->
      <div *ngIf="!loading && bookingData" class="row mb-4">
        <!-- Booking Trends Chart -->
        <div class="col-md-8 mb-3">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-chart-area me-2"></i>
                Booking Trends
              </h5>
            </div>
            <div class="card-body">
              <div class="chart-container" style="height: 300px;">
                <app-chart-placeholder
                  title="Daily Booking Trends"
                  subtitle="Booking volume and status over time"
                  icon="fa-chart-area"
                  [dataPoints]="bookingData.trends.length">
                </app-chart-placeholder>
              </div>
            </div>
          </div>
        </div>

        <!-- Status Breakdown -->
        <div class="col-md-4 mb-3">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-chart-pie me-2"></i>
                Status Breakdown
              </h5>
            </div>
            <div class="card-body">
              <div class="status-breakdown">
                <div *ngFor="let status of getStatusEntries()" class="d-flex justify-content-between align-items-center mb-3">
                  <div class="d-flex align-items-center">
                    <i class="fas me-2" [class]="getStatusIcon(status.key)" [style.color]="getStatusColor(status.key)"></i>
                    <div>
                      <div class="fw-semibold text-capitalize">{{ status.key }}</div>
                      <small class="text-muted">{{ getStatusPercentage(status.value) }}%</small>
                    </div>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold">{{ status.value.toLocaleString() }}</div>
                  </div>
                </div>
                
                <!-- Status Progress Bars -->
                <div *ngFor="let status of getStatusEntries()" class="mb-2">
                  <div class="progress" style="height: 6px;">
                    <div 
                      class="progress-bar" 
                      [style.background-color]="getStatusColor(status.key)"
                      [style.width.%]="getStatusPercentage(status.value)">
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Patterns and Insights Row -->
      <div *ngIf="!loading && bookingData" class="row mb-4">
        <!-- Booking Patterns -->
        <div class="col-md-6 mb-3">
          <div class="card">
            <div class="card-header">
              <h5 class="mb-0">
                <i class="fas fa-brain me-2"></i>
                Booking Patterns
              </h5>
            </div>
            <div class="card-body">
              <div class="patterns-grid">
                <!-- Peak Hours -->
                <div class="pattern-item mb-3">
                  <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-clock text-primary me-2"></i>
                    <strong>Peak Hours</strong>
                  </div>
                  <div class="d-flex gap-2 flex-wrap">
                    <span *ngFor="let hour of bookingData.patterns.peak_hours" 
                          class="badge bg-primary">
                      {{ formatHour(hour) }}
                    </span>
                  </div>
                </div>

                <!-- Peak Days -->
                <div class="pattern-item mb-3">
                  <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-calendar-alt text-success me-2"></i>
                    <strong>Peak Days</strong>
                  </div>
                  <div class="d-flex gap-2 flex-wrap">
                    <span *ngFor="let day of bookingData.patterns.peak_days" 
                          class="badge bg-success text-capitalize">
                      {{ day }}
                    </span>
                  </div>
                </div>

                <!-- Popular Vehicle -->
                <div class="pattern-item mb-3">
                  <div class="d-flex align-items-center mb-2">
                    <i class="fas" [class]="getVehicleIcon(bookingData.patterns.most_popular_vehicle)" class="text-info me-2"></i>
                    <strong>Most Popular Vehicle</strong>
                  </div>
                  <span class="badge bg-info text-capitalize">
                    {{ bookingData.patterns.most_popular_vehicle }}
                  </span>
                </div>

                <!-- Average Duration -->
                <div class="pattern-item">
                  <div class="d-flex align-items-center mb-2">
                    <i class="fas fa-hourglass-half text-warning me-2"></i>
                    <strong>Average Duration</strong>
                  </div>
                  <span class="badge bg-warning">
                    {{ formatDuration(bookingData.patterns.average_duration) }}
                  </span>
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
                Vehicle Type Analysis
              </h5>
            </div>
            <div class="card-body">
              <div class="vehicle-breakdown">
                <div *ngFor="let vehicle of getVehicleEntries()" class="d-flex justify-content-between align-items-center mb-3">
                  <div class="d-flex align-items-center">
                    <i class="fas fa-lg me-2" [class]="getVehicleIcon(vehicle.key)" [style.color]="getVehicleColor(vehicle.key)"></i>
                    <div>
                      <div class="fw-semibold text-capitalize">{{ vehicle.key }}</div>
                      <small class="text-muted">{{ getVehiclePercentage(vehicle.value) }}% of bookings</small>
                    </div>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold">{{ vehicle.value.toLocaleString() }}</div>
                  </div>
                </div>
                
                <!-- Vehicle Progress Bars -->
                <div *ngFor="let vehicle of getVehicleEntries()" class="mb-2">
                  <div class="progress" style="height: 8px;">
                    <div 
                      class="progress-bar" 
                      [style.background-color]="getVehicleColor(vehicle.key)"
                      [style.width.%]="getVehiclePercentage(vehicle.value)">
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div *ngIf="!loading && (!bookingData || bookingData.total_bookings === 0)" class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-body text-center py-5">
              <i class="fas fa-ticket-alt fa-3x text-muted mb-3"></i>
              <h5>No Booking Data</h5>
              <p class="text-muted">No booking data found for the selected period.</p>
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
    .bg-gradient-primary {
      background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
    }

    .bg-gradient-success {
      background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    }

    .bg-gradient-warning {
      background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
    }

    .bg-gradient-info {
      background: linear-gradient(135deg, #17a2b8 0%, #007bff 100%);
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

    .status-breakdown,
    .vehicle-breakdown {
      padding: 0.5rem 0;
    }

    .patterns-grid {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .pattern-item {
      padding: 0.75rem;
      background-color: #f8f9fa;
      border-radius: 8px;
      border-left: 4px solid #007bff;
    }

    .progress {
      border-radius: 10px;
    }

    .progress-bar {
      border-radius: 10px;
    }

    .badge {
      font-size: 0.75rem;
      padding: 0.375rem 0.75rem;
    }

    @media (max-width: 768px) {
      .patterns-grid {
        gap: 0.75rem;
      }
      
      .pattern-item {
        padding: 0.5rem;
      }
      
      .chart-container {
        height: 250px !important;
      }
    }
  `]
})
export class BookingAnalyticsComponent implements OnInit {
  // Data
  bookingData: BookingAnalytics | null = null;
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
    await this.loadBookingData();
  }

  async loadParkingLots(): Promise<void> {
    try {
      this.parkingLots = await this.parkingLotService.getAllLots({ is_active: true });
    } catch (error) {
      console.error('Error loading parking lots:', error);
      this.toastService.showError('Failed to load parking lots');
    }
  }

  async loadBookingData(): Promise<void> {
    try {
      this.loading = true;
      
      const dateRange = this.getDateRange();
      console.log('📊 Loading booking data for:', dateRange);
      
      this.bookingData = await this.analyticsService.getBookingAnalytics(
        dateRange.start, 
        dateRange.end, 
        this.selectedLotId || undefined
      );
      
      console.log('📊 Booking data loaded:', this.bookingData);
      
    } catch (error) {
      console.error('Error loading booking data:', error);
      this.toastService.showError('Failed to load booking analytics');
      this.bookingData = null;
    } finally {
      this.loading = false;
    }
  }

  async refreshData(): Promise<void> {
    await this.loadBookingData();
    this.toastService.showSuccess('Booking data refreshed');
  }

  onPeriodChange(): void {
    if (this.selectedPeriod !== 'custom') {
      this.loadBookingData();
    }
  }

  onCustomDateChange(): void {
    if (this.customStartDate && this.customEndDate) {
      this.loadBookingData();
    }
  }

  onLotFilterChange(): void {
    this.loadBookingData();
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

  // Helper methods for template
  formatDuration(hours: number): string {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    } else if (hours < 24) {
      return `${hours.toFixed(1)}h`;
    } else {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return `${days}d ${remainingHours.toFixed(1)}h`;
    }
  }

  formatHour(hour: number): string {
    const date = new Date();
    date.setHours(hour, 0, 0, 0);
    return date.toLocaleTimeString('en-IN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      hour12: true 
    });
  }

  getStatusEntries(): { key: string; value: number }[] {
    if (!this.bookingData) return [];
    
    return Object.entries(this.bookingData.status_breakdown)
      .map(([key, value]) => ({ key, value }))
      .sort((a, b) => b.value - a.value);
  }

  getVehicleEntries(): { key: string; value: number }[] {
    if (!this.bookingData) return [];
    
    return Object.entries(this.bookingData.vehicle_breakdown)
      .map(([key, value]) => ({ key, value }))
      .sort((a, b) => b.value - a.value);
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'confirmed': return 'fa-check';
      case 'active': return 'fa-play';
      case 'completed': return 'fa-check-circle';
      case 'cancelled': return 'fa-times-circle';
      default: return 'fa-question-circle';
    }
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'confirmed': return '#17a2b8';
      case 'active': return '#28a745';
      case 'completed': return '#007bff';
      case 'cancelled': return '#dc3545';
      default: return '#6c757d';
    }
  }

  getVehicleIcon(vehicle: string): string {
    switch (vehicle) {
      case 'car': return 'fa-car';
      case 'bike': return 'fa-motorcycle';
      default: return 'fa-vehicle';
    }
  }

  getVehicleColor(vehicle: string): string {
    switch (vehicle) {
      case 'car': return '#007bff';
      case 'bike': return '#28a745';
      default: return '#6c757d';
    }
  }

  getStatusPercentage(value: number): number {
    if (!this.bookingData || this.bookingData.total_bookings === 0) return 0;
    return (value / this.bookingData.total_bookings) * 100;
  }

  getVehiclePercentage(value: number): number {
    if (!this.bookingData || this.bookingData.total_bookings === 0) return 0;
    return (value / this.bookingData.total_bookings) * 100;
  }
}
