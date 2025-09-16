import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil, interval, startWith } from 'rxjs';
import { AdminService, AdminStats } from '../services/admin.service';
import { LoadingComponent } from '../../../shared/components/loading.component';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h1 class="h2 mb-1">
                <i class="fas fa-tachometer-alt me-2"></i>
                Admin Dashboard
              </h1>
              <p class="text-muted">System overview and management</p>
            </div>
            <div>
              <button class="btn btn-primary me-2" (click)="refreshData()">
                <i class="fas fa-sync-alt me-2" [class.fa-spin]="loading"></i>
                Refresh
              </button>
              <button class="btn btn-outline-secondary" routerLink="/admin/reports">
                <i class="fas fa-chart-line me-2"></i>
                View Reports
              </button>
            </div>
          </div>
        </div>
      </div>

      <app-loading *ngIf="loading && !stats" message="Loading dashboard..."></app-loading>

      <div *ngIf="!loading || stats">
        <!-- Quick Stats Cards -->
        <div class="row mb-4" *ngIf="stats">
          <div class="col-xl-3 col-md-6 mb-4">
            <div class="card border-primary">
              <div class="card-body">
                <div class="row no-gutters align-items-center">
                  <div class="col mr-2">
                    <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                      Total Users
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      {{ stats.totalUsers | number }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-users fa-2x text-primary"></i>
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
                      {{ stats.totalBookings | number }}
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
                      Total Revenue
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      \${{ stats.totalRevenue | number:'1.2-2' }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-dollar-sign fa-2x text-info"></i>
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
                      Active Lots
                    </div>
                    <div class="h5 mb-0 font-weight-bold text-gray-800">
                      {{ stats.activeLots | number }}
                    </div>
                  </div>
                  <div class="col-auto">
                    <i class="fas fa-parking fa-2x text-warning"></i>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Today's Stats -->
        <div class="row mb-4" *ngIf="stats">
          <div class="col-lg-6">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-calendar-day me-2"></i>
                  Today's Performance
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-6">
                    <div class="text-center">
                      <h3 class="text-primary">{{ stats.todayBookings }}</h3>
                      <p class="text-muted mb-0">Bookings Today</p>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="text-center">
                      <h3 class="text-success">\${{ stats.todayRevenue | number:'1.2-2' }}</h3>
                      <p class="text-muted mb-0">Revenue Today</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-6">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-chart-pie me-2"></i>
                  System Utilization
                </h5>
              </div>
              <div class="card-body">
                <div class="text-center">
                  <div class="progress mb-3" style="height: 20px;">
                    <div
                      class="progress-bar"
                      [class.bg-success]="stats.occupancyRate < 70"
                      [class.bg-warning]="stats.occupancyRate >= 70 && stats.occupancyRate < 90"
                      [class.bg-danger]="stats.occupancyRate >= 90"
                      [style.width.%]="stats.occupancyRate"
                    >
                      {{ stats.occupancyRate.toFixed(1) }}%
                    </div>
                  </div>
                  <h4>{{ stats.occupancyRate.toFixed(1) }}% Occupied</h4>
                  <p class="text-muted mb-0">Average occupancy across all lots</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-bolt me-2"></i>
                  Quick Actions
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-lg-3 col-md-6 mb-3">
                    <button class="btn btn-outline-primary w-100 h-100" routerLink="/admin/users">
                      <i class="fas fa-users fa-2x d-block mb-2"></i>
                      Manage Users
                    </button>
                  </div>
                  <div class="col-lg-3 col-md-6 mb-3">
                    <button class="btn btn-outline-success w-100 h-100" routerLink="/admin/parking">
                      <i class="fas fa-parking fa-2x d-block mb-2"></i>
                      Manage Parking
                    </button>
                  </div>
                  <div class="col-lg-3 col-md-6 mb-3">
                    <button class="btn btn-outline-info w-100 h-100" routerLink="/admin/bookings">
                      <i class="fas fa-ticket-alt fa-2x d-block mb-2"></i>
                      Manage Bookings
                    </button>
                  </div>
                  <div class="col-lg-3 col-md-6 mb-3">
                    <button class="btn btn-outline-warning w-100 h-100" routerLink="/admin/analytics">
                      <i class="fas fa-chart-line fa-2x d-block mb-2"></i>
                      View Analytics
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="row" *ngIf="stats && stats.recentActivity">
          <div class="col-12">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <i class="fas fa-history me-2"></i>
                  Recent Activity
                </h5>
                <a routerLink="/admin/logs" class="btn btn-sm btn-outline-secondary">
                  View All Logs
                </a>
              </div>
              <div class="card-body">
                <div class="list-group list-group-flush">
                  <div 
                    class="list-group-item list-group-item-action" 
                    *ngFor="let activity of stats.recentActivity.slice(0, 10)"
                  >
                    <div class="d-flex w-100 justify-content-between">
                      <h6 class="mb-1">{{ activity.title }}</h6>
                      <small>{{ activity.timestamp | date:'short' }}</small>
                    </div>
                    <p class="mb-1">{{ activity.description }}</p>
                    <small class="text-muted">{{ activity.user || 'System' }}</small>
                  </div>
                </div>
                
                <div class="text-center py-4" *ngIf="stats.recentActivity.length === 0">
                  <i class="fas fa-inbox fa-2x text-muted mb-2"></i>
                  <p class="text-muted">No recent activity</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div class="row" *ngIf="!loading && !stats">
        <div class="col-12">
          <div class="card">
            <div class="card-body text-center py-5">
              <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
              <h4>Unable to Load Dashboard</h4>
              <p class="text-muted mb-4">
                {{ errorMessage || 'There was an error loading the admin dashboard.' }}
              </p>
              <button class="btn btn-primary" (click)="refreshData()">
                <i class="fas fa-retry me-2"></i>
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .card {
      box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
      border: 1px solid #e3e6f0;
    }

    .text-xs {
      font-size: 0.7rem;
    }

    .font-weight-bold {
      font-weight: 700;
    }

    .text-gray-800 {
      color: #5a5c69;
    }

    .btn.h-100 {
      min-height: 100px;
    }

    .progress {
      background-color: #e9ecef;
    }
  `]
})
export class AdminDashboardComponent implements OnInit, OnDestroy {
  stats: AdminStats | null = null;
  loading = true;
  errorMessage = '';
  
  private destroy$ = new Subject<void>();

  constructor(private adminService: AdminService) {}

  ngOnInit(): void {
    this.loadDashboardData();
    
    // Auto-refresh every 5 minutes
    interval(5 * 60 * 1000)
      .pipe(
        startWith(0),
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        if (!this.loading) {
          this.refreshData();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadDashboardData(): void {
    this.adminService.getAdminStats()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (stats) => {
          this.stats = stats;
          this.loading = false;
          this.errorMessage = '';
        },
        error: (error) => {
          console.error('Error loading admin stats:', error);
          this.errorMessage = error.message || 'Failed to load dashboard data';
          this.loading = false;
          
          // Provide fallback demo data if backend is not available
          this.stats = this.getDemoStats();
        }
      });
  }

  refreshData(): void {
    this.loading = true;
    this.loadDashboardData();
  }

  private getDemoStats(): AdminStats {
    return {
      totalUsers: 125,
      totalBookings: 1847,
      totalRevenue: 15420.50,
      activeLots: 8,
      todayBookings: 23,
      todayRevenue: 180.75,
      occupancyRate: 68.5,
      recentActivity: [
        {
          title: 'New user registered',
          description: 'john.doe@example.com joined the platform',
          timestamp: new Date().toISOString(),
          user: 'System'
        },
        {
          title: 'Booking cancelled',
          description: 'Booking #1234 was cancelled by user',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          user: 'jane.smith@example.com'
        }
      ]
    };
  }
}
