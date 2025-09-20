import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { BookingService } from '../services/booking.service';
import { ParkingService } from '../../parking/services/parking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { HybridDurationPickerComponent } from './hybrid-duration-picker.component';
import { DemandIndicatorComponent } from '../../../shared/components/demand-indicator.component';
import { ParkingLot } from '../../../core/models/parking.model';
import { PricingPreviewResponse, Booking } from '../../../core/models/booking.model';
import { DurationSelection, DurationTier } from '../../../core/models/duration.model';
import { 
  nowIST,
  toBackendDate,
  toDatetimeLocalIST,
  parseBackendDate,
  fromDatetimeLocalToUTC
} from '../../../core/utils/timezone.util';

@Component({
  selector: 'app-booking-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LoadingComponent, HybridDurationPickerComponent, DemandIndicatorComponent],
  template: `
    <div class="container mt-4">
      <div class="row">
        <div class="col-12">
          <h1 class="h2 mb-4">
            <i class="fas fa-ticket-alt me-2"></i>
            Book Parking Space
          </h1>
        </div>
      </div>

      <app-loading *ngIf="loading" message="Loading booking information..."></app-loading>

      <div *ngIf="!loading">
        <!-- Parking Lot Information -->
        <div class="row mb-4" *ngIf="selectedLot">
          <div class="col-12">
            <div class="card border-primary">
              <div class="card-header bg-primary text-white">
                <div class="d-flex justify-content-between align-items-center">
                  <h5 class="mb-0">
                    <i class="fas fa-map-marker-alt me-2"></i>
                    {{ selectedLot.name }}
                  </h5>
                  <app-demand-indicator 
                    [lotId]="selectedLot.id"
                    [config]="{
                      style: 'badge',
                      size: 'medium',
                      showPercentage: true,
                      showTrend: true,
                      showRecommendation: false,
                      showFactors: false,
                      autoRefresh: true,
                      refreshInterval: 30
                    }">
                  </app-demand-indicator>
                </div>
              </div>
              <div class="card-body">
                <p class="card-text">
                  <i class="fas fa-location-arrow me-2"></i>
                  {{ selectedLot.address }}
                </p>
                <div class="row">
                  <div class="col-md-6">
                    <small class="text-muted">Available Slots:</small>
                    <div class="fw-bold">
                      Cars: {{ selectedLot.total_car_slots }} | 
                      Bikes: {{ selectedLot.total_bike_slots }}
                    </div>
                  </div>
                  <div class="col-md-6">
                    <small class="text-muted">Hourly Rates:</small>
                    <div class="fw-bold">
                      Cars: \${{ selectedLot.hourly_rate_car }}/hr | 
                      Bikes: \${{ selectedLot.hourly_rate_bike }}/hr
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Booking Form -->
        <div class="row">
          <div class="col-lg-8">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">Booking Details</h5>
              </div>
              <div class="card-body">
                <form [formGroup]="bookingForm" (ngSubmit)="onSubmit()">
                  <!-- Compact Single Row Layout -->
                  <div class="row">
                    <div class="col-lg-3 col-md-4 col-sm-6 mb-3">
                      <label for="vehicleType" class="form-label">Vehicle Type</label>
                      <select
                        class="form-select"
                        id="vehicleType"
                        formControlName="vehicleType"
                        [class.is-invalid]="isFieldInvalid('vehicleType')"
                        (change)="onVehicleTypeChange()"
                      >
                        <option value="">Select type</option>
                        <option value="car">Car</option>
                        <option value="bike">Bike/Motorcycle</option>
                        <option value="truck">Truck</option>
                        <option value="electric_car">Electric Car</option>
                        <option value="electric_bike">Electric Bike</option>
                      </select>
                      <div class="invalid-feedback" *ngIf="isFieldInvalid('vehicleType')">
                        Please select a vehicle type
                      </div>
                    </div>

                    <div class="col-lg-4 col-md-4 col-sm-6 mb-3">
                      <label for="vehicleNumber" class="form-label">Vehicle Number</label>
                      <input
                        type="text"
                        class="form-control"
                        id="vehicleNumber"
                        formControlName="vehicleNumber"
                        [class.is-invalid]="isFieldInvalid('vehicleNumber')"
                        placeholder="Enter vehicle number"
                        style="text-transform: uppercase;"
                      />
                      <div class="invalid-feedback" *ngIf="isFieldInvalid('vehicleNumber')">
                        <div *ngIf="bookingForm.get('vehicleNumber')?.errors?.['required']">
                          Vehicle number is required
                        </div>
                        <div *ngIf="bookingForm.get('vehicleNumber')?.errors?.['minlength']">
                          Vehicle number must be at least 3 characters
                        </div>
                      </div>
                    </div>

                    <div class="col-lg-5 col-md-4 col-sm-12 mb-3">
                      <label for="startTime" class="form-label">
                        Start Time <small class="text-muted">(IST)</small>
                      </label>
                      <input
                        type="datetime-local"
                        class="form-control"
                        id="startTime"
                        formControlName="startTime"
                        [class.is-invalid]="isFieldInvalid('startTime')"
                        [min]="minStartTime"
                        (change)="onTimeChange()"
                      />
                      <div class="invalid-feedback" *ngIf="isFieldInvalid('startTime')">
                        Please select a start time
                      </div>
                    </div>
                  </div>


                  <!-- Duration Selection -->
                  <div class="row" *ngIf="selectedLot && bookingForm.get('vehicleType')?.value">
                    <div class="col-12 mb-3">
                      <label class="form-label">
                        <i class="fas fa-clock me-2"></i>
                        Select Parking Duration
                      </label>
                      <app-hybrid-duration-picker
                        [lotId]="selectedLot.id"
                        [vehicleType]="bookingForm.get('vehicleType')?.value"
                        [startTime]="bookingForm.get('startTime')?.value"
                        [config]="{
                          showTierLabels: true,
                          showBufferTime: true,
                          showDemandIndicator: false,
                          enableQuickSelect: true,
                          enableCustomDuration: true,
                          defaultTier: DurationTier.SHORT,
                          maxDuration: 240,
                          minDuration: 15
                        }"
                        (durationSelected)="onDurationSelected($event)"
                        (validationChanged)="onDurationValidationChanged($event)">
                      </app-hybrid-duration-picker>
                      <div class="form-text">
                        Select your parking duration. Our smart system will automatically assign the best available slot.
                      </div>
                    </div>
                  </div>

                  <div class="alert alert-danger" *ngIf="errorMessage">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    {{ errorMessage }}
                  </div>

                  <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                    <button
                      type="button"
                      class="btn btn-outline-secondary"
                      (click)="goBack()"
                    >
                      <i class="fas fa-arrow-left me-2"></i>
                      Back to Search
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- Pricing Summary -->
          <div class="col-lg-4">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <i class="fas fa-calculator me-2"></i>
                  Pricing Summary
                </h5>
              </div>
              <div class="card-body">
                <div *ngIf="loadingPrice" class="text-center py-3">
                  <div class="spinner-border spinner-border-sm text-primary"></div>
                  <p class="mt-2 mb-0">Calculating price...</p>
                </div>

                <div *ngIf="pricingPreview && !loadingPrice && selectedDuration">
                  <div class="mb-3">
                    <div class="d-flex justify-content-between mb-2">
                      <span>Duration:</span>
                      <span class="fw-bold">{{ formatDurationDisplay(pricingPreview.duration_hours) }}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2" *ngIf="pricingPreview">
                      <span>Average Rate:</span>
                      <span class="fw-bold">\${{ pricingPreview.average_rate.toFixed(2) }}/hr</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                      <span>Vehicle Type:</span>
                      <span class="fw-bold text-capitalize">{{ pricingPreview.vehicle_type }}</span>
                    </div>
                  </div>

                  <hr>

                  <!-- Pricing Breakdown -->
                  <div class="mb-3" *ngIf="pricingPreview && pricingPreview.pricing_breakdown.length > 0">
                    <h6 class="mb-2">Pricing Breakdown:</h6>
                    <div *ngFor="let item of pricingPreview.pricing_breakdown" class="small mb-2">
                      <div class="d-flex justify-content-between">
                        <span>{{ item.rule_name }}</span>
                        <span>\${{ item.amount.toFixed(2) }}</span>
                      </div>
                      <div class="text-muted">
                        {{ formatDurationDisplay(item.duration_hours) }} × \${{ item.rate_per_hour.toFixed(2) }}/hr
                        <span *ngIf="item.multiplier && item.multiplier !== 1">
                          × {{ item.multiplier }}
                        </span>
                      </div>
                    </div>
                    <hr>
                  </div>

                  <div class="d-flex justify-content-between fs-5 fw-bold text-primary">
                    <span>Total Amount:</span>
                    <span>\${{ pricingPreview.total_amount.toFixed(2) }}</span>
                  </div>

                  <div class="mt-3 p-2 bg-light rounded">
                    <small class="text-muted">
                      <i class="fas fa-info-circle me-1"></i>
                      Price includes all applicable taxes and fees
                    </small>
                  </div>
                </div>

                <div *ngIf="!selectedDuration && !loadingPrice" class="text-center py-3">
                  <div class="alert alert-info mb-0">
                    <i class="fas fa-clock me-2"></i>
                    <strong>Select a parking duration</strong> to see pricing details
                  </div>
                </div>
                
                <div *ngIf="selectedDuration && !pricingPreview && !loadingPrice" class="text-center py-3">
                  <div class="alert alert-warning mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Unable to calculate pricing. Please try again.
                  </div>
                </div>
              </div>
              
              <!-- Payment Button -->
              <div class="card-footer">
                <div class="d-grid">
                  <button
                    type="submit"
                    class="btn btn-primary btn-lg"
                    [disabled]="bookingForm.invalid || submitting"
                    (click)="onSubmit()"
                  >
                    <span class="spinner-border spinner-border-sm me-2" *ngIf="submitting"></span>
                    <i class="fas fa-credit-card me-2" *ngIf="!submitting"></i>
                    {{ submitting ? 'Processing...' : 'Proceed to Payment' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Booking Terms -->
            <div class="card mt-3">
              <div class="card-header">
                <h6 class="mb-0">
                  <i class="fas fa-file-contract me-2"></i>
                  Booking Terms
                </h6>
              </div>
              <div class="card-body">
                <ul class="list-unstyled small mb-0">
                  <li class="mb-2">
                    <i class="fas fa-clock text-warning me-2"></i>
                    Free cancellation up to 2 hours before start time
                  </li>
                  <li class="mb-2">
                    <i class="fas fa-shield-alt text-success me-2"></i>
                    Your parking spot is guaranteed once booked
                  </li>
                  <li class="mb-2">
                    <i class="fas fa-mobile-alt text-info me-2"></i>
                    QR code access for easy entry/exit
                  </li>
                  <li>
                    <i class="fas fa-headset text-primary me-2"></i>
                    24/7 customer support available
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>


    </div>
  `
})
export class BookingFormComponent implements OnInit, OnDestroy {
  bookingForm: FormGroup;
  selectedLot: ParkingLot | null = null;
  pricingPreview: PricingPreviewResponse | null = null;
  loading = true;
  loadingPrice = false;
  submitting = false;
  errorMessage = '';
  
