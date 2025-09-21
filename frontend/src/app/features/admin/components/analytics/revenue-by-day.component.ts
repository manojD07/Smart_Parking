import { Component, OnInit, OnDestroy, ViewChild, ElementRef, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { Chart, ChartConfiguration, ChartType, registerables } from 'chart.js';
import { AnalyticsService, RevenueAnalytics } from '../../services/analytics.service';

Chart.register(...registerables);

@Component({
  selector: 'app-revenue-by-day',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="card">
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title mb-0">
            <i class="fas fa-chart-line me-2"></i>
            Revenue by Day
          </h5>
          <div class="d-flex gap-2">
            <select 
              class="form-select form-select-sm" 
              [(ngModel)]="selectedPeriod" 
              (change)="onPeriodChange()"
              style="width: auto;">
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
            <button 
              class="btn btn-sm btn-outline-primary" 
              (click)="refreshData()"
              [disabled]="loading">
              <i class="fas fa-sync-alt" [class.fa-spin]="loading"></i>
            </button>
          </div>
        </div>
      </div>
      <div class="card-body">
        <div *ngIf="loading" class="text-center py-4">
          <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 mb-0 text-muted">Loading revenue data...</p>
        </div>
        
        <div *ngIf="!loading && errorMessage" class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          {{ errorMessage }}
        </div>
        
        <div *ngIf="!loading && !errorMessage" class="chart-container">
          <canvas #revenueChart></canvas>
        </div>
        
        <!-- Summary Stats -->
        <div *ngIf="!loading && revenueData" class="row mt-3">
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Total Revenue</h6>
              <h4 class="text-success mb-0">\${{ revenueData.total_revenue | number:'1.2-2' }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Daily Average</h6>
              <h4 class="text-info mb-0">\${{ revenueData.average_daily_revenue | number:'1.2-2' }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Best Day</h6>
              <h4 class="text-primary mb-0">\${{ getBestDay() | number:'1.2-2' }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Growth Trend</h6>
              <h4 class="mb-0" [ngClass]="getGrowthTrendClass()">
                <i [class]="getGrowthTrendIcon()"></i>
                {{ getGrowthTrend() }}%
              </h4>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chart-container {
      position: relative;
      height: 400px;
      width: 100%;
    }
    
    .card {
      border-radius: 12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .card-header {
      background-color: #f8f9fa;
      border-bottom: 1px solid #e9ecef;
    }
    
    @media (max-width: 768px) {
      .chart-container {
        height: 300px;
      }
    }
  `]
})
export class RevenueByDayComponent implements OnInit, OnDestroy {
  @ViewChild('revenueChart', { static: true }) chartRef!: ElementRef<HTMLCanvasElement>;
  @Input() dateRange?: { start: string; end: string };
  
  private destroy$ = new Subject<void>();
  private chart?: Chart;
  
  loading = true;
  errorMessage = '';
  selectedPeriod = '30';
  revenueData: RevenueAnalytics | null = null;
  
  constructor(private analyticsService: AnalyticsService) {}
  
  ngOnInit(): void {
    this.loadRevenueData();
  }
  
  ngOnDestroy(): void {
    if (this.chart) {
      this.chart.destroy();
    }
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  loadRevenueData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.dateRange || this.getDateRange();
    
    this.analyticsService.getRevenueAnalytics(
      dateRange.start, 
      dateRange.end, 
      'daily'
    ).pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (data) => {
        this.revenueData = data;
        this.createChart();
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load revenue data:', error);
        this.errorMessage = 'Failed to load revenue data. Please try again.';
        this.loading = false;
      }
    });
  }
  
  onPeriodChange(): void {
    this.loadRevenueData();
  }
  
  refreshData(): void {
    this.loadRevenueData();
  }
  
  private getDateRange(): { start: string; end: string } {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - parseInt(this.selectedPeriod));
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0]
    };
  }
  
  private createChart(): void {
    if (!this.revenueData || !this.chartRef) return;
    
    if (this.chart) {
      this.chart.destroy();
    }
    
    const ctx = this.chartRef.nativeElement.getContext('2d');
    if (!ctx) return;
    
    // Extract data from revenue trends or period breakdown
    const chartData = this.extractChartData();
    
    const config: ChartConfiguration = {
      type: 'line' as ChartType,
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Daily Revenue ($)',
          data: chartData.data,
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#007bff',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: '#007bff',
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                return `Revenue: $${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Date',
              color: '#6c757d'
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Revenue ($)',
              color: '#6c757d'
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              callback: function(value) {
                return '$' + Number(value).toFixed(0);
              }
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index'
        }
      }
    };
    
    this.chart = new Chart(ctx, config);
  }
  
  private extractChartData(): { labels: string[]; data: number[] } {
    if (!this.revenueData) {
      return { labels: [], data: [] };
    }
    
    // Try to extract from revenue_trends or period_breakdown
    let chartData = this.revenueData.revenue_trends || this.revenueData.period_breakdown || [];
    
    // If no structured data, return empty arrays
    if (!chartData || chartData.length === 0) {
      return { labels: [], data: [] };
    }
    
    // Extract from structured data
    const labels = chartData.map((item: any) => {
      if (item.date) {
        return new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }
      return item.period || item.label || 'N/A';
    });
    
    const data = chartData.map((item: any) => 
      parseFloat(item.revenue || item.total_revenue || item.amount || 0)
    );
    
    return { labels, data };
  }
  
  getBestDay(): number {
    if (!this.revenueData) return 0;
    
    const chartData = this.extractChartData();
    return Math.max(...chartData.data);
  }
  
  getGrowthTrend(): number {
    if (!this.revenueData) return 0;
    
    const chartData = this.extractChartData();
    if (chartData.data.length < 2) return 0;
    
    const firstWeek = chartData.data.slice(0, 7).reduce((a, b) => a + b, 0);
    const lastWeek = chartData.data.slice(-7).reduce((a, b) => a + b, 0);
    
    if (firstWeek === 0) return 0;
    
    return Math.round(((lastWeek - firstWeek) / firstWeek) * 100);
  }
  
  getGrowthTrendClass(): string {
    const trend = this.getGrowthTrend();
    if (trend > 0) return 'text-success';
    if (trend < 0) return 'text-danger';
    return 'text-muted';
  }
  
  getGrowthTrendIcon(): string {
    const trend = this.getGrowthTrend();
    if (trend > 0) return 'fas fa-arrow-up me-1';
    if (trend < 0) return 'fas fa-arrow-down me-1';
    return 'fas fa-minus me-1';
  }
}
