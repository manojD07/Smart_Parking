import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { ParkingService } from '../services/parking.service';
import { BookingService } from '../../booking/services/booking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { ParkingLot, VehicleType, AvailabilityResponse } from '../../../core/models/parking.model';

@Component({
  selector: 'app-parking-search',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LoadingComponent],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <h1 class="h2 mb-4">Find Parking</h1>
        </div>
      </div>

      <!-- Search Form -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <i class="fas fa-search me-2"></i>
                  Search Criteria
                </h5>
                <button 
                  class="btn btn-sm btn-outline-secondary"
                  type="button"
                  (click)="toggleSearchForm()"
                  [attr.aria-expanded]="!searchFormCollapsed"
                  aria-controls="searchFormCollapse"
                >
                  <i class="fas" [class.fa-chevron-up]="!searchFormCollapsed" [class.fa-chevron-down]="searchFormCollapsed"></i>
                  {{ searchFormCollapsed ? 'Expand' : 'Minimize' }}
                </button>
              </div>
            </div>
            <div class="card-body collapse" [class.show]="!searchFormCollapsed" id="searchFormCollapse">
              <!-- Initial Vehicle Type Reminder -->
              <div class="alert alert-warning" *ngIf="!searchForm.get('vehicleType')?.value && !hasSearched">
                <i class="fas fa-car me-2"></i>
                <strong>Start Here:</strong> Please select your vehicle type first to see accurate parking rates and availability for your specific vehicle.
              </div>

              <form [formGroup]="searchForm" (ngSubmit)="onSearch()">
                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="vehicleType" class="form-label">
                      Vehicle Type <span class="text-danger">*</span>
                      <small class="text-muted">(Required for accurate pricing)</small>
                    </label>
                    <select
                      class="form-select form-select-lg-mobile"
                      id="vehicleType"
                      formControlName="vehicleType"
                      [class.is-invalid]="isFieldInvalid('vehicleType')"
                      [class.border-danger]="errorMessage && !searchForm.get('vehicleType')?.value"
                      [style.animation]="errorMessage && !searchForm.get('vehicleType')?.value ? 'pulse 1s ease-in-out 3' : 'none'"
                      (change)="onVehicleTypeChange()"
                    >
                      <option value="">Select vehicle type</option>
                      <option value="car">Car</option>
                      <option value="bike">Bike/Motorcycle</option>
                      <option value="truck">Truck</option>
                      <option value="electric_car">Electric Car</option>
                      <option value="electric_bike">Electric Bike</option>
                    </select>
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('vehicleType')">
                      Please select a vehicle type
                    </div>
                    
                    <!-- Warning when no vehicle type selected -->
                    <div class="form-text text-danger" *ngIf="!searchForm.get('vehicleType')?.value && (searchForm.get('vehicleType')?.touched || hasSearched)">
                      <i class="fas fa-exclamation-circle me-1"></i>
                      <strong>Required:</strong> Please select your vehicle type to see accurate pricing and availability.
                    </div>
                    
                    <!-- Info when vehicle type is selected -->
                    <div class="form-text text-info" *ngIf="searchForm.get('vehicleType')?.value">
                      <i class="fas fa-info-circle me-1"></i>
                      <strong>Good:</strong> Vehicle type selected. You'll see accurate rates for {{ searchForm.get('vehicleType')?.value | titlecase }} parking.
                    </div>
                  </div>

                  <div class="col-md-6 mb-3">
                    <label for="location" class="form-label">Location</label>
                    <div class="input-group">
                      <input
                        type="text"
                        class="form-control"
                        id="location"
                        formControlName="location"
                        placeholder="Enter location or use current location"
                      />
                      <button
                        type="button"
                        class="btn btn-outline-secondary"
                        (click)="getCurrentLocation()"
                        [disabled]="gettingLocation"
                      >
                        <i class="fas fa-location-arrow" *ngIf="!gettingLocation"></i>
                        <span class="spinner-border spinner-border-sm" *ngIf="gettingLocation"></span>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label for="startTime" class="form-label">Start Time</label>
                    <input
                      type="datetime-local"
                      class="form-control"
                      id="startTime"
                      formControlName="startTime"
                      [class.is-invalid]="isFieldInvalid('startTime')"
                    />
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('startTime')">
                      Please select a start time
                    </div>
                  </div>

                  <div class="col-md-6 mb-3">
                    <label for="endTime" class="form-label">End Time</label>
                    <input
                      type="datetime-local"
                      class="form-control"
                      id="endTime"
                      formControlName="endTime"
                      [class.is-invalid]="isFieldInvalid('endTime')"
                    />
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('endTime')">
                      Please select an end time
                    </div>
                  </div>
                </div>

                <div class="row">
                  <div class="col-md-4 mb-3">
                    <label for="radius" class="form-label">Search Radius (km)</label>
                    <select class="form-select" id="radius" formControlName="radius">
                      <option value="1">1 km</option>
                      <option value="5">5 km</option>
                      <option value="10">10 km</option>
                      <option value="25">25 km</option>
                      <option value="50">50 km</option>
                    </select>
                  </div>

                  <div class="col-md-4 mb-3">
                    <label for="sortBy" class="form-label">Sort By</label>
                    <select class="form-select" id="sortBy" formControlName="sortBy">
                      <option value="distance">Distance</option>
                      <option value="price">Price</option>
                      <option value="availability">Availability</option>
                    </select>
                  </div>

                  <div class="col-md-4 mb-3 d-flex align-items-end">
                    <button
                      type="submit"
                      class="btn btn-primary w-100"
                      [disabled]="searching"
                    >
                      <span class="spinner-border spinner-border-sm me-2" *ngIf="searching"></span>
                      <i class="fas fa-search me-2" *ngIf="!searching"></i>
                      {{ searching ? 'Searching...' : 'Search Parking' }}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <app-loading *ngIf="searching && !errorMessage" message="Searching for parking lots..."></app-loading>

      <!-- Error Message -->
      <div class="alert alert-danger alert-dismissible fade show" *ngIf="errorMessage" role="alert">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Search Error:</strong> {{ errorMessage }}
        <button type="button" class="btn-close" (click)="clearError()" aria-label="Close"></button>
      </div>

      <!-- Search Results -->
      <div class="row" *ngIf="searchResults.length > 0 && !searching">
        <div class="col-12 mb-3">
          <h3>Found {{ searchResults.length }} parking lot(s)</h3>
        </div>
        
        <div class="col-md-6 col-lg-4 mb-4" *ngFor="let lot of searchResults">
          <div class="card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="card-title">{{ lot.name }}</h5>
                <span class="badge bg-success" *ngIf="lot.is_active">Active</span>
                <span class="badge bg-secondary" *ngIf="!lot.is_active">Inactive</span>
              </div>
              
              <p class="card-text">
                <i class="fas fa-map-marker-alt text-primary me-1"></i>
                {{ lot.address }}
              </p>

              <div class="row mb-2">
                <div class="col-6">
                  <small class="text-muted">Car Slots:</small>
                  <div class="fw-bold" [class.text-success]="lot.available_car_slots !== undefined">
                    <span *ngIf="lot.available_car_slots !== undefined">
                      {{ lot.available_car_slots }} available
                    </span>
                    <span *ngIf="lot.available_car_slots === undefined">
                      {{ lot.total_car_slots }} total
                    </span>
                  </div>
                </div>
                <div class="col-6">
                  <small class="text-muted">Bike Slots:</small>
                  <div class="fw-bold" [class.text-success]="lot.available_bike_slots !== undefined">
                    <span *ngIf="lot.available_bike_slots !== undefined">
                      {{ lot.available_bike_slots }} available
                    </span>
                    <span *ngIf="lot.available_bike_slots === undefined">
                      {{ lot.total_bike_slots }} total
                    </span>
                  </div>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-6">
                  <small class="text-muted">Car Rate:</small>
                  <div class="fw-bold">\${{ lot.hourly_rate_car }}/hr</div>
                </div>
                <div class="col-6">
                  <small class="text-muted">Bike Rate:</small>
                  <div class="fw-bold">\${{ lot.hourly_rate_bike }}/hr</div>
                </div>
              </div>

              <!-- Dynamic Pricing Strategy -->
              <div class="mb-3" *ngIf="getPricingInfo(lot)">
                <div class="card bg-light">
                  <div class="card-body py-2">
                    <h6 class="card-title mb-2">
                      <i class="fas fa-tags me-1"></i>
                      Dynamic Pricing for Your Search
                    </h6>
                    <div class="row">
                      <div class="col-6">
                        <small class="text-muted">Your Rate:</small>
                        <div class="fw-bold text-success">
                          \${{ getPricingInfo(lot)?.average_rate?.toFixed(2) }}/hr
                        </div>
                      </div>
                      <div class="col-6">
                        <small class="text-muted">Total Cost:</small>
                        <div class="fw-bold text-primary">
                          \${{ getPricingInfo(lot)?.total_amount?.toFixed(2) }}
                        </div>
                      </div>
                    </div>
                    <div class="mt-2" *ngIf="getPricingInfo(lot)?.pricing_breakdown?.length > 0">
                      <small class="text-muted">Pricing Rules Applied:</small>
                      <div *ngFor="let rule of getPricingInfo(lot)?.pricing_breakdown" class="small">
                        <span class="badge bg-info me-1">{{ rule.rule_name || 'Standard Rate' }}</span>
                        <span *ngIf="rule.multiplier">({{ rule.multiplier }}x)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Distance -->
              <div class="mb-3" *ngIf="userLocation && lot.latitude && lot.longitude">
                <small class="text-muted">
                  <i class="fas fa-route me-1"></i>
                  {{ calculateDistance(userLocation.latitude, userLocation.longitude, lot.latitude, lot.longitude).toFixed(1) }} km away
                </small>
              </div>
            </div>
            
            <div class="card-footer">
              <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button
                  class="btn btn-outline-primary btn-sm me-md-2"
                  (click)="viewLotDetails(lot.id)"
                >
                  View Details
                </button>
                <button
                  class="btn btn-primary btn-sm"
                  (click)="bookParkingLot(lot)"
                  [disabled]="!lot.is_active"
                >
                  Book Now
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- No Results -->
      <div class="row" *ngIf="searchResults.length === 0 && !searching && hasSearched">
        <div class="col-12">
          <div class="text-center py-5">
            <i class="fas fa-search fa-3x text-muted mb-3"></i>
            <h4>No parking lots found</h4>
            <p class="text-muted">Try adjusting your search criteria or expanding the search radius.</p>
            <button class="btn btn-primary" (click)="resetSearch()">
              Clear Search
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
      70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
      100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
    
    @media (max-width: 768px) {
      .form-select-lg-mobile {
        font-size: 1.1rem;
        padding: 0.75rem 1rem;
        min-height: 48px;
      }
      
      .form-label {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
      }
      
      .btn {
        min-height: 48px;
        font-size: 1rem;
      }
    }
  `]
})
export class ParkingSearchComponent implements OnInit, OnDestroy {
  searchForm: FormGroup;
  searchResults: ParkingLot[] = [];
  userLocation: { latitude: number; longitude: number } | null = null;
  searching = false;
  gettingLocation = false;
  hasSearched = false;
  errorMessage = '';
  searchFormCollapsed = false;
  
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private parkingService: ParkingService,
    private bookingService: BookingService,
    private router: Router
  ) {
    this.searchForm = this.createSearchForm();
  }

  ngOnInit(): void {
    this.initializeForm();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createSearchForm(): FormGroup {
    const now = new Date();
    const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000);

    return this.fb.group({
      vehicleType: ['', Validators.required],
      location: [''],
      startTime: [this.formatDateTimeLocal(now), Validators.required],
      endTime: [this.formatDateTimeLocal(oneHourLater), Validators.required],
      radius: [10],
      sortBy: ['distance']
    });
  }

  private initializeForm(): void {
    // Auto-detect user location on component load
    this.getCurrentLocation();
  }

  getCurrentLocation(): void {
    this.gettingLocation = true;
    this.parkingService.getCurrentLocation()
      .then(position => {
        this.userLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        this.searchForm.patchValue({
          location: `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`
        });
        this.gettingLocation = false;
      })
      .catch(error => {
        console.error('Error getting location:', error);
        this.gettingLocation = false;
      });
  }

  onSearch(): void {
    // Check if vehicle type is selected first
    if (!this.searchForm.get('vehicleType')?.value) {
      this.errorMessage = '⚠️ Vehicle Type Required: Please select your vehicle type first to see accurate parking rates and availability for your specific vehicle.';
      this.markFormGroupTouched();
      
      // Scroll to vehicle type field and focus it
      setTimeout(() => {
        const vehicleTypeElement = document.getElementById('vehicleType');
        if (vehicleTypeElement) {
          vehicleTypeElement.focus();
          vehicleTypeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
      
      return;
    }
    
    if (this.searchForm.valid) {
      this.searching = true;
      this.errorMessage = '';
      this.hasSearched = true;

      // For now, just get all parking lots since we don't have location search implemented
      this.parkingService.getParkingLots({ is_active: true, limit: 50 })
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (lots) => {
            // Enhance each lot with availability and pricing data
            this.enhanceLotsWithRealTimeData(lots);
          },
          error: (error) => {
            this.errorMessage = error.message || 'Failed to search parking lots';
            this.searching = false;
          }
        });
    } else {
      this.markFormGroupTouched();
    }
  }

  calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    return this.parkingService.calculateDistance(lat1, lon1, lat2, lon2);
  }

  viewLotDetails(lotId: string): void {
    this.router.navigate(['/parking', lotId]);
  }

  bookParkingLot(lot: ParkingLot): void {
    const queryParams = {
      lotId: lot.id,
      vehicleType: this.searchForm.get('vehicleType')?.value,
      startTime: this.searchForm.get('startTime')?.value,
      endTime: this.searchForm.get('endTime')?.value
    };
    
    this.router.navigate(['/booking'], { queryParams });
  }

  resetSearch(): void {
    this.searchResults = [];
    this.hasSearched = false;
    this.errorMessage = '';
    this.searchForm.reset();
    this.initializeForm();
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.searchForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markFormGroupTouched(): void {
    Object.keys(this.searchForm.controls).forEach(key => {
      const control = this.searchForm.get(key);
      control?.markAsTouched();
    });
  }

  toggleSearchForm(): void {
    this.searchFormCollapsed = !this.searchFormCollapsed;
  }

  onVehicleTypeChange(): void {
    // Clear error message when vehicle type is selected
    if (this.searchForm.get('vehicleType')?.value) {
      this.errorMessage = '';
    }
  }

  clearError(): void {
    this.errorMessage = '';
  }

  private formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  private enhanceLotsWithRealTimeData(lots: ParkingLot[]): void {
    const formValue = this.searchForm.value;
    const vehicleType = formValue.vehicleType;
    const startTime = formValue.startTime;
    const endTime = formValue.endTime;

    if (!vehicleType || !startTime || !endTime) {
      // If no time/vehicle selected, just show lots without enhancement
      this.searchResults = lots;
      this.searching = false;
      if (lots.length > 0) {
        this.searchFormCollapsed = true;
      }
      return;
    }

    // Convert form times to ISO format
    const startISO = new Date(startTime).toISOString();
    const endISO = new Date(endTime).toISOString();

    let processedCount = 0;
    const enhancedLots = [...lots];

    lots.forEach((lot, index) => {
      // Get both availability and pricing data
      const availabilityCall = this.parkingService.checkAvailability(lot.id, vehicleType, startISO, endISO);
      const pricingCall = this.bookingService.getPricingPreview({
        lot_id: lot.id,
        vehicle_type: vehicleType,
        start_time: startISO,
        end_time: endISO
      });

      // Combine both calls
      availabilityCall.pipe(takeUntil(this.destroy$)).subscribe({
        next: (availability) => {
          // Update lot with availability data
          if (vehicleType === 'car') {
            enhancedLots[index].available_car_slots = availability.available_slots;
          } else {
            enhancedLots[index].available_bike_slots = availability.available_slots;
          }
          
          // Also get pricing data
          pricingCall.pipe(takeUntil(this.destroy$)).subscribe({
            next: (pricing) => {
              // Add pricing strategy info to lot
              (enhancedLots[index] as any).pricingInfo = pricing;
              
              processedCount++;
              if (processedCount === lots.length) {
                this.finishEnhancement(enhancedLots);
              }
            },
            error: () => {
              processedCount++;
              if (processedCount === lots.length) {
                this.finishEnhancement(enhancedLots);
              }
            }
          });
        },
        error: () => {
          processedCount++;
          if (processedCount === lots.length) {
            this.finishEnhancement(enhancedLots);
          }
        }
      });
    });
  }

  private finishEnhancement(lots: ParkingLot[]): void {
    this.searchResults = lots;
    this.searching = false;
    // Auto-collapse search form after successful search
    if (lots.length > 0) {
      this.searchFormCollapsed = true;
    }
  }

  getPricingInfo(lot: ParkingLot): any {
    return (lot as any).pricingInfo || null;
  }
}