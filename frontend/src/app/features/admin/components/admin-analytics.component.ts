import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

// Components
import { RevenueAnalyticsComponent } from './analytics/revenue-analytics.component';
import { BookingAnalyticsComponent } from './analytics/booking-analytics.component';

@Component({
  selector: 'app-admin-analytics',
  standalone: true,
  imports: [CommonModule, RevenueAnalyticsComponent, BookingAnalyticsComponent],
  template: `
    <div class="container-fluid mt-4">
      <!-- Header -->
      <div class="row mb-4">
        <div class="col-12">
          <h2>
            <i class="fas fa-chart-bar me-2"></i>
            Analytics Dashboard
          </h2>
          <p class="text-muted">Comprehensive business analytics and insights</p>
        </div>
      </div>

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
                id="overview-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#overview" 
                type="button" 
                role="tab">
                <i class="fas fa-tachometer-alt me-2"></i>
                Overview
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button 
                class="nav-link" 
                id="parking-tab" 
                data-bs-toggle="tab" 
                data-bs-target="#parking" 
                type="button" 
                role="tab">
                <i class="fas fa-parking me-2"></i>
                Parking Analytics
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- Tab Content -->
      <div class="tab-content" id="analyticsTabContent">
        <!-- Revenue Analytics Tab -->
        <div class="tab-pane fade show active" id="revenue" role="tabpanel">
          <app-revenue-analytics></app-revenue-analytics>
        </div>

        <!-- Booking Analytics Tab -->
        <div class="tab-pane fade" id="bookings" role="tabpanel">
          <app-booking-analytics></app-booking-analytics>
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
export class AdminAnalyticsComponent implements OnInit {

  constructor() {}

  ngOnInit(): void {
    // Component initialization
  }
}