import { Component } from '@angular/core';

@Component({
  selector: 'app-admin-checkin',
  standalone: true,
  template: `
    <div class="container-fluid py-4">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="card border-0 shadow-sm">
            <div class="card-body text-center py-5">
              <!-- Coming Soon Icon -->
              <div class="mb-4">
                <i class="fas fa-tools text-primary" style="font-size: 4rem; opacity: 0.7;"></i>
              </div>
              
              <!-- Title -->
              <h2 class="text-primary mb-3">
                <i class="fas fa-calendar-check me-2"></i>
                Check-In Management
              </h2>
              
              <!-- Coming Soon Message -->
              <div class="alert alert-info border-0 shadow-sm mb-4">
                <h4 class="alert-heading mb-3">
                  <i class="fas fa-rocket me-2"></i>
                  Coming in Next Version!
                </h4>
                <p class="mb-2">
                  The Check-In Management feature is currently under development and will be available in the next version of the Smart Parking System.
                </p>
                <hr class="my-3">
                <p class="mb-0">
                  <strong>Planned Features:</strong>
                </p>
              </div>
              
              <!-- Feature Preview -->
              <div class="row g-4 mt-2">
                <div class="col-md-6">
                  <div class="card h-100 border-primary border-opacity-25">
                    <div class="card-body">
                      <div class="text-primary mb-3">
                        <i class="fas fa-qrcode" style="font-size: 2rem;"></i>
                      </div>
                      <h5 class="card-title">QR Code Check-In</h5>
                      <p class="card-text text-muted">
                        Scan QR codes for quick vehicle check-in and check-out processes.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="card h-100 border-success border-opacity-25">
                    <div class="card-body">
                      <div class="text-success mb-3">
                        <i class="fas fa-car-side" style="font-size: 2rem;"></i>
                      </div>
                      <h5 class="card-title">Manual Check-In</h5>
                      <p class="card-text text-muted">
                        Manual check-in/out for vehicles with booking verification.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="card h-100 border-warning border-opacity-25">
                    <div class="card-body">
                      <div class="text-warning mb-3">
                        <i class="fas fa-clock" style="font-size: 2rem;"></i>
                      </div>
                      <h5 class="card-title">Real-time Tracking</h5>
                      <p class="card-text text-muted">
                        Track vehicle entry/exit times and parking duration in real-time.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="card h-100 border-info border-opacity-25">
                    <div class="card-body">
                      <div class="text-info mb-3">
                        <i class="fas fa-chart-line" style="font-size: 2rem;"></i>
                      </div>
                      <h5 class="card-title">Check-In Analytics</h5>
                      <p class="card-text text-muted">
                        Detailed analytics on check-in patterns and parking utilization.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Version Info -->
              <div class="mt-5 pt-4 border-top">
                <p class="text-muted mb-0">
                  <i class="fas fa-info-circle me-1"></i>
                  This feature will be available in <strong>Version 2.0</strong> of the Smart Parking Management System.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .card {
      transition: all 0.3s ease;
    }
    
    .card:hover {
      transform: translateY(-2px);
    }
    
    .alert {
      background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
    }
    
    .fas {
      transition: all 0.3s ease;
    }
    
    .card:hover .fas {
      transform: scale(1.1);
    }
    
    .border-primary {
      border-color: var(--bs-primary) !important;
    }
    
    .border-success {
      border-color: var(--bs-success) !important;
    }
    
    .border-warning {
      border-color: var(--bs-warning) !important;
    }
    
    .border-info {
      border-color: var(--bs-info) !important;
    }
  `]
})
export class AdminCheckinComponent {
}