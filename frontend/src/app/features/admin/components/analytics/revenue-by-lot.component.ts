import { Component, OnInit, OnDestroy, ViewChild, ElementRef, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { Chart, ChartConfiguration, ChartType, registerables } from 'chart.js';
import { AnalyticsService } from '../../services/analytics.service';
import { ParkingService } from '../../../parking/services/parking.service';

Chart.register(...registerables);

export interface LotRevenueData {
  lot_id: string;
  lot_name: string;
  total_revenue: number;
  bookings_count: number;
  utilization_rate: number;
  average_booking_value: number;
}

@Component({
  selector: 'app-revenue-by-lot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="card">
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <h5 class="card-title mb-0">
            <i class="fas fa-building me-2"></i>
            Revenue by Parking Lot
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
            <select 
              class="form-select form-select-sm" 
              [(ngModel)]="chartType" 
              (change)="onChartTypeChange()"
              style="width: auto;">
              <option value="bar">Bar Chart</option>
              <option value="pie">Pie Chart</option>
              <option value="doughnut">Doughnut</option>
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
          <p class="mt-2 mb-0 text-muted">Loading lot revenue data...</p>
        </div>
        
        <div *ngIf="!loading && errorMessage" class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          {{ errorMessage }}
        </div>
        
        <div *ngIf="!loading && !errorMessage" class="row">
          <div class="col-md-8">
            <div class="chart-container">
              <canvas #lotRevenueChart></canvas>
            </div>
          </div>
          <div class="col-md-4">
            <div class="lot-stats">
              <h6 class="text-muted mb-3">Top Performing Lots</h6>
              <div *ngFor="let lot of getTopLots(); let i = index" class="lot-stat-item mb-3">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <div class="fw-semibold">{{ lot.lot_name }}</div>
                    <small class="text-muted">{{ lot.bookings_count }} bookings</small>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold text-success">\${{ lot.total_revenue | number:'1.2-2' }}</div>
                    <small class="text-muted">{{ lot.utilization_rate | percent:'1.0-0' }} util.</small>
                  </div>
                </div>
                <div class="progress mt-2" style="height: 4px;">
                  <div class="progress-bar" 
                       [style.width.%]="(lot.total_revenue / getMaxRevenue()) * 100"
                       [style.background-color]="getColorForIndex(i)">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Summary Stats -->
        <div *ngIf="!loading && lotRevenueData.length > 0" class="row mt-4 pt-3 border-top">
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Total Lots</h6>
              <h4 class="text-primary mb-0">{{ lotRevenueData.length }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Total Revenue</h6>
              <h4 class="text-success mb-0">\${{ getTotalRevenue() | number:'1.2-2' }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Avg per Lot</h6>
              <h4 class="text-info mb-0">\${{ getAverageRevenue() | number:'1.2-2' }}</h4>
            </div>
          </div>
          <div class="col-md-3">
            <div class="text-center">
              <h6 class="text-muted mb-1">Best Performer</h6>
              <h4 class="text-warning mb-0">{{ getBestLot()?.lot_name || 'N/A' }}</h4>
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
    
    .lot-stats {
      max-height: 400px;
      overflow-y: auto;
    }
    
    .lot-stat-item {
      padding: 12px;
      background-color: #f8f9fa;
      border-radius: 8px;
      border-left: 4px solid transparent;
    }
    
    .lot-stat-item:nth-child(1) { border-left-color: #007bff; }
    .lot-stat-item:nth-child(2) { border-left-color: #28a745; }
    .lot-stat-item:nth-child(3) { border-left-color: #ffc107; }
    .lot-stat-item:nth-child(4) { border-left-color: #dc3545; }
    .lot-stat-item:nth-child(5) { border-left-color: #6f42c1; }
    
    @media (max-width: 768px) {
      .chart-container {
        height: 300px;
      }
      
      .col-md-8, .col-md-4 {
        margin-bottom: 1rem;
      }
    }
  `]
})
export class RevenueByLotComponent implements OnInit, OnDestroy {
  @ViewChild('lotRevenueChart', { static: true }) chartRef!: ElementRef<HTMLCanvasElement>;
  @Input() dateRange?: { start: string; end: string };
  
  private destroy$ = new Subject<void>();
  private chart?: Chart;
  
  loading = true;
  errorMessage = '';
  selectedPeriod = '30';
  chartType: 'bar' | 'pie' | 'doughnut' = 'bar';
  lotRevenueData: LotRevenueData[] = [];
  
  private colorPalette = [
    '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1',
    '#fd7e14', '#20c997', '#e83e8c', '#6c757d', '#343a40'
  ];
  
  constructor(
    private analyticsService: AnalyticsService,
    private parkingService: ParkingService
  ) {}
  
  ngOnInit(): void {
    this.loadLotRevenueData();
  }
  
  ngOnDestroy(): void {
    if (this.chart) {
      this.chart.destroy();
    }
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  loadLotRevenueData(): void {
    this.loading = true;
    this.errorMessage = '';
    
    const dateRange = this.dateRange || this.getDateRange();
    
    // First get all parking lots
    this.parkingService.getParkingLots({ skip: 0, limit: 50 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: async (lots: any[]) => {
          try {
            // Get analytics for each lot
            const lotAnalytics = await Promise.all(
              lots.map(async (lot: any) => {
                try {
                  const analytics = await this.analyticsService.getLotAnalytics(
                    lot.id,
                    dateRange.start,
                    dateRange.end
                  ).toPromise();
                  
                  return {
                    lot_id: lot.id,
                    lot_name: lot.name,
                    total_revenue: analytics?.revenue?.total_revenue || 0,
                    bookings_count: analytics?.revenue?.total_bookings || 0,
                    utilization_rate: analytics?.utilization?.overall_utilization_rate || 0,
                    average_booking_value: analytics?.revenue?.average_booking_value || 0
                  } as LotRevenueData;
                } catch (error) {
                  console.warn(`Failed to get analytics for lot ${lot.name}:`, error);
                  return {
                    lot_id: lot.id,
                    lot_name: lot.name,
                    total_revenue: 0,
                    bookings_count: 0,
                    utilization_rate: 0,
                    average_booking_value: 0
                  } as LotRevenueData;
                }
              })
            );
            
            this.lotRevenueData = lotAnalytics
              .filter(lot => lot.total_revenue > 0)
              .sort((a, b) => b.total_revenue - a.total_revenue);
            
            this.createChart();
            this.loading = false;
          } catch (error) {
            console.error('Failed to process lot analytics:', error);
            this.errorMessage = 'Failed to load lot revenue data. Please try again.';
            this.loading = false;
          }
        },
        error: (error: any) => {
          console.error('Failed to load parking lots:', error);
          this.errorMessage = 'Failed to load parking lots. Please try again.';
          this.loading = false;
        }
      });
  }
  
  onPeriodChange(): void {
    this.loadLotRevenueData();
  }
  
  onChartTypeChange(): void {
    this.createChart();
  }
  
  refreshData(): void {
    this.loadLotRevenueData();
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
    if (!this.lotRevenueData || this.lotRevenueData.length === 0 || !this.chartRef) return;
    
    if (this.chart) {
      this.chart.destroy();
    }
    
    const ctx = this.chartRef.nativeElement.getContext('2d');
    if (!ctx) return;
    
    const labels = this.lotRevenueData.map(lot => lot.lot_name);
    const data = this.lotRevenueData.map(lot => lot.total_revenue);
    const colors = this.lotRevenueData.map((_, index) => this.colorPalette[index % this.colorPalette.length]);
    
    const config: ChartConfiguration = {
      type: this.chartType as ChartType,
      data: {
        labels,
        datasets: [{
          label: 'Revenue ($)',
          data,
          backgroundColor: this.chartType === 'bar' ? colors.map(c => c + '80') : colors,
          borderColor: colors,
          borderWidth: this.chartType === 'bar' ? 1 : 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: this.chartType !== 'bar',
            position: 'bottom'
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: '#007bff',
            borderWidth: 1,
            callbacks: {
              label: (context) => {
                const lot = this.lotRevenueData[context.dataIndex];
                return [
                  `Revenue: $${context.parsed.y?.toFixed(2) || context.parsed?.toFixed(2)}`,
                  `Bookings: ${lot.bookings_count}`,
                  `Utilization: ${(lot.utilization_rate * 100).toFixed(1)}%`
                ];
              }
            }
          }
        },
        scales: this.chartType === 'bar' ? {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Parking Lots',
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
        } : undefined
      }
    };
    
    this.chart = new Chart(ctx, config);
  }
  
  getTopLots(): LotRevenueData[] {
    return this.lotRevenueData.slice(0, 5);
  }
  
  getTotalRevenue(): number {
    return this.lotRevenueData.reduce((sum, lot) => sum + lot.total_revenue, 0);
  }
  
  getAverageRevenue(): number {
    if (this.lotRevenueData.length === 0) return 0;
    return this.getTotalRevenue() / this.lotRevenueData.length;
  }
  
  getBestLot(): LotRevenueData | null {
    if (this.lotRevenueData.length === 0) return null;
    return this.lotRevenueData[0];
  }
  
  getMaxRevenue(): number {
    if (this.lotRevenueData.length === 0) return 1;
    return Math.max(...this.lotRevenueData.map(lot => lot.total_revenue));
  }
  
  getColorForIndex(index: number): string {
    return this.colorPalette[index % this.colorPalette.length];
  }
}
