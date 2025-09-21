import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { GuestService } from '../services/guest.service';
import { ParkingService } from '../../parking/services/parking.service';
import { AuthService } from '../../auth/services/auth.service';
import { ParkingLot } from '../../../core/models/parking.model';

interface GuestSearchParams {
  location: string;
  vehicleType: string;
  startTime: string;
  endTime: string;
}

@Component({
  selector: 'app-guest-search',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="guest-search">
      <!-- Header -->
      <div class="bg-light py-3 mb-4">
        <div class="container">
          <div class="row align-items-center">
            <div class="col-md-8">
              <h2 class="mb-0">
                <i class="fas fa-search me-2 text-primary"></i>
                Parking Search Results
              </h2>
              <p class="text-muted mb-0">
                Found {{ searchResults.length }} parking lot{{ searchResults.length !== 1 ? 's' : '' }} 
                for your search
              </p>
            </div>
            <div class="col-md-4 text-end">
              <button 
                class="btn btn-outline-primary"
                (click)="goBack()">
                <i class="fas fa-arrow-left me-2"></i>New Search
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Search Criteria Summary -->
      <div class="container mb-4">
        <div class="card">
          <div class="card-body py-3">
            <div class="row g-3 align-items-center">
              <div class="col-md-3">
                <small class="text-muted">Location:</small>
                <div class="fw-semibold">{{ searchCriteria.location }}</div>
              </div>
              <div class="col-md-2">
                <small class="text-muted">Vehicle:</small>
                <div class="fw-semibold text-capitalize">{{ searchCriteria.vehicleType }}</div>
              </div>
              <div class="col-md-3">
                <small class="text-muted">Start Time:</small>
                <div class="fw-semibold">{{ formatDateTime(searchCriteria.startTime) }}</div>
              </div>
              <div class="col-md-3">
                <small class="text-muted">End Time:</small>
                <div class="fw-semibold">{{ formatDateTime(searchCriteria.endTime) }}</div>
              </div>
              <div class="col-md-1 text-end">
                <button 
                  class="btn btn-sm btn-outline-secondary"
                  (click)="modifySearch()"
                  title="Modify Search">
                  <i class="fas fa-edit"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Search Results -->
      <div class="container">
        <div class="row">
          <!-- Loading State -->
          <div *ngIf="isLoading" class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Searching for available parking...</p>
          </div>

          <!-- Error State -->
          <div *ngIf="searchError && !isLoading" class="col-12">
            <div class="alert alert-warning text-center">
              <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
              <h5>{{ searchError }}</h5>
              <button 
                class="btn btn-outline-primary mt-2"
                (click)="retrySearch()">
                Try Again
              </button>
            </div>
          </div>

          <!-- No Results -->
          <div *ngIf="searchResults.length === 0 && !isLoading && !searchError" class="col-12">
            <div class="alert alert-info text-center">
              <i class="fas fa-info-circle fa-2x mb-3"></i>
              <h5>No Parking Available</h5>
              <p>No parking lots found matching your criteria. Try adjusting your search parameters.</p>
              <button 
                class="btn btn-primary"
                (click)="modifySearch()">
                Modify Search
              </button>
            </div>
          </div>

          <!-- Results Grid -->
          <div *ngIf="searchResults.length > 0 && !isLoading" class="col-12">
            <div class="row">
              <div 
                *ngFor="let lot of searchResults; trackBy: trackByLotId" 
                class="col-lg-6 col-xl-4 mb-4">
                <div class="card h-100 parking-lot-card">
                  <div class="card-body">
                    <!-- Lot Header -->
                    <div class="d-flex justify-content-between align-items-start mb-3">
                      <div>
                        <h5 class="card-title mb-1">{{ lot.name }}</h5>
                        <p class="text-muted small mb-0">
                          <i class="fas fa-map-marker-alt me-1"></i>
                          {{ lot.address }}
                        </p>
                      </div>
                      <span 
                        class="badge"
                        [ngClass]="{
                          'bg-success': getAvailableSlots(lot) > 5,
                          'bg-warning': getAvailableSlots(lot) <= 5 && getAvailableSlots(lot) > 0,
                          'bg-danger': getAvailableSlots(lot) === 0
                        }">
                        {{ getAvailableSlots(lot) }} available
                      </span>
                    </div>

                    <!-- Lot Details -->
                    <div class="lot-details mb-3">
                      <div class="row g-2 small">
                        <div class="col-6">
                          <i class="fas fa-car text-primary me-1"></i>
                          Car slots: {{ lot.total_car_slots }}
                        </div>
                        <div class="col-6">
                          <i class="fas fa-motorcycle text-primary me-1"></i>
                          Bike slots: {{ lot.total_bike_slots }}
                        </div>
                        <div class="col-6">
                          <i class="fas fa-clock text-primary me-1"></i>
                          24/7 Access
                        </div>
                        <div class="col-6">
                          <i class="fas fa-shield-alt text-primary me-1"></i>
                          Secure
                        </div>
                      </div>
                    </div>

                    <!-- Pricing -->
                    <div class="pricing-section mb-3">
                      <div class="d-flex justify-content-between align-items-center">
                        <div>
                          <span class="text-muted small">Hourly Rate:</span>
                          <div class="fw-bold text-primary fs-5">
                            \${{ lot.hourly_rate_car }}/hour
                          </div>
                        </div>
                        <div class="text-end">
                          <span class="text-muted small">Estimated Total:</span>
                          <div class="fw-bold">
                            \${{ calculateEstimatedCost(lot.hourly_rate_car) }}
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="d-grid gap-2">
                      <button 
                        class="btn btn-primary"
                        [disabled]="getAvailableSlots(lot) === 0"
                        (click)="selectParkingLot(lot)">
                        <i class="fas fa-parking me-2"></i>
                        {{ getAvailableSlots(lot) === 0 ? 'Fully Booked' : 'Book This Spot' }}
                      </button>
                      <button 
                        class="btn btn-outline-secondary btn-sm"
                        (click)="viewLotDetails(lot)">
                        <i class="fas fa-info-circle me-2"></i>
                        View Details
                      </button>
                    </div>
                  </div>

                  <!-- Quick Info Footer -->
                  <div class="card-footer bg-light">
                    <div class="d-flex justify-content-between align-items-center small">
                      <span class="text-muted">
                        <i class="fas fa-walking me-1"></i>
                        {{ calculateDistance(lot) }} away
                      </span>
                      <span class="text-success">
                        <i class="fas fa-check-circle me-1"></i>
                        Instant booking
                      </span>
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
    .guest-search {
      min-height: 100vh;
      background-color: #f8f9fa;
    }

    .parking-lot-card {
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      border: none;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .parking-lot-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }

    .lot-details {
      background-color: #f8f9fa;
      border-radius: 8px;
      padding: 0.75rem;
    }

    .pricing-section {
      border-top: 1px solid #dee2e6;
      border-bottom: 1px solid #dee2e6;
      padding: 0.75rem 0;
    }

    .badge {
      font-size: 0.75rem;
    }

    .btn-primary {
      background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
      border: none;
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
    }

    .card-footer {
      border-top: 1px solid #dee2e6;
    }

    @media (max-width: 768px) {
      .row.g-3.align-items-center > div {
        text-align: center;
        margin-bottom: 0.5rem;
      }
      
      .col-md-1.text-end {
        text-align: center !important;
      }
    }
  `]
})
export class GuestSearchComponent implements OnInit {
  searchResults: ParkingLot[] = [];
  searchCriteria: GuestSearchParams = {
    location: '',
    vehicleType: '',
    startTime: '',
    endTime: ''
  };
  
  isLoading = false;
  searchError = '';
  selectedLot: ParkingLot | null = null;

  constructor(
    private guestService: GuestService,
    private parkingService: ParkingService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.initializeFromQueryParams();
    this.loadSearchResults();
  }

  private initializeFromQueryParams(): void {
    this.route.queryParams.subscribe(params => {
      if (params['location']) {
        this.searchCriteria = {
          location: params['location'] || '',
          vehicleType: params['vehicleType'] || '',
          startTime: params['startTime'] || '',
          endTime: params['endTime'] || ''
        };
      } else {
        // Try to get from guest service
        const context = this.guestService.getGuestSearchContext();
        if (context) {
          this.searchCriteria = {
            location: context.location,
            vehicleType: context.vehicleType,
            startTime: context.startTime,
            endTime: context.endTime
          };
        }
      }
    });
  }

  private async loadSearchResults(): Promise<void> {
    // Try to get cached results first
    const cachedResults = this.guestService.getGuestSearchResults();
    if (cachedResults && cachedResults.length > 0) {
      this.searchResults = cachedResults;
      return;
    }

    // If no cached results, perform search
    if (this.searchCriteria.location && this.searchCriteria.vehicleType) {
      await this.performSearch();
    }
  }

  private async performSearch(): Promise<void> {
    this.isLoading = true;
    this.searchError = '';

    try {
      const searchParams = {
        location: this.searchCriteria.location,
        vehicleType: this.searchCriteria.vehicleType,
        startTime: new Date(this.searchCriteria.startTime).toISOString(),
        endTime: new Date(this.searchCriteria.endTime).toISOString()
      };

      this.searchResults = await this.guestService.searchParkingAsGuest(searchParams);
      
      if (this.searchResults.length === 0) {
        this.searchError = 'No parking lots found for your criteria.';
      }

    } catch (error) {
      console.error('Search error:', error);
      this.searchError = 'Failed to search parking lots. Please try again.';
    } finally {
      this.isLoading = false;
    }
  }

  formatDateTime(dateTimeStr: string): string {
    if (!dateTimeStr) return '';
    
    const date = new Date(dateTimeStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  }

  getAvailableSlots(lot: ParkingLot): number {
    return (lot.available_car_slots || 0) + (lot.available_bike_slots || 0);
  }

  calculateEstimatedCost(hourlyRate: number): string {
    if (!this.searchCriteria.startTime || !this.searchCriteria.endTime) {
      return '0.00';
    }

    const startTime = new Date(this.searchCriteria.startTime);
    const endTime = new Date(this.searchCriteria.endTime);
    const durationHours = (endTime.getTime() - startTime.getTime()) / (1000 * 60 * 60);
    
    return (hourlyRate * durationHours).toFixed(2);
  }

  calculateDistance(lot: ParkingLot): string {
    // Placeholder - in real implementation, calculate based on coordinates
    return `${(Math.random() * 2 + 0.5).toFixed(1)} km`;
  }

  selectParkingLot(lot: ParkingLot): void {
    this.selectedLot = lot;
    
    // Store guest context with selected lot
    this.guestService.setGuestSearchContext({
      ...this.searchCriteria,
      selectedLot: lot
    });

    // Show login modal
    this.showLoginModal();
  }

  viewLotDetails(lot: ParkingLot): void {
    // Navigate to lot details with guest context
    this.router.navigate(['/parking/details', lot.id], {
      queryParams: { 
        guest: 'true',
        returnUrl: '/guest/search'
      }
    });
  }

  modifySearch(): void {
    this.router.navigate(['/guest'], {
      queryParams: {
        location: this.searchCriteria.location,
        vehicleType: this.searchCriteria.vehicleType,
        startTime: this.searchCriteria.startTime,
        endTime: this.searchCriteria.endTime
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/guest']);
  }

  async retrySearch(): Promise<void> {
    await this.performSearch();
  }

  trackByLotId(index: number, lot: ParkingLot): string {
    return lot.id;
  }

  private showLoginModal(): void {
    // In a real implementation, use Bootstrap modal
    // For now, navigate directly to login
    this.proceedToLogin();
  }

  proceedToLogin(): void {
    const returnUrl = '/parking/book';
    this.router.navigate(['/auth/login'], {
      queryParams: {
        returnUrl,
        guest: 'true',
        lotId: this.selectedLot?.id,
        message: `Please login to book parking at ${this.selectedLot?.name}`
      }
    });
  }

  proceedToRegister(): void {
    const returnUrl = '/parking/book';
    this.router.navigate(['/auth/register'], {
      queryParams: {
        returnUrl,
        guest: 'true',
        lotId: this.selectedLot?.id,
        message: `Create an account to book parking at ${this.selectedLot?.name}`
      }
    });
  }

  closeModal(): void {
    this.selectedLot = null;
    // Close modal logic
  }
}
