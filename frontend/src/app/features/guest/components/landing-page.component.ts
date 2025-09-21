import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { GuestService } from '../services/guest.service';
import { ParkingService } from '../../parking/services/parking.service';
import { AuthService } from '../../auth/services/auth.service';
import { ParkingLot } from '../../../core/models/parking.model';

interface GuestSearchForm {
  location: string;
  vehicleType: string;
  startTime: string;
  endTime: string;
}

@Component({
  selector: 'app-guest-landing',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="guest-landing">
      <!-- Hero Section -->
      <section class="hero-section bg-primary text-white py-5">
        <div class="container">
          <div class="row align-items-center">
            <div class="col-lg-6">
              <h1 class="display-4 fw-bold mb-4">Smart Parking Made Simple</h1>
              <p class="lead mb-4">
                Find and book parking spots instantly. Real-time availability, 
                dynamic pricing, and seamless booking experience.
              </p>
              <div class="d-flex gap-3">
                <button 
                  class="btn btn-light btn-lg"
                  (click)="scrollToSearch()">
                  Find Parking Now
                </button>
                <button 
                  class="btn btn-outline-light btn-lg"
                  (click)="navigateToAuth('register')">
                  Create Account
                </button>
              </div>
            </div>
            <div class="col-lg-6">
              <div class="hero-image text-center">
                <i class="fas fa-car fa-10x opacity-75"></i>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick Search Section -->
      <section class="search-section py-5" id="search-section">
        <div class="container">
          <div class="row justify-content-center">
            <div class="col-lg-8">
              <div class="card shadow-lg">
                <div class="card-header bg-white d-flex justify-content-between align-items-center">
                  <div class="text-center flex-grow-1">
                    <h3 class="mb-0">Find Parking Near You</h3>
                    <p class="text-muted mb-0" *ngIf="!isSearchFormMinimized">
                      Search available parking spots in real-time
                    </p>
                  </div>
                  <button 
                    type="button" 
                    class="btn btn-link p-0"
                    (click)="toggleSearchForm()"
                    *ngIf="searchResults.length > 0">
                    <i class="fas" 
                       [ngClass]="isSearchFormMinimized ? 'fa-chevron-down' : 'fa-chevron-up'"></i>
                  </button>
                </div>
                <div class="card-body" [ngClass]="{'d-none': isSearchFormMinimized}">
                  <form (ngSubmit)="onGuestSearch()" #searchForm="ngForm">
                    <div class="row g-3">
                      <!-- Location Input -->
                      <div class="col-md-12">
                        <label class="form-label">Location</label>
                        <div class="input-group">
                          <input
                            type="text"
                            class="form-control"
                            [(ngModel)]="guestSearchData.location"
                            name="location"
                            placeholder="Enter address or landmark"
                            required>
                          <button 
                            type="button" 
                            class="btn btn-outline-secondary"
                            (click)="getCurrentLocation()">
                            <i class="fas fa-location-arrow"></i>
                          </button>
                        </div>
                      </div>

                      <!-- Vehicle Type & Time Row -->
                      <div class="col-md-4">
                        <label class="form-label">Vehicle Type</label>
                        <select 
                          class="form-select"
                          [(ngModel)]="guestSearchData.vehicleType"
                          name="vehicleType"
                          required>
                          <option value="">Select Type</option>
                          <option value="car">Car</option>
                          <option value="bike">Bike</option>
                        </select>
                      </div>

                      <div class="col-md-4">
                        <label class="form-label">Start Time</label>
                        <input
                          type="datetime-local"
                          class="form-control"
                          [(ngModel)]="guestSearchData.startTime"
                          name="startTime"
                          [min]="minDateTime"
                          required>
                      </div>

                      <div class="col-md-4">
                        <label class="form-label">End Time</label>
                        <input
                          type="datetime-local"
                          class="form-control"
                          [(ngModel)]="guestSearchData.endTime"
                          name="endTime"
                          [min]="guestSearchData.startTime"
                          required>
                      </div>
                    </div>

                    <!-- Search Button -->
                    <div class="row mt-4">
                      <div class="col-12">
                        <button 
                          type="submit" 
                          class="btn btn-primary btn-lg w-100"
                          [disabled]="!searchForm.form.valid || isSearching">
                          <span *ngIf="isSearching" class="spinner-border spinner-border-sm me-2"></span>
                          <i *ngIf="!isSearching" class="fas fa-search me-2"></i>
                          {{ isSearching ? 'Searching...' : 'Search Available Parking' }}
                        </button>
                      </div>
                    </div>

                    <!-- Validation Messages -->
                    <div *ngIf="searchError" class="alert alert-warning mt-3">
                      <i class="fas fa-exclamation-triangle me-2"></i>{{ searchError }}
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Search Results Preview -->
      <section *ngIf="searchResults.length > 0" class="results-preview py-4">
        <div class="container">
          <div class="row">
            <div class="col-12">
              <h4 class="mb-3">Available Parking Lots</h4>
              <div class="row">
                <div 
                  *ngFor="let lot of searchResults | slice:0:(showAllResults ? searchResults.length : 3)" 
                  class="col-md-4 mb-3">
                  <div class="card h-100">
                    <div class="card-body">
                      <h5 class="card-title">{{ lot.name }}</h5>
                      <p class="card-text text-muted">{{ lot.address }}</p>
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-success">
                          {{ (lot.available_car_slots || 0) + (lot.available_bike_slots || 0) }} spots available
                        </span>
                        <span class="fw-bold text-primary">
                          \${{ lot.hourly_rate_car }}/hr
                        </span>
                      </div>
                      <div class="small text-muted mb-2">
                        <i class="fas fa-car me-1"></i>{{ lot.available_car_slots || 0 }} cars • 
                        <i class="fas fa-motorcycle ms-2 me-1"></i>{{ lot.available_bike_slots || 0 }} bikes
                      </div>
                      <button 
                        class="btn btn-outline-primary btn-sm mt-2 w-100"
                        (click)="onBookNow(lot)">
                        Book Now
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- View All Results -->
              <div class="text-center mt-4" *ngIf="searchResults.length > 3 && !showAllResults">
                <button 
                  class="btn btn-primary"
                  (click)="viewAllResults()">
                  View All {{ searchResults.length }} Results
                </button>
              </div>
              
              <!-- Show Less Results -->
              <div class="text-center mt-4" *ngIf="showAllResults && searchResults.length > 3">
                <button 
                  class="btn btn-outline-secondary"
                  (click)="showAllResults = false">
                  Show Less
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Features Section -->
      <section class="features-section py-5 bg-light">
        <div class="container">
          <div class="row text-center">
            <div class="col-12 mb-5">
              <h2>Why Choose Smart Parking?</h2>
              <p class="lead text-muted">Experience the future of parking management</p>
            </div>
          </div>
          <div class="row">
            <div class="col-md-4 mb-4">
              <div class="feature-card text-center">
                <i class="fas fa-clock fa-3x text-primary mb-3"></i>
                <h4>Real-Time Availability</h4>
                <p class="text-muted">
                  See live parking availability and reserve your spot instantly
                </p>
              </div>
            </div>
            <div class="col-md-4 mb-4">
              <div class="feature-card text-center">
                <i class="fas fa-dollar-sign fa-3x text-primary mb-3"></i>
                <h4>Dynamic Pricing</h4>
                <p class="text-muted">
                  Transparent pricing based on demand, time, and location
                </p>
              </div>
            </div>
            <div class="col-md-4 mb-4">
              <div class="feature-card text-center">
                <i class="fas fa-mobile-alt fa-3x text-primary mb-3"></i>
                <h4>Easy Booking</h4>
                <p class="text-muted">
                  Book, pay, and manage your parking from your mobile device
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="cta-section py-5 bg-primary text-white">
        <div class="container">
          <div class="row text-center">
            <div class="col-lg-8 mx-auto">
              <h2 class="mb-4">Ready to Start Parking Smarter?</h2>
              <p class="lead mb-4">
                Join thousands of users who have simplified their parking experience
              </p>
              <div class="d-flex justify-content-center gap-3">
                <button 
                  class="btn btn-light btn-lg"
                  (click)="navigateToAuth('register')">
                  <i class="fas fa-user-plus me-2"></i>Sign Up Free
                </button>
                <button 
                  class="btn btn-outline-light btn-lg"
                  (click)="navigateToAuth('login')">
                  <i class="fas fa-sign-in-alt me-2"></i>Login
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .guest-landing {
      min-height: 100vh;
    }

    .hero-section {
      background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    }

    .hero-image {
      opacity: 0.1;
    }

    .search-section {
      margin-top: -50px;
      position: relative;
      z-index: 10;
    }

    .card {
      border: none;
      border-radius: 15px;
    }

    .card-header {
      border-radius: 15px 15px 0 0 !important;
      border-bottom: 1px solid #e9ecef;
    }

    .feature-card {
      padding: 2rem;
      transition: transform 0.3s ease;
    }

    .feature-card:hover {
      transform: translateY(-5px);
    }

    .btn-lg {
      padding: 0.75rem 2rem;
      font-size: 1.1rem;
    }

    .results-preview .card {
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .results-preview .card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    @media (max-width: 768px) {
      .hero-section {
        text-align: center;
      }
      
      .hero-section .col-lg-6:first-child {
        margin-bottom: 2rem;
      }
      
      .d-flex.gap-3 {
        flex-direction: column;
        gap: 1rem !important;
      }
    }
  `]
})
export class GuestLandingPageComponent implements OnInit {
  guestSearchData: GuestSearchForm = {
    location: '',
    vehicleType: '',
    startTime: '',
    endTime: ''
  };

  searchResults: ParkingLot[] = [];
  isSearching = false;
  searchError = '';
  minDateTime = '';
  isSearchFormMinimized = false;
  showAllResults = false;

  constructor(
    private guestService: GuestService,
    private parkingService: ParkingService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeDateTime();
  }

  private initializeDateTime(): void {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5); // 5 minutes from now
    this.minDateTime = this.formatDateTimeLocal(now);
    
    // Set default start time to 5 minutes from now
    this.guestSearchData.startTime = this.formatDateTimeLocal(now);
    
    // Set default end time to 1 hour later
    const endTime = new Date(now);
    endTime.setHours(endTime.getHours() + 1);
    this.guestSearchData.endTime = this.formatDateTimeLocal(endTime);
  }

  private formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  getCurrentLocation(): void {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          this.guestSearchData.location = `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
        },
        (error) => {
          console.error('Error getting location:', error);
          this.searchError = 'Could not get your current location. Please enter manually.';
          setTimeout(() => this.searchError = '', 3000);
        }
      );
    } else {
      this.searchError = 'Geolocation is not supported by this browser.';
      setTimeout(() => this.searchError = '', 3000);
    }
  }

  async onGuestSearch(): Promise<void> {
    if (!this.validateSearchForm()) {
      return;
    }

    this.isSearching = true;
    this.searchError = '';
    this.showAllResults = false; // Reset show all results for new search

    try {
      const searchParams = {
        location: this.guestSearchData.location,
        vehicleType: this.guestSearchData.vehicleType,
        startTime: new Date(this.guestSearchData.startTime).toISOString(),
        endTime: new Date(this.guestSearchData.endTime).toISOString()
      };

      this.searchResults = await this.guestService.searchParkingAsGuest(searchParams);
      
      if (this.searchResults.length === 0) {
        this.searchError = 'No parking lots found for your criteria. Try adjusting your search.';
      } else {
        // Auto-minimize search form after successful search
        this.isSearchFormMinimized = true;
      }

    } catch (error) {
      console.error('Search error:', error);
      this.searchError = 'Failed to search parking lots. Please try again.';
    } finally {
      this.isSearching = false;
    }
  }

  private validateSearchForm(): boolean {
    if (!this.guestSearchData.location) {
      this.searchError = 'Please enter a location.';
      return false;
    }

    if (!this.guestSearchData.vehicleType) {
      this.searchError = 'Please select a vehicle type.';
      return false;
    }

    const startTime = new Date(this.guestSearchData.startTime);
    const endTime = new Date(this.guestSearchData.endTime);
    const now = new Date();

    if (startTime <= now) {
      this.searchError = 'Start time must be in the future.';
      return false;
    }

    if (endTime <= startTime) {
      this.searchError = 'End time must be after start time.';
      return false;
    }

    // Minimum booking duration of 15 minutes
    const durationMinutes = (endTime.getTime() - startTime.getTime()) / (1000 * 60);
    if (durationMinutes < 15) {
      this.searchError = 'Minimum booking duration is 15 minutes.';
      return false;
    }

    return true;
  }

  // Removed old proceedToBooking method - replaced with onBookNow

  navigateToAuth(type: 'login' | 'register'): void {
    this.router.navigate([`/auth/${type}`]);
  }

  scrollToSearch(): void {
    const element = document.getElementById('search-section');
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  }

  toggleSearchForm(): void {
    this.isSearchFormMinimized = !this.isSearchFormMinimized;
  }

  viewAllResults(): void {
    this.showAllResults = true;
  }

  onBookNow(lot: ParkingLot): void {
    // Save the current search context and selected lot
    const guestContext = this.guestService.getGuestSearchContext();
    if (guestContext) {
      this.guestService.createGuestBookingIntent({
        lotId: lot.id,
        location: guestContext.location,
        vehicleType: guestContext.vehicleType,
        startTime: guestContext.startTime,
        endTime: guestContext.endTime
      });
    }

    // Navigate to login with booking intent
    this.router.navigate(['/auth/login'], {
      queryParams: {
        guest: 'true',
        lotId: lot.id,
        message: 'Please login to complete your booking.'
      }
    });
  }
}
