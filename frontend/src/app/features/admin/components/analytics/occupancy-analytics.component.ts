import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// Services
import { AnalyticsService, OccupancyAnalytics, UtilizationAnalytics } from '../../services/analytics.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from '../shared/loading-state.component';
import { ChartPlaceholderComponent } from './shared/chart-placeholder.component';

@Component({
  selector: 'app-occupancy-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingStateComponent, ChartPlaceholderComponent],
  template: `
    <div class="container-fluid">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h3>
                <i class="fas fa-chart-area me-2 text-info"></i>
                Occupancy & Utilization Analytics
              </h3>
              <p class="text-muted mb-0">Monitor space utilization and occupancy patterns</p>
            </div>
            <div class="d-flex gap-2">
              <select 
                class="form-select form-select-sm" 
                [(ngModel)]="selectedPeriod" 
                (change)="onPeriodChange()"
                style="width: auto;">
                <option value="weekly">Last 7 days</option>
                <option value="monthly">Last 30 days</option>
              </select>
              <button 
                class="btn btn-outline-primary btn-sm"
                (click)="refreshData()"
                [disabled]="loading">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <app-loading-state *ngIf="loading" message="Loading occupancy data..."></app-loading-state>

      <!-- Error State -->
      <div class="alert alert-danger" *ngIf="errorMessage && !loading">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ errorMessage }}
        <button class="btn btn-outline-danger btn-sm ms-2" (click)="refreshData()">
          Try Again
        </button>
      </div>

      <!-- Content -->
      <div *ngIf="!loading && !errorMessage">
        
        <!-- Key Metrics Cards -->
        <div class="row mb-4" *ngIf="utilizationData">
          <div class="col-md-4 mb-3">
            <div class="card border-info">
              <div class="card-body text-center">
                <div class="d-flex justify-content-center align-items-center mb-2">
                  <i class="fas fa-chart-pie fa-2x text-info me-3"></i>
                  <div>
                    <h3 class="mb-0 text-info">{{ utilizationData.overall_utilization_rate | percent:'1.1-1' }}</h3>
                    <small class="text-muted">Overall Utilization</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-3">
            <div class="card border-success">
              <div class="card-body text-center">
                <div class="d-flex justify-content-center align-items-center mb-2">
                  <i class="fas fa-expand-arrows-alt fa-2x text-success me-3"></i>
                  <div>
                    <h3 class="mb-0 text-success">{{ utilizationData.space_efficiency | percent:'1.1-1' }}</h3>
                    <small class="text-muted">Space Efficiency</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-4 mb-3">
            <div class="card border-warning">
              <div class="card-body text-center">
                <div class="d-flex justify-content-center align-items-center mb-2">
                  <i class="fas fa-clock fa-2x text-warning me-3"></i>
                  <div>
                    <h3 class="mb-0 text-warning">{{ getPeakHour() }}</h3>
                    <small class="text-muted">Peak Hour</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Charts Section -->
        <div class="row">
          
          <!-- Hourly Utilization Chart -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-chart-line me-2"></i>
                  Hourly Utilization Trends
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="utilizationData?.hourly_breakdown || []"
                  type="line"
                  height="300px"
                  [options]="{
                    title: 'Utilization by Hour',
                    xAxis: 'hour',
                    yAxis: 'utilization_rate',
                    color: '#17a2b8'
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

          <!-- Occupancy Heatmap -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-th me-2"></i>
                  Occupancy Heatmap
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="occupancyData?.heatmap || []"
                  type="heatmap"
                  height="300px"
                  [options]="{
                    title: 'Hourly Occupancy Pattern',
                    colorScale: ['#e3f2fd', '#1976d2']
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

          <!-- Daily Utilization -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-calendar-day me-2"></i>
                  Daily Utilization
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="utilizationData?.daily_breakdown || []"
                  type="bar"
                  height="300px"
                  [options]="{
                    title: 'Utilization by Day',
                    xAxis: 'date',
                    yAxis: 'utilization_rate',
                    color: '#28a745'
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

          <!-- Peak Hours Analysis -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-fire me-2"></i>
                  Peak Hours Analysis
                </h5>
              </div>
              <div class="card-body">
                <div class="table-responsive" *ngIf="occupancyData && occupancyData.peak_hours && occupancyData.peak_hours.length > 0">
                  <table class="table table-sm">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Utilization</th>
                        <th>Occupancy</th>
                        <th>Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let peak of (occupancyData?.peak_hours || []).slice(0, 10)">
                        <td>
                          <strong>{{ formatHour(peak.hour) }}</strong>
                        </td>
                        <td>
                          <span class="badge bg-info">
                            {{ peak.utilization_rate | percent:'1.0-0' }}
                          </span>
                        </td>
                        <td>
                          <span class="badge bg-primary">
                            {{ peak.occupied_slots }}/{{ peak.total_slots }}
                          </span>
                        </td>
                        <td>
                          <i class="fas fa-arrow-up text-success" *ngIf="peak.trend === 'up'"></i>
                          <i class="fas fa-arrow-down text-danger" *ngIf="peak.trend === 'down'"></i>
                          <i class="fas fa-minus text-muted" *ngIf="peak.trend === 'stable'"></i>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div *ngIf="!occupancyData?.peak_hours?.length" class="text-center text-muted py-4">
                  <i class="fas fa-chart-line fa-3x mb-3 opacity-25"></i>
                  <p>No peak hours data available</p>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Utilization Insights -->
        <div class="row" *ngIf="utilizationData">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-lightbulb me-2"></i>
                  Utilization Insights
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <h6 class="text-muted">Performance Indicators</h6>
                    <ul class="list-unstyled">
                      <li class="mb-2">
                        <span class="badge bg-info me-2">Utilization Rate</span>
                        {{ utilizationData.overall_utilization_rate | percent:'1.1-1' }}
                        <span class="text-muted ms-2">(Target: 85%)</span>
                      </li>
                      <li class="mb-2">
                        <span class="badge bg-success me-2">Space Efficiency</span>
                        {{ utilizationData.space_efficiency | percent:'1.1-1' }}
                        <span class="text-muted ms-2">(Target: 90%)</span>
                      </li>
                    </ul>
                  </div>
                  <div class="col-md-6">
                    <h6 class="text-muted">Recommendations</h6>
                    <div class="alert alert-light">
                      <small>
                        <i class="fas fa-info-circle me-1"></i>
                        <span *ngIf="utilizationData.overall_utilization_rate < 0.6">
                          Consider implementing dynamic pricing to increase utilization during off-peak hours.
                        </span>
                        <span *ngIf="utilizationData.overall_utilization_rate >= 0.6 && utilizationData.overall_utilization_rate < 0.85">
                          Good utilization levels. Monitor peak hours for optimization opportunities.
                        </span>
                        <span *ngIf="utilizationData.overall_utilization_rate >= 0.85">
                          Excellent utilization! Consider expanding capacity during peak periods.
                        </span>
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
  `,
  styles: [`
    .card {
      box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
      border: 1px solid rgba(0, 0, 0, 0.125);
    }
    
    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid rgba(0, 0, 0, 0.125);
    }
    
    .table th {
      font-weight: 600;
      font-size: 0.875rem;
      color: #6c757d;
    }
    
    .badge {
      font-size: 0.75rem;
    }
    
    .alert-light {
      background-color: #f8f9fa;
      border-color: #dee2e6;
      color: #6c757d;
    }
  `]
})
export class OccupancyAnalyticsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Component state
  loading = true;
  errorMessage = '';
  selectedPeriod: 'weekly' | 'monthly' = 'weekly';
  
  // Analytics data
  occupancyData: OccupancyAnalytics | null = null;
  utilizationData: UtilizationAnalytics | null = null;

  constructor(
    private analyticsService: AnalyticsService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.loadOccupancyData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load occupancy and utilization data
   */
  loadOccupancyData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.analyticsService.getDateRange(this.selectedPeriod);
    
    // Load both occupancy and utilization data
    Promise.all([
      this.analyticsService.getOccupancyAnalytics(dateRange.start, dateRange.end).toPromise(),
      this.analyticsService.getUtilizationAnalytics(dateRange.start, dateRange.end).toPromise()
    ])
    .then(([occupancy, utilization]) => {
      this.occupancyData = occupancy || null;
      this.utilizationData = utilization || null;
      this.loading = false;
    })
    .catch(error => {
      console.error('Failed to load occupancy data:', error);
      this.errorMessage = 'Failed to load occupancy data. Please try again.';
      this.loading = false;
      this.toastService.showError('Failed to load occupancy analytics');
    });
  }

  /**
   * Handle period change
   */
  onPeriodChange(): void {
    this.loadOccupancyData();
  }

  /**
   * Refresh data
   */
  refreshData(): void {
    this.loadOccupancyData();
  }

  /**
   * Get peak hour from data
   */
  getPeakHour(): string {
    if (!this.occupancyData?.peak_hours?.length) {
      return 'N/A';
    }
    
    const peakHour = this.occupancyData.peak_hours[0];
    return this.formatHour(peakHour.hour);
  }

  /**
   * Format hour for display
   */
  formatHour(hour: number): string {
    if (hour === 0) return '12:00 AM';
    if (hour === 12) return '12:00 PM';
    if (hour < 12) return `${hour}:00 AM`;
    return `${hour - 12}:00 PM`;
  }
}
