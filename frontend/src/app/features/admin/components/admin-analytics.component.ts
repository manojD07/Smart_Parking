import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';

// Analytics Components
import { SimpleRevenueAnalyticsComponent } from './analytics/simple-revenue-analytics.component';

// Services
import { AnalyticsService, AnalyticsOverview } from '../services/analytics.service';

@Component({
  selector: 'app-admin-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, SimpleRevenueAnalyticsComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12 d-flex justify-content-between align-items-center">
          <div>
            <h2>
              <i class="fas fa-chart-bar me-2"></i>
              Analytics Dashboard
            </h2>
            <p class="text-muted">Comprehensive business analytics and insights</p>
          </div>
          <div class="d-flex gap-2">
            <button 
              class="btn btn-outline-primary" 
              (click)="refreshAnalytics()"
              [disabled]="loading">
              <i class="fas fa-sync-alt me-1" [class.fa-spin]="loading"></i>
              Refresh
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading analytics data...</p>
      </div>

      <!-- REMOVED: These 4 cards were using different API and causing inconsistency -->
      <!-- All data now comes from the revenue analytics component below -->

      <!-- Tab Navigation -->
      <div class="row mb-4">
        <div class="col-12">
          <ul class="nav nav-tabs" id="analyticsTab" role="tablist">
            <li class="nav-item" role="presentation">
              <button 
                class="nav-link active" 
                id="revenue-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#revenue" 
                type="button" 
                role="tab">
                <i class="fas fa-dollar-sign me-2"></i>
                Revenue Analytics
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button 
                class="nav-link" 
                id="bookings-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#bookings" 
                type="button" 
                role="tab">
                <i class="fas fa-ticket-alt me-2"></i>
                Booking Analytics
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button 
                class="nav-link" 
                id="occupancy-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#occupancy" 
                type="button" 
                role="tab">
                <i class="fas fa-chart-area me-2"></i>
                Occupancy & Utilization
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button 
                class="nav-link" 
                id="performance-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#performance" 
                type="button" 
                role="tab">
                <i class="fas fa-tachometer-alt me-2"></i>
                Performance Metrics
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="tab-content" id="analyticsTabContent">
        <!-- Revenue Analytics Tab -->
        <div class="tab-pane fade show active" id="revenue" role="tabpanel">
          <app-simple-revenue-analytics></app-simple-revenue-analytics>
        </div>

        <!-- Booking Analytics Tab -->
        <div class="tab-pane fade" id="bookings" role="tabpanel">
          <div class="text-center py-5">
            <i class="fas fa-ticket-alt fa-3x text-muted mb-3"></i>
            <h5>Booking Analytics</h5>
            <p class="text-muted">Component temporarily disabled - will be restored in next phase</p>
          </div>
        </div>

        <!-- Occupancy & Utilization Tab -->
        <div class="tab-pane fade" id="occupancy" role="tabpanel">
          <div class="text-center py-5">
            <i class="fas fa-chart-area fa-3x text-muted mb-3"></i>
            <h5>Occupancy & Utilization</h5>
            <p class="text-muted">Component temporarily disabled - will be restored in next phase</p>
          </div>
        </div>

        <!-- Performance Metrics Tab -->
        <div class="tab-pane fade" id="performance" role="tabpanel">
          <div class="text-center py-5">
            <i class="fas fa-tachometer-alt fa-3x text-muted mb-3"></i>
            <h5>Performance Metrics</h5>
            <p class="text-muted">Component temporarily disabled - will be restored in next phase</p>
          </div>
        </div>

        <!-- Overview Tab -->
        <div class="tab-pane fade" id="overview" role="tabpanel">
          <div class="text-center py-5">
            <i class="fas fa-tachometer-alt fa-3x text-muted mb-3"></i>
            <h5>System Overview</h5>
            <p class="text-muted">Coming in Phase 3</p>
          </div>
        </div>

        <!-- Parking Analytics Tab -->
        <div class="tab-pane fade" id="parking" role="tabpanel">
          <div class="text-center py-5">
            <i class="fas fa-parking fa-3x text-muted mb-3"></i>
            <h5>Parking Analytics</h5>
            <p class="text-muted">Coming in future version</p>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .nav-tabs {
      border-bottom: 2px solid #e9ecef;
    }

    .nav-tabs .nav-link {
      border: none;
      border-bottom: 3px solid transparent;
      color: #6c757d;
      font-weight: 500;
      padding: 1rem 1.5rem;
    }

    .nav-tabs .nav-link:hover {
      border-bottom-color: #dee2e6;
      color: #495057;
    }

    .nav-tabs .nav-link.active {
      color: #007bff;
      border-bottom-color: #007bff;
      background-color: transparent;
    }

    .tab-content {
      padding-top: 1rem;
    }

    .card {
      border-radius: 12px;
      border: 1px solid #e9ecef;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    @media (max-width: 768px) {
      .nav-tabs .nav-link {
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
      }
    }
  `]
})
export class AdminAnalyticsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Component state
  loading = true;
  selectedPeriod: 'weekly' | 'monthly' | 'quarterly' | 'yearly' = 'monthly';
  
  // Analytics data
  analyticsOverview: AnalyticsOverview | null = null;
  errorMessage = '';

  constructor(private analyticsService: AnalyticsService) {}

  ngOnInit(): void {
    this.loadAnalyticsData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Load analytics data based on selected period
   */
  loadAnalyticsData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.analyticsService.getDateRange(this.selectedPeriod);
    
    this.analyticsService.getAnalyticsOverview(dateRange.start, dateRange.end)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (overview) => {
          this.analyticsOverview = overview;
          this.loading = false;
        },
        error: (error) => {
          console.error('Failed to load analytics data:', error);
          this.errorMessage = 'Failed to load analytics data. Please try again.';
          this.loading = false;
        }
      });
  }

  /**
   * Handle period change
   */
  onPeriodChange(): void {
    this.loadAnalyticsData();
  }

  /**
   * Refresh analytics data
   */
  refreshAnalytics(): void {
    this.loadAnalyticsData();
  }

  /**
   * Get date range for child components
   */
  getDateRangeForComponents(): { start: string; end: string } {
    const dateRange = this.analyticsService.getDateRange(this.selectedPeriod);
    return {
      start: dateRange.start,
      end: dateRange.end
    };
  }

  /**
   * Convert period to days for child component
   */
  getPeriodInDays(): string {
    switch (this.selectedPeriod) {
      case 'weekly': return '7';
      case 'monthly': return '30';
      case 'quarterly': return '90';
      case 'yearly': return '365';
      default: return '30';
    }
  }
}