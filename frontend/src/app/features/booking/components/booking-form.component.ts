import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, takeUntil, forkJoin } from 'rxjs';
import { BookingService } from '../services/booking.service';
import { ParkingService } from '../../parking/services/parking.service';
import { LoadingComponent } from '../../../shared/components/loading.component';
import { ChunkSelectorComponent } from './chunk-selector.component';
import { ParkingLot } from '../../../core/models/parking.model';
import { PricingPreviewResponse, Booking } from '../../../core/models/booking.model';
import { TimeChunk } from '../../../core/models/slot-chunks.model';

@Component({
  selector: 'app-booking-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, LoadingComponent, ChunkSelectorComponent],
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
                <h5 class="mb-0">
                  <i class="fas fa-map-marker-alt me-2"></i>
                  {{ selectedLot.name }}
                </h5>
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
                  <div class="row">
                    <div class="col-md-6 mb-3">
                      <label for="vehicleType" class="form-label">Vehicle Type</label>
                      <select
                        class="form-select"
                        id="vehicleType"
                        formControlName="vehicleType"
                        [class.is-invalid]="isFieldInvalid('vehicleType')"
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
                    </div>

                    <div class="col-md-6 mb-3">
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
                  </div>

                  <!-- Time Chunk Selection -->
                  <div class="row mb-4" *ngIf="selectedLot && bookingForm.get('vehicleType')?.value">
                    <div class="col-12">
                      <h6 class="mb-3">
                        <i class="fas fa-clock me-2"></i>
                        Select Time Slots (30-minute chunks)
                      </h6>
                      <app-chunk-selector
                        [slotId]="selectedLot.id"
                        [vehicleType]="bookingForm.get('vehicleType')?.value"
                        (chunksSelected)="onChunksSelected($event)"
                        (timeRangeChanged)="onTimeRangeChanged($event)"
                      ></app-chunk-selector>
                      
                      <!-- Info -->
                      <div class="mt-2 p-2 bg-light small text-muted" *ngIf="selectedLot">
                        <i class="fas fa-info-circle me-1"></i>
                        Showing time slots for <strong>{{ selectedLot.name }}</strong> - 
                        <span class="text-success">{{ (bookingForm.get('vehicleType')?.value | titlecase) || 'Select vehicle type' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Time Range Display (for form validation) -->
                  <div class="row" style="display: none;">
                    <div class="col-md-6 mb-3">
                      <input
                        type="datetime-local"
                        class="form-control"
                        id="startTime"
                        formControlName="startTime"
                      />
                    </div>
                    <div class="col-md-6 mb-3">
                      <input
                        type="datetime-local"
                        class="form-control"
                        id="endTime"
                        formControlName="endTime"
                      />
                    </div>
                  </div>

                  <div class="alert alert-danger" *ngIf="errorMessage">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    {{ errorMessage }}
                  </div>

                  <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                    <button
                      type="button"
                      class="btn btn-outline-secondary me-md-2"
                      (click)="goBack()"
                    >
                      <i class="fas fa-arrow-left me-2"></i>
                      Back to Search
                    </button>
                    <button
                      type="submit"
                      class="btn btn-primary"
                      [disabled]="bookingForm.invalid || submitting || !pricingPreview"
                    >
                      <span class="spinner-border spinner-border-sm me-2" *ngIf="submitting"></span>
                      <i class="fas fa-credit-card me-2" *ngIf="!submitting"></i>
                      {{ submitting ? 'Processing...' : 'Proceed to Payment' }}
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

                <div *ngIf="pricingPreview && !loadingPrice">
                  <div class="mb-3">
                    <div class="d-flex justify-content-between mb-2">
                      <span>Duration:</span>
                      <span class="fw-bold">{{ pricingPreview.duration_hours.toFixed(1) }} hours</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
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
                  <div class="mb-3" *ngIf="pricingPreview.pricing_breakdown.length > 0">
                    <h6 class="mb-2">Pricing Breakdown:</h6>
                    <div *ngFor="let item of pricingPreview.pricing_breakdown" class="small mb-2">
                      <div class="d-flex justify-content-between">
                        <span>{{ item.rule_name }}</span>
                        <span>\${{ item.amount.toFixed(2) }}</span>
                      </div>
                      <div class="text-muted">
                        {{ item.duration_hours.toFixed(1) }}h × \${{ item.rate_per_hour.toFixed(2) }}/hr
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

                <div *ngIf="!pricingPreview && !loadingPrice && bookingForm.valid" class="text-center py-3">
                  <p class="text-muted mb-0">Complete the form to see pricing</p>
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
  
  // Chunk selection properties
  selectedChunks: TimeChunk[] = [];
  chunkSessionId: string | null = null;
  
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private bookingService: BookingService,
    private parkingService: ParkingService,
    private router: Router,
    private route: ActivatedRoute
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
    // Set default times: start time = current time + 1 hour, end time = start + 2 hours
    const now = new Date();
    const startTime = new Date(now.getTime() + 60 * 60 * 1000); // +1 hour
    const endTime = new Date(startTime.getTime() + 60 * 60 * 1000); // +1 hour from start
    
    return this.fb.group({
      vehicleType: ['', Validators.required],
      vehicleNumber: ['', [Validators.required, Validators.minLength(3)]],
      startTime: [this.formatDatetimeLocal(startTime), Validators.required],
      endTime: [this.formatDatetimeLocal(endTime), Validators.required]
    });
  }

  private formatDatetimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  get minStartTime(): string {
    const now = new Date();
    return this.formatDatetimeLocal(now);
  }

  get minEndTime(): string {
    const startTimeValue = this.bookingForm.get('startTime')?.value;
    if (startTimeValue) {
      const startTime = new Date(startTimeValue);
      return this.formatDatetimeLocal(new Date(startTime.getTime() + 30 * 60 * 1000)); // +30 min minimum duration
    }
    const now = new Date();
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
      formData.startTime = queryParams['startTime'];
    }
    
    if (queryParams['endTime']) {
      formData.endTime = queryParams['endTime'];
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

  onChunksSelected(chunks: TimeChunk[]): void {
    this.selectedChunks = chunks;
    console.log('Chunks selected:', chunks);
    
    // Update form with time range from selected chunks
    if (chunks.length > 0) {
      const sortedChunks = [...chunks].sort((a, b) => 
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      );
      
      const startTime = new Date(sortedChunks[0].start_time);
      const endTime = new Date(sortedChunks[sortedChunks.length - 1].end_time);
      
      this.bookingForm.patchValue({
        startTime: this.formatDateTimeLocal(startTime),
        endTime: this.formatDateTimeLocal(endTime)
      });
      
      this.calculatePricing();
    }
  }

  onTimeRangeChanged(event: {startTime: string, endTime: string, sessionId?: string}): void {
    console.log('Time range changed:', event);
    
    if (event.sessionId) {
      this.chunkSessionId = event.sessionId;
    }
    
    // Update form values
    this.bookingForm.patchValue({
      startTime: event.startTime,
      endTime: event.endTime
    });
    
    this.calculatePricing();
  }

  private calculatePricing(): void {
    if (this.bookingForm.valid && this.selectedLot) {
      this.loadingPrice = true;
      
      const formValue = this.bookingForm.value;
      const pricingRequest = {
        lot_id: this.selectedLot.id,
        vehicle_type: formValue.vehicleType,
        start_time: formValue.startTime,
        end_time: formValue.endTime
      };

      this.bookingService.getPricingPreview(pricingRequest)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (pricing) => {
            this.pricingPreview = pricing;
            this.loadingPrice = false;
          },
          error: (error) => {
            console.error('Error calculating pricing:', error);
            this.loadingPrice = false;
          }
        });
    }
  }

  onSubmit(): void {
    if (this.bookingForm.valid && this.selectedLot) {
      this.submitting = true;
      this.errorMessage = '';

      const formValue = this.bookingForm.value;
      
      // Convert datetime-local values to proper ISO format
      // The form inputs are in local time, convert them to ISO strings
      const startDate = new Date(formValue.startTime);
      const endDate = new Date(formValue.endTime);
      
      // Use chunk-based booking if chunks are selected, otherwise use regular booking
      let bookingObservable;
      
      if (this.selectedChunks.length > 0 && this.chunkSessionId) {
        const chunkBookingData = {
          session_id: this.chunkSessionId,
          vehicle_number: formValue.vehicleNumber.toUpperCase()
        };

        bookingObservable = this.bookingService.confirmChunkBooking(chunkBookingData);
      } else {
        const bookingData = {
          lot_id: this.selectedLot.id,
          vehicle_type: formValue.vehicleType,
          vehicle_number: formValue.vehicleNumber.toUpperCase(),
          start_time: startDate.toISOString(),
          end_time: endDate.toISOString()
        };

        bookingObservable = this.bookingService.createBooking(bookingData);
      }

      bookingObservable
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (booking) => {
            this.submitting = false;
            // Navigate to payment page instead of showing inline payment form
            this.router.navigate(['/payment', booking.id]);
          },
          error: (error) => {
            this.errorMessage = error.message || 'Failed to create booking. Please try again.';
            this.submitting = false;
          }
        });
    } else {
      this.markFormGroupTouched();
    }
  }

  goBack(): void {
    this.router.navigate(['/parking']);
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

  private formatDateTimeLocal(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  }
}