  // Duration-based booking properties
  selectedDuration: DurationSelection | null = null;
  isDurationValid = false;
  
  // Make enum accessible in template
  DurationTier = DurationTier;

  /**
   * Format duration in hours to "X hour Y minutes" format
   */
  formatDurationDisplay(hours: number): string {
    const totalMinutes = Math.round(hours * 60);
    const hoursPart = Math.floor(totalMinutes / 60);
    const minutesPart = totalMinutes % 60;
    
    if (hoursPart === 0) {
      return `${minutesPart} minutes`;
    } else if (minutesPart === 0) {
      return `${hoursPart} hour${hoursPart > 1 ? 's' : ''}`;
    } else {
      return `${hoursPart} hour${hoursPart > 1 ? 's' : ''} ${minutesPart} minutes`;
    }
  }
  
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private bookingService: BookingService,
    private parkingService: ParkingService,
    private router: Router,
    private route: ActivatedRoute,
    private location: Location
  ) {
    this.bookingForm = this.createBookingForm();
  }

  ngOnInit(): void {
    this.loadBookingData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createBookingForm(): FormGroup {
    // Set default times in IST: start time = current IST time + 30 minutes, end time = start + 2 hours
    const now = nowIST();
    const startTime = new Date(now.getTime() + 30 * 60 * 1000); // +30 minutes (buffer for future time)
    const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000); // +2 hours from start
    
    return this.fb.group({
      vehicleType: ['', Validators.required],
      vehicleNumber: ['', [Validators.required, Validators.minLength(3)]],
      startTime: [toDatetimeLocalIST(startTime), Validators.required]
    });
  }

  private formatDatetimeLocal(date: Date): string {
    // Use IST timezone utility instead of manual formatting
    return toDatetimeLocalIST(date);
  }

  get minStartTime(): string {
    const now = nowIST();
    return this.formatDatetimeLocal(now);
  }

  get minEndTime(): string {
    const startTimeValue = this.bookingForm.get('startTime')?.value;
    if (startTimeValue) {
      const startTime = new Date(startTimeValue);
      return this.formatDatetimeLocal(new Date(startTime.getTime() + 30 * 60 * 1000)); // +30 min minimum duration
    }
    const now = nowIST();
    return this.formatDatetimeLocal(new Date(now.getTime() + 30 * 60 * 1000));
  }

  private loadBookingData(): void {
    const queryParams = this.route.snapshot.queryParams;
    
    if (queryParams['lotId']) {
      // Load parking lot details
      this.parkingService.getParkingLot(queryParams['lotId'])
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (lot) => {
            this.selectedLot = lot;
            
            // No need to pre-select slots - backend will handle optimal allocation
            console.log('Parking lot loaded successfully:', lot.name);
            
            this.prefillForm(queryParams);
            this.loading = false;
          },
          error: (error) => {
            this.errorMessage = 'Failed to load parking lot details';
            this.loading = false;
          }
        });
    } else {
      this.errorMessage = 'No parking lot selected';
      this.loading = false;
    }
  }

  private prefillForm(queryParams: any): void {
    const formData: any = {};
    
    if (queryParams['vehicleType']) {
      formData.vehicleType = queryParams['vehicleType'];
    }
    
    if (queryParams['startTime']) {
      // Validate that the query param time is still in the future
      const queryStartTime = new Date(queryParams['startTime']);
      const now = nowIST();
      const minStartTime = new Date(now.getTime() + 30 * 60 * 1000); // 30 minutes from now
      
      if (queryStartTime < minStartTime) {
        console.log('⚠️ Query param start time is in past, using default future time');
        formData.startTime = toDatetimeLocalIST(minStartTime);
        // Also update end time to maintain duration
        if (queryParams['endTime']) {
          const originalDuration = new Date(queryParams['endTime']).getTime() - queryStartTime.getTime();
          const newEndTime = new Date(minStartTime.getTime() + Math.max(originalDuration, 60 * 60 * 1000)); // At least 1 hour
          formData.endTime = toDatetimeLocalIST(newEndTime);
        }
      } else {
        formData.startTime = queryParams['startTime'];
        if (queryParams['endTime']) {
          formData.endTime = queryParams['endTime'];
        }
      }
    }

    this.bookingForm.patchValue(formData);
    
    // Trigger pricing calculation if form is valid
    if (this.bookingForm.valid) {
      this.calculatePricing();
    }
  }

  onVehicleTypeChange(): void {
    this.calculatePricing();
  }

  onTimeChange(): void {
    this.calculatePricing();
  }

  // ===== DURATION-BASED BOOKING METHODS =====
  
  onDurationSelected(duration: DurationSelection): void {
    this.selectedDuration = duration;
    
    if (duration.isValid) {
      // Calculate end time based on start time and duration
      const startTime = this.bookingForm.get('startTime')?.value;
      if (startTime) {
        const startDate = new Date(startTime);
        const endDate = new Date(startDate.getTime() + (duration.duration * 60 * 1000));
        
        this.bookingForm.patchValue({
          endTime: this.toDateTimeLocal(endDate)
        });
        
        // Recalculate pricing with new duration
        this.calculatePricing();
      }
    }
  }
  
  onDurationValidationChanged(isValid: boolean): void {
    this.isDurationValid = isValid;
  }
  
  private toDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  private calculatePricing(): void {
    if (this.bookingForm.valid && this.selectedLot) {
      this.loadingPrice = true;
      
      const formValue = this.bookingForm.value;
      
      // Calculate end time from start time + selected duration
      if (!this.selectedDuration) {
        console.log('⚠️ No duration selected, skipping pricing calculation');
        this.loadingPrice = false;
        return;
      }
      
      const durationMinutes = this.selectedDuration.duration;
      
      // CORRECT APPROACH: Convert start time to UTC first, then add duration
      const convertedStartTime = fromDatetimeLocalToUTC(formValue.startTime);
      const startTimeUTC = new Date(convertedStartTime);
      const endTimeUTC = new Date(startTimeUTC.getTime() + durationMinutes * 60 * 1000);
      const convertedEndTime = endTimeUTC.toISOString();
      
      // Debug: Log form values
      console.log('🔍 Booking form pricing calculation:');
      console.log('  Form startTime (IST):', formValue.startTime);
      console.log('  Duration:', durationMinutes, 'minutes');
      console.log('  Start Time UTC:', startTimeUTC);
      console.log('  End Time UTC:', endTimeUTC);
      console.log('  Duration in UTC hours:', (endTimeUTC.getTime() - startTimeUTC.getTime()) / (1000 * 60 * 60));
      
      console.log('  Converted startTime (UTC):', convertedStartTime);
      console.log('  Converted endTime (UTC):', convertedEndTime);
      
      // Validate that times are in the future
      const now = new Date();
      if (startTimeUTC <= now) {
        console.error('❌ Start time is in the past, cannot calculate pricing');
        this.loadingPrice = false;
        return;
      }
      
      if (endTimeUTC <= startTimeUTC) {
        console.error('❌ End time must be after start time');
        this.loadingPrice = false;
        return;
      }
      
      const pricingRequest = {
        lot_id: this.selectedLot.id,
        vehicle_type: formValue.vehicleType,
        start_time: convertedStartTime,  // IST datetime-local → UTC
        end_time: convertedEndTime       // IST datetime-local → UTC
      };
      
      console.log('📤 Booking form pricing request:', pricingRequest);
      console.log('  🕐 Start time (UTC):', convertedStartTime);
      console.log('  🕐 End time (UTC):', convertedEndTime);
      console.log('  🚗 Vehicle type:', formValue.vehicleType);
      console.log('  ⏱️  Duration hours:', durationMinutes / 60);

      this.bookingService.getPricingPreview(pricingRequest)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (pricing) => {
            console.log('✅ Pricing response received:', pricing);
            console.log('  💰 Total amount:', pricing.total_amount);
            console.log('  📊 Breakdown items:', pricing.pricing_breakdown?.length || 0);
            if (pricing.pricing_breakdown?.length > 0) {
              console.log('  📋 Rules applied:', pricing.pricing_breakdown.map(b => `${b.rule_name}: $${b.rate_per_hour}/hr × ${b.multiplier || 1}`));
            }
            this.pricingPreview = pricing;
            this.loadingPrice = false;
          },
          error: (error) => {
            console.error('❌ Booking form pricing error:', error);
            console.error('   Request data was:', pricingRequest);
            console.error('   Error details:', error.error);
            this.loadingPrice = false;
          }
        });
    }
  }

  onSubmit(): void {
    // Clear any previous error messages
    this.errorMessage = '';
    
    // Validation checks with user-friendly messages
    if (!this.selectedDuration) {
      this.errorMessage = 'Please select a parking duration before proceeding to payment.';
      return;
    }
    
    if (!this.pricingPreview) {
      this.errorMessage = 'Unable to calculate pricing. Please select a duration and try again.';
      return;
    }
    
    if ((this.pricingPreview.total_amount || 0) <= 0) {
      this.errorMessage = 'Invalid pricing calculated ($0.00). Please select a different duration or contact support.';
      return;
    }
    
    if (!this.isDurationValid) {
      this.errorMessage = 'Selected duration is not valid. Please choose a different duration.';
      return;
    }
    
    if (this.bookingForm.valid && this.selectedLot && this.selectedDuration && this.isDurationValid) {
      this.submitting = true;
      
      console.log('🔄 Starting duration-based payment flow...');
      console.log('- Selected duration:', this.selectedDuration.duration, 'minutes');
      console.log('- Duration tier:', this.selectedDuration.tier);
      console.log('- Lot:', this.selectedLot.name);
      console.log('- Vehicle:', this.bookingForm.value.vehicleType);
      console.log('- Form valid:', this.bookingForm.valid);
      console.log('- Form value:', this.bookingForm.value);
      
      // Create booking reservation with duration-based approach
      // Calculate end time from start time + duration
      const startTime = new Date(this.bookingForm.value.startTime);
      const endTime = new Date(startTime.getTime() + this.selectedDuration!.duration * 60 * 1000);
      
      const bookingRequest = {
        lot_id: this.selectedLot!.id,
        vehicle_type: this.bookingForm.value.vehicleType,
        vehicle_number: this.bookingForm.value.vehicleNumber,
        start_time: fromDatetimeLocalToUTC(this.bookingForm.value.startTime),
        end_time: fromDatetimeLocalToUTC(endTime.toISOString().slice(0, 16)), // Convert to datetime-local format
        duration_minutes: this.selectedDuration!.duration,
        duration_tier: this.selectedDuration!.tier
      };
      
      // TODO: When backend supports duration-based reservations, replace this with proper reservation API
      // For now, simulate a reservation by generating a session ID
      const mockReservation = {
        success: true,
        session_id: 'duration_' + Date.now() + '_' + Math.random().toString(36).substring(7),
        expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString() // 10 minutes from now
      };
      
      // Simulate async call with setTimeout
      setTimeout(() => {
        this.submitting = false;
        const reservation = mockReservation;
        
        if (reservation.success) {
          console.log('✅ Duration reservation successful:', reservation.session_id);
          
          // Navigate to payment page with reservation session ID and booking details
          const navigationExtras = {
            queryParams: {
              sessionId: reservation.session_id,
              lotId: this.selectedLot!.id,
              lotName: this.selectedLot!.name,
              vehicleType: this.bookingForm.value.vehicleType,
              vehicleNumber: this.bookingForm.value.vehicleNumber.toUpperCase(),
              duration: this.selectedDuration?.duration || 0,
              durationTier: this.selectedDuration?.tier || 'short',
              totalAmount: this.pricingPreview?.total_amount || 0,
              expiresAt: reservation.expires_at  // UTC timestamp from backend
            }
          };
          
          this.router.navigate(['/payment'], navigationExtras);
        } else {
          console.error('❌ Duration reservation failed');
          this.errorMessage = 'Failed to reserve parking slot. Please try again.';
        }
      }, 1000); // 1 second delay to simulate API call
    } else {
      this.markFormGroupTouched();
      
      if (!this.selectedDuration || !this.isDurationValid) {
        this.errorMessage = 'Please select a valid parking duration to continue.';
      }
    }
  }

  goBack(): void {
    // Use browser back to preserve search results and form state
    this.location.back();
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.bookingForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  private markFormGroupTouched(): void {
    Object.keys(this.bookingForm.controls).forEach(key => {
      const control = this.bookingForm.get(key);
      control?.markAsTouched();
    });
  }

  formatDateTime(dateTime: string): string {
    return new Date(dateTime).toLocaleString();
  }
}