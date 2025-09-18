import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { ParkingService } from '../services/parking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { ParkingLot, ParkingSlot, AvailabilityResponse } from '../../../core/models/parking.model';
import { 
  nowIST,
  toDatetimeLocalIST
} from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-parking-details',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  template: `
    <div class="container mt-4">
      <app-loading *ngIf="loading" message="Loading parking lot details..."></app-loading>

      <div *ngIf="!loading && parkingLot">
        <!-- Header -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h1 class="h2 mb-1">{{ parkingLot.name }}</h1>
                <p class="text-muted mb-0">
                  <i class="fas fa-map-marker-alt me-1"></i>
                  {{ parkingLot.address }}
                </p>
              </div>
              <div>
                <span class="badge fs-6" [class]="parkingLot.is_active ? 'bg-success' : 'bg-danger'">
                  {{ parkingLot.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="row mb-4">
          <div class="col-12">
            <div class="d-flex gap-2 flex-wrap">
              <button 
                class="btn btn-primary"
                [disabled]="!parkingLot.is_active"
                (click)="bookNow()"
              >
                <i class="fas fa-ticket-alt me-2"></i>
                Book Now
              </button>
              <button class="btn btn-outline-secondary" (click)="getDirections()">
                <i class="fas fa-directions me-2"></i>
                Get Directions
              </button>
              <button class="btn btn-outline-info" (click)="shareLocation()">
                <i class="fas fa-share me-2"></i>
                Share Location
              </button>
            </div>
          </div>
        </div>

        <div class="row">
          <!-- Main Information -->
          <div class="col-lg-8">
            <!-- Overview Card -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-info-circle me-2"></i>
                  Overview
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <div class="d-flex align-items-center">
                      <div class="icon-circle bg-primary text-white me-3">
                        <i class="fas fa-car"></i>
                      </div>
                      <div>
                        <h6 class="mb-0">{{ parkingLot.total_car_slots }}</h6>
                        <small class="text-muted">Car Spaces</small>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="d-flex align-items-center">
                      <div class="icon-circle bg-success text-white me-3">
                        <i class="fas fa-motorcycle"></i>
                      </div>
                      <div>
                        <h6 class="mb-0">{{ parkingLot.total_bike_slots }}</h6>
                        <small class="text-muted">Bike Spaces</small>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="d-flex align-items-center">
                      <div class="icon-circle bg-warning text-white me-3">
                        <i class="fas fa-dollar-sign"></i>
                      </div>
                      <div>
                        <h6 class="mb-0">\${{ parkingLot.hourly_rate_car }}/hr</h6>
                        <small class="text-muted">Car Rate</small>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6 mb-3">
                    <div class="d-flex align-items-center">
                      <div class="icon-circle bg-info text-white me-3">
                        <i class="fas fa-coins"></i>
                      </div>
                      <div>
                        <h6 class="mb-0">\${{ parkingLot.hourly_rate_bike }}/hr</h6>
                        <small class="text-muted">Bike Rate</small>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Distance (if available) -->
                <div class="row" *ngIf="distance !== null">
                  <div class="col-12">
                    <div class="alert alert-info">
                      <i class="fas fa-route me-2"></i>
                      <strong>{{ distance.toFixed(1) }} km</strong> from your current location
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Real-time Availability -->
            <div class="card mb-4">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <i class="fas fa-chart-bar me-2"></i>
                  Current Availability
                </h5>
                <button class="btn btn-sm btn-outline-primary" (click)="refreshAvailability()">
                  <i class="fas fa-sync-alt me-1" [class.fa-spin]="loadingAvailability"></i>
                  Refresh
                </button>
              </div>
              <div class="card-body">
                <div *ngIf="loadingAvailability" class="text-center py-3">
                  <div class="spinner-border text-primary"></div>
                  <p class="mt-2 mb-0">Checking availability...</p>
                </div>

                <div *ngIf="!loadingAvailability">
                  <!-- Car Availability -->
                  <div class="mb-4" *ngIf="carAvailability">
                    <h6>Car Parking</h6>
                    <div class="progress mb-2" style="height: 20px;">
                      <div
                        class="progress-bar"
                        [class.bg-success]="carAvailability.occupancy_rate < 70"
                        [class.bg-warning]="carAvailability.occupancy_rate >= 70 && carAvailability.occupancy_rate < 90"
                        [class.bg-danger]="carAvailability.occupancy_rate >= 90"
                        [style.width.%]="carAvailability.occupancy_rate"
                      >
                        {{ carAvailability.occupancy_rate.toFixed(0) }}% Occupied
                      </div>
                    </div>
                    <div class="d-flex justify-content-between">
                      <span>Available: <strong>{{ carAvailability.available_slots }}</strong></span>
                      <span>Total: <strong>{{ carAvailability.total_slots }}</strong></span>
                    </div>
                  </div>

                  <!-- Bike Availability -->
                  <div class="mb-3" *ngIf="bikeAvailability">
                    <h6>Bike Parking</h6>
                    <div class="progress mb-2" style="height: 20px;">
                      <div
                        class="progress-bar"
                        [class.bg-success]="bikeAvailability.occupancy_rate < 70"
                        [class.bg-warning]="bikeAvailability.occupancy_rate >= 70 && bikeAvailability.occupancy_rate < 90"
                        [class.bg-danger]="bikeAvailability.occupancy_rate >= 90"
                        [style.width.%]="bikeAvailability.occupancy_rate"
                      >
                        {{ bikeAvailability.occupancy_rate.toFixed(0) }}% Occupied
                      </div>
                    </div>
                    <div class="d-flex justify-content-between">
                      <span>Available: <strong>{{ bikeAvailability.available_slots }}</strong></span>
                      <span>Total: <strong>{{ bikeAvailability.total_slots }}</strong></span>
                    </div>
                  </div>

                  <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    Last updated: {{ lastUpdated | date:'short' }}
                  </small>
                </div>
              </div>
            </div>

            <!-- Features & Amenities -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-list-check me-2"></i>
                  Features & Amenities
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <ul class="list-unstyled">
                      <li class="mb-2">
                        <i class="fas fa-shield-alt text-success me-2"></i>
                        24/7 Security
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-camera text-info me-2"></i>
                        CCTV Surveillance
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-lightbulb text-warning me-2"></i>
                        Well Lit
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-wheelchair text-primary me-2"></i>
                        Wheelchair Accessible
                      </li>
                    </ul>
                  </div>
                  <div class="col-md-6">
                    <ul class="list-unstyled">
                      <li class="mb-2">
                        <i class="fas fa-qrcode text-secondary me-2"></i>
                        QR Code Access
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-mobile-alt text-success me-2"></i>
                        Mobile App Integration
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-headset text-info me-2"></i>
                        24/7 Support
                      </li>
                      <li class="mb-2">
                        <i class="fas fa-credit-card text-primary me-2"></i>
                        Multiple Payment Options
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <!-- Operating Hours -->
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-clock me-2"></i>
                  Operating Hours
                </h5>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <div class="d-flex justify-content-between mb-2">
                      <span>Monday - Friday:</span>
                      <span class="fw-bold">24 Hours</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                      <span>Saturday:</span>
                      <span class="fw-bold">24 Hours</span>
                    </div>
                    <div class="d-flex justify-content-between">
                      <span>Sunday:</span>
                      <span class="fw-bold">24 Hours</span>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="alert alert-success mb-0">
                      <i class="fas fa-check-circle me-2"></i>
                      <strong>Open 24/7</strong>
                      <br>
                      <small>Access available at all times</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="col-lg-4">
            <!-- Quick Booking -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-zap me-2"></i>
                  Quick Book
                </h5>
              </div>
              <div class="card-body">
                <p class="mb-3">Book your parking space now for immediate or future use.</p>
                <div class="d-grid gap-2">
                  <button 
                    class="btn btn-success"
                    [disabled]="!parkingLot.is_active"
                    (click)="bookNow('car')"
                  >
                    <i class="fas fa-car me-2"></i>
                    Book Car Space
                  </button>
                  <button 
                    class="btn btn-info"
                    [disabled]="!parkingLot.is_active"
                    (click)="bookNow('bike')"
                  >
                    <i class="fas fa-motorcycle me-2"></i>
                    Book Bike Space
                  </button>
                </div>
                <small class="text-muted mt-2 d-block">
                  <i class="fas fa-info-circle me-1"></i>
                  Guaranteed spot once booked
                </small>
              </div>
            </div>

            <!-- Location Map Placeholder -->
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-map me-2"></i>
                  Location
                </h5>
              </div>
              <div class="card-body p-0">
                <div class="map-placeholder bg-light d-flex align-items-center justify-content-center" style="height: 200px;">
                  <div class="text-center">
                    <i class="fas fa-map fa-2x text-muted mb-2"></i>
                    <p class="text-muted mb-0">Interactive Map</p>
                    <small class="text-muted">{{ parkingLot.latitude }}, {{ parkingLot.longitude }}</small>
                  </div>
                </div>
              </div>
            </div>

            <!-- Contact Information -->
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-phone me-2"></i>
                  Contact & Support
                </h5>
              </div>
              <div class="card-body">
                <div class="mb-3">
                  <strong>Emergency Contact:</strong>
                  <br>
                  <a href="tel:+15551234567" class="text-decoration-none">
                    <i class="fas fa-phone me-1"></i>
                    (555) 123-PARK
                  </a>
                </div>
                <div class="mb-3">
                  <strong>Support Email:</strong>
                  <br>
                  <a href="mailto:support@smartparking.com" class="text-decoration-none">
                    <i class="fas fa-envelope me-1"></i>
                    support@smartparking.com
                  </a>
                </div>
                <div>
                  <strong>Report Issues:</strong>
                  <br>
                  <button class="btn btn-sm btn-outline-warning">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    Report Problem
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Back Button -->
        <div class="row mt-4">
          <div class="col-12">
            <button class="btn btn-outline-primary" (click)="goBack()">
              <i class="fas fa-arrow-left me-2"></i>
              Back to Search
            </button>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div class="row" *ngIf="!loading && !parkingLot">
        <div class="col-12">
          <div class="text-center py-5">
            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h4>Parking Lot Not Found</h4>
            <p class="text-muted mb-4">
              {{ errorMessage || 'The parking lot you are looking for could not be found.' }}
            </p>
            <button class="btn btn-primary" routerLink="/parking">
              <i class="fas fa-search me-2"></i>
              Search Parking
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Custom CSS -->
    <style>
      .icon-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
      }

      .map-placeholder {
        cursor: pointer;
        transition: background-color 0.3s;
      }

      .map-placeholder:hover {
        background-color: #e9ecef !important;
      }
    </style>
  `
})
export class ParkingDetailsComponent implements OnInit, OnDestroy {
  parkingLot: ParkingLot | null = null;
  carAvailability: AvailabilityResponse | null = null;
  bikeAvailability: AvailabilityResponse | null = null;
  distance: number | null = null;
  loading = true;
  loadingAvailability = false;
  errorMessage = '';
  lastUpdated = new Date();
  
  private destroy$ = new Subject<void>();

  constructor(
    private parkingService: ParkingService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadParkingLotDetails();
    this.getCurrentLocation();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadParkingLotDetails(): void {
    const lotId = this.route.snapshot.params['id'];
    
    if (lotId) {
      this.parkingService.getParkingLot(lotId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (lot) => {
            this.parkingLot = lot;
            this.loading = false;
            this.loadAvailability();
          },
          error: (error) => {
            this.errorMessage = error.message || 'Failed to load parking lot details';
            this.loading = false;
          }
        });
    }
  }

  private getCurrentLocation(): void {
    this.parkingService.getCurrentLocation()
      .then(position => {
        if (this.parkingLot) {
          this.distance = this.parkingService.calculateDistance(
            position.coords.latitude,
            position.coords.longitude,
            this.parkingLot.latitude,
            this.parkingLot.longitude
          );
        }
      })
      .catch(error => {
        console.log('Could not get current location:', error);
      });
  }

  private loadAvailability(): void {
    if (!this.parkingLot) return;
    
    this.loadingAvailability = true;
    
    // Get availability for both car and bike
    forkJoin({
      car: this.parkingService.checkAvailability(this.parkingLot.id, 'car'),
      bike: this.parkingService.checkAvailability(this.parkingLot.id, 'bike')
    })
    .pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (availability) => {
        this.carAvailability = availability.car;
        this.bikeAvailability = availability.bike;
        this.lastUpdated = new Date();
        this.loadingAvailability = false;
      },
      error: (error) => {
        console.error('Error loading availability:', error);
        this.loadingAvailability = false;
      }
    });
  }

  refreshAvailability(): void {
    this.loadAvailability();
  }

  bookNow(vehicleType?: string): void {
    if (!this.parkingLot) return;
    
    const now = nowIST();
    // Add 30 minutes buffer to ensure future time
    const startTime = new Date(now.getTime() + 30 * 60 * 1000);
    const oneHourLater = new Date(startTime.getTime() + 60 * 60 * 1000);
    
    const queryParams: any = {
      lotId: this.parkingLot.id,
      startTime: toDatetimeLocalIST(startTime),
      endTime: toDatetimeLocalIST(oneHourLater)
    };
    
    if (vehicleType) {
      queryParams.vehicleType = vehicleType;
    }
    
    this.router.navigate(['/booking'], { queryParams });
  }

  getDirections(): void {
    if (!this.parkingLot) return;
    
    const url = `https://www.google.com/maps/dir/?api=1&destination=${this.parkingLot.latitude},${this.parkingLot.longitude}`;
    window.open(url, '_blank');
  }

  shareLocation(): void {
    if (!this.parkingLot) return;
    
    if (navigator.share) {
      navigator.share({
        title: this.parkingLot.name,
        text: `Check out this parking lot: ${this.parkingLot.name}`,
        url: window.location.href
      });
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(window.location.href).then(() => {
        alert('Location link copied to clipboard!');
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/parking']);
  }

  private formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }
}