import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// Services
import { AnalyticsService, PerformanceMetrics, BookingPatterns } from '../../services/analytics.service';
import { ToastService } from '../../../../core/services/toast.service';

// Components
import { LoadingStateComponent } from '../shared/loading-state.component';
import { ChartPlaceholderComponent } from './shared/chart-placeholder.component';

@Component({
  selector: 'app-performance-metrics',
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
                <i class="fas fa-tachometer-alt me-2 text-warning"></i>
                Performance Metrics & KPIs
              </h3>
              <p class="text-muted mb-0">Monitor system performance and key performance indicators</p>
            </div>
            <div class="d-flex gap-2">
              <select 
                class="form-select form-select-sm" 
                [(ngModel)]="selectedPeriod" 
                (change)="onPeriodChange()"
                style="width: auto;">
                <option value="weekly">Last 7 days</option>
                <option value="monthly">Last 30 days</option>
                <option value="quarterly">Last 3 months</option>
              </select>
              <button 
                class="btn btn-outline-primary btn-sm"
                (click)="refreshData()"
                [disabled]="loading">
                <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-outline-secondary btn-sm">
                <i class="fas fa-download me-1"></i>
                Export Report
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <app-loading-state *ngIf="loading" message="Loading performance data..."></app-loading-state>

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
        
        <!-- KPI Cards -->
        <div class="row mb-4" *ngIf="performanceData">
          <div class="col-lg-3 col-md-6 mb-3">
            <div class="card bg-gradient-primary text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <h4 class="mb-0">{{ getKPI('booking_completion_rate') | percent:'1.1-1' }}</h4>
                    <p class="mb-0 small">Booking Completion</p>
                  </div>
                  <i class="fas fa-check-circle fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-3">
            <div class="card bg-gradient-success text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <h4 class="mb-0">{{ getKPI('average_response_time') }}ms</h4>
                    <p class="mb-0 small">Avg Response Time</p>
                  </div>
                  <i class="fas fa-stopwatch fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-3">
            <div class="card bg-gradient-info text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <h4 class="mb-0">{{ getKPI('customer_satisfaction') | number:'1.1-1' }}/5</h4>
                    <p class="mb-0 small">Customer Satisfaction</p>
                  </div>
                  <i class="fas fa-star fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-3">
            <div class="card bg-gradient-warning text-white">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <h4 class="mb-0">{{ getKPI('system_uptime') | percent:'1.2-2' }}</h4>
                    <p class="mb-0 small">System Uptime</p>
                  </div>
                  <i class="fas fa-server fa-2x opacity-75"></i>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance Charts -->
        <div class="row mb-4">
          
          <!-- Booking Trends -->
          <div class="col-lg-8 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-chart-line me-2"></i>
                  Booking Performance Trends
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="bookingPatterns?.booking_patterns?.trends || []"
                  type="line"
                  height="350px"
                  [options]="{
                    title: 'Booking Volume & Success Rate Over Time',
                    series: [
                      { name: 'Total Bookings', type: 'column', yAxis: 0 },
                      { name: 'Success Rate', type: 'line', yAxis: 1 }
                    ]
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

          <!-- Performance Metrics -->
          <div class="col-lg-4 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-gauge-high me-2"></i>
                  Performance Score
                </h5>
              </div>
              <div class="card-body text-center">
                <div class="performance-gauge mb-3">
                  <div class="performance-score">
                    <h2 class="text-success">{{ getOverallPerformanceScore() }}</h2>
                    <p class="text-muted">Overall Score</p>
                  </div>
                </div>
                <div class="performance-breakdown">
                  <div class="row text-center">
                    <div class="col-6 border-end">
                      <h6 class="text-primary">{{ getKPI('efficiency_score') | number:'1.0-0' }}</h6>
                      <small class="text-muted">Efficiency</small>
                    </div>
                    <div class="col-6">
                      <h6 class="text-info">{{ getKPI('reliability_score') | number:'1.0-0' }}</h6>
                      <small class="text-muted">Reliability</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Booking Patterns Analysis -->
        <div class="row mb-4" *ngIf="bookingPatterns">
          
          <!-- Vehicle Type Distribution -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-car me-2"></i>
                  Vehicle Type Distribution
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="bookingPatterns.vehicle_analytics?.breakdown || []"
                  type="donut"
                  height="300px"
                  [options]="{
                    title: 'Bookings by Vehicle Type',
                    colors: ['#007bff', '#28a745', '#ffc107', '#dc3545']
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

          <!-- Duration Patterns -->
          <div class="col-lg-6 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-clock me-2"></i>
                  Booking Duration Patterns
                </h5>
              </div>
              <div class="card-body">
                <app-chart-placeholder 
                  [data]="bookingPatterns.duration_patterns?.distribution || []"
                  type="bar"
                  height="300px"
                  [options]="{
                    title: 'Most Popular Duration Ranges',
                    xAxis: 'duration_range',
                    yAxis: 'booking_count',
                    color: '#17a2b8'
                  }">
                </app-chart-placeholder>
              </div>
            </div>
          </div>

        </div>

        <!-- Performance Insights & Recommendations -->
        <div class="row">
          <div class="col-lg-8 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-lightbulb me-2"></i>
                  Performance Insights
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <h6 class="text-muted">Key Findings</h6>
                    <ul class="list-unstyled">
                      <li class="mb-2" *ngFor="let insight of getPerformanceInsights()">
                        <span [class]="'badge me-2 ' + insight.type">{{ insight.category }}</span>
                        {{ insight.message }}
                      </li>
                    </ul>
                  </div>
                  <div class="col-md-6">
                    <h6 class="text-muted">Recommendations</h6>
                    <div class="recommendations">
                      <div class="alert alert-info" *ngFor="let rec of getRecommendations()">
                        <small>
                          <i [class]="'fas ' + rec.icon + ' me-1'"></i>
                          {{ rec.message }}
                        </small>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Quick Stats -->
          <div class="col-lg-4 mb-4">
            <div class="card">
              <div class="card-header">
                <h5 class="card-title mb-0">
                  <i class="fas fa-chart-simple me-2"></i>
                  Quick Stats
                </h5>
              </div>
              <div class="card-body">
                <div class="stats-list">
                  <div class="stat-item d-flex justify-content-between mb-3">
                    <span class="text-muted">Peak Hour Efficiency</span>
                    <span class="fw-bold">{{ getKPI('peak_hour_efficiency') | percent:'1.0-0' }}</span>
                  </div>
                  <div class="stat-item d-flex justify-content-between mb-3">
                    <span class="text-muted">Off-Peak Utilization</span>
                    <span class="fw-bold">{{ getKPI('off_peak_utilization') | percent:'1.0-0' }}</span>
                  </div>
                  <div class="stat-item d-flex justify-content-between mb-3">
                    <span class="text-muted">Avg Booking Duration</span>
                    <span class="fw-bold">{{ getKPI('avg_booking_duration') }} min</span>
                  </div>
                  <div class="stat-item d-flex justify-content-between mb-3">
                    <span class="text-muted">User Retention Rate</span>
                    <span class="fw-bold">{{ getKPI('user_retention_rate') | percent:'1.0-0' }}</span>
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
    .bg-gradient-primary {
      background: linear-gradient(45deg, #007bff, #0056b3);
    }
    
    .bg-gradient-success {
      background: linear-gradient(45deg, #28a745, #1e7e34);
    }
    
    .bg-gradient-info {
      background: linear-gradient(45deg, #17a2b8, #117a8b);
    }
    
    .bg-gradient-warning {
      background: linear-gradient(45deg, #ffc107, #d39e00);
    }
    
    .performance-gauge {
      position: relative;
      width: 120px;
      height: 120px;
      margin: 0 auto;
      border: 8px solid #e9ecef;
      border-radius: 50%;
      border-top-color: #28a745;
      animation: spin 2s linear infinite;
    }
    
    .performance-score {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    .recommendations .alert {
      margin-bottom: 0.5rem;
      padding: 0.5rem;
    }
    
    .stat-item {
      border-bottom: 1px solid #e9ecef;
      padding-bottom: 0.75rem;
    }
    
    .stat-item:last-child {
      border-bottom: none;
      margin-bottom: 0 !important;
    }
  `]
})
export class PerformanceMetricsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Component state
  loading = true;
  errorMessage = '';
  selectedPeriod: 'weekly' | 'monthly' | 'quarterly' = 'monthly';
  
  // Analytics data
  performanceData: PerformanceMetrics | null = null;
  bookingPatterns: BookingPatterns | null = null;

  constructor(
    private analyticsService: AnalyticsService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.loadPerformanceData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load performance metrics and booking patterns
   */
  loadPerformanceData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.analyticsService.getDateRange(this.selectedPeriod);
    
    Promise.all([
      this.analyticsService.getPerformanceMetrics(dateRange.start, dateRange.end).toPromise(),
      this.analyticsService.getBookingPatterns(dateRange.start, dateRange.end).toPromise()
    ])
    .then(([performance, patterns]) => {
      this.performanceData = performance || null;
      this.bookingPatterns = patterns || null;
      this.loading = false;
    })
    .catch(error => {
      console.error('Failed to load performance data:', error);
      this.errorMessage = 'Failed to load performance data. Please try again.';
      this.loading = false;
      this.toastService.showError('Failed to load performance metrics');
    });
  }

  /**
   * Handle period change
   */
  onPeriodChange(): void {
    this.loadPerformanceData();
  }

  /**
   * Refresh data
   */
  refreshData(): void {
    this.loadPerformanceData();
  }

  /**
   * Get KPI value by key
   */
  getKPI(key: string): number {
    if (!this.performanceData?.performance_benchmarks) {
      return 0;
    }
    
    // Use actual performance data when available
    if (this.performanceData) {
      const value = (this.performanceData as any)[key];
      if (value !== undefined) {
        return value;
      }
    }
    
    // Default values for when data is not available
    const defaultValues: { [key: string]: number } = {
      booking_completion_rate: 0.0,
      average_response_time: 0,
      customer_satisfaction: 0.0,
      system_uptime: 0.0,
      efficiency_score: 0,
      reliability_score: 0,
      peak_hour_efficiency: 0.0,
      off_peak_utilization: 0.0,
      avg_booking_duration: 0,
      user_retention_rate: 0.0
    };
    
    return defaultValues[key] || 0;
  }

  /**
   * Calculate overall performance score
   */
  getOverallPerformanceScore(): string {
    const efficiency = this.getKPI('efficiency_score');
    const reliability = this.getKPI('reliability_score');
    const satisfaction = this.getKPI('customer_satisfaction') * 20; // Convert to 100 scale
    
    const score = (efficiency + reliability + satisfaction) / 3;
    return score.toFixed(0);
  }

  /**
   * Get performance insights
   */
  getPerformanceInsights(): any[] {
    const insights = [];
    
    const completionRate = this.getKPI('booking_completion_rate');
    if (completionRate > 0.9) {
      insights.push({
        category: 'Booking Success',
        type: 'bg-success',
        message: 'Excellent booking completion rate indicates smooth user experience'
      });
    }
    
    const responseTime = this.getKPI('average_response_time');
    if (responseTime < 200) {
      insights.push({
        category: 'Performance',
        type: 'bg-success',
        message: 'System response time is within optimal range'
      });
    } else if (responseTime > 500) {
      insights.push({
        category: 'Performance',
        type: 'bg-warning',
        message: 'Response time could be improved for better user experience'
      });
    }
    
    const uptime = this.getKPI('system_uptime');
    if (uptime > 0.995) {
      insights.push({
        category: 'Reliability',
        type: 'bg-success',
        message: 'System uptime exceeds industry standards'
      });
    }
    
    return insights;
  }

  /**
   * Get actionable recommendations
   */
  getRecommendations(): any[] {
    const recommendations = [];
    
    const peakEfficiency = this.getKPI('peak_hour_efficiency');
    if (peakEfficiency < 0.8) {
      recommendations.push({
        icon: 'fa-clock',
        message: 'Consider optimizing slot allocation during peak hours to improve efficiency'
      });
    }
    
    const offPeakUtil = this.getKPI('off_peak_utilization');
    if (offPeakUtil < 0.4) {
      recommendations.push({
        icon: 'fa-percentage',
        message: 'Implement dynamic pricing to increase off-peak hour utilization'
      });
    }
    
    const satisfaction = this.getKPI('customer_satisfaction');
    if (satisfaction < 4.0) {
      recommendations.push({
        icon: 'fa-heart',
        message: 'Focus on user experience improvements to boost customer satisfaction'
      });
    }
    
    return recommendations;
  }
}
