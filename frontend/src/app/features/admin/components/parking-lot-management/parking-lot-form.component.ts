import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ParkingLot, CreateLotData, UpdateLotData } from '../../../../core/services/parking-lot.service';

@Component({
  selector: 'app-parking-lot-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="modal fade" [id]="modalId" tabindex="-1" [attr.aria-labelledby]="modalId + 'Label'">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" [id]="modalId + 'Label'">
              <i class="fas" [class]="isEditMode ? 'fa-edit' : 'fa-plus-circle'"></i>
              {{ isEditMode ? 'Edit Parking Lot' : 'Create New Parking Lot' }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" (click)="onCancel()"></button>
          </div>

          <form [formGroup]="lotForm" (ngSubmit)="onSubmit()">
            <div class="modal-body">
              <div class="row">
                <!-- Basic Information -->
                <div class="col-md-6">
                  <h6 class="text-muted mb-3">Basic Information</h6>
                  
                  <div class="mb-3">
                    <label class="form-label required">Parking Lot Name</label>
                    <input 
                      type="text" 
                      class="form-control" 
                      formControlName="name"
                      placeholder="Enter lot name"
                      [class.is-invalid]="isFieldInvalid('name')"
                    >
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('name')">
                      <div *ngIf="lotForm.get('name')?.errors?.['required']">Lot name is required</div>
                      <div *ngIf="lotForm.get('name')?.errors?.['minlength']">Lot name must be at least 2 characters</div>
                    </div>
                  </div>

                  <div class="mb-3">
                    <label class="form-label required">Address</label>
                    <textarea 
                      class="form-control" 
                      formControlName="address"
                      placeholder="Enter full address"
                      rows="3"
                      [class.is-invalid]="isFieldInvalid('address')"
                    ></textarea>
                    <div class="invalid-feedback" *ngIf="isFieldInvalid('address')">
                      <div *ngIf="lotForm.get('address')?.errors?.['required']">Address is required</div>
                    </div>
                  </div>

                  <!-- GPS Coordinates -->
                  <div class="mb-3">
                    <label class="form-label">GPS Coordinates</label>
                    <div class="row">
                      <div class="col-6">
                        <input 
                          type="number" 
                          class="form-control" 
                          formControlName="latitude"
                          placeholder="Latitude"
                          step="0.000001"
                          [class.is-invalid]="isFieldInvalid('latitude')"
                        >
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('latitude')">
                          <div *ngIf="lotForm.get('latitude')?.errors?.['required']">Latitude is required</div>
                          <div *ngIf="lotForm.get('latitude')?.errors?.['min'] || lotForm.get('latitude')?.errors?.['max']">
                            Latitude must be between -90 and 90
                          </div>
                        </div>
                      </div>
                      <div class="col-6">
                        <input 
                          type="number" 
                          class="form-control" 
                          formControlName="longitude"
                          placeholder="Longitude"
                          step="0.000001"
                          [class.is-invalid]="isFieldInvalid('longitude')"
                        >
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('longitude')">
                          <div *ngIf="lotForm.get('longitude')?.errors?.['required']">Longitude is required</div>
                          <div *ngIf="lotForm.get('longitude')?.errors?.['min'] || lotForm.get('longitude')?.errors?.['max']">
                            Longitude must be between -180 and 180
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="form-text">
                      <i class="fas fa-info-circle me-1"></i>
                      You can get coordinates from Google Maps by right-clicking on the location
                    </div>
                  </div>
                </div>

                <!-- Capacity & Pricing -->
                <div class="col-md-6">
                  <h6 class="text-muted mb-3">Capacity & Pricing</h6>
                  
                  <!-- Capacity -->
                  <div class="capacity-section mb-4">
                    <label class="form-label">Slot Capacity</label>
                    <div class="row">
                      <div class="col-6">
                        <div class="input-group">
                          <span class="input-group-text">
                            <i class="fas fa-car text-primary"></i>
                          </span>
                          <input 
                            type="number" 
                            class="form-control" 
                            formControlName="total_car_slots"
                            placeholder="Car slots"
                            min="0"
                            [class.is-invalid]="isFieldInvalid('total_car_slots')"
                          >
                        </div>
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('total_car_slots')">
                          <div *ngIf="lotForm.get('total_car_slots')?.errors?.['required']">Car slots required</div>
                          <div *ngIf="lotForm.get('total_car_slots')?.errors?.['min']">Must be 0 or greater</div>
                        </div>
                        <div class="form-text">Car Slots</div>
                      </div>
                      <div class="col-6">
                        <div class="input-group">
                          <span class="input-group-text">
                            <i class="fas fa-motorcycle text-success"></i>
                          </span>
                          <input 
                            type="number" 
                            class="form-control" 
                            formControlName="total_bike_slots"
                            placeholder="Bike slots"
                            min="0"
                            [class.is-invalid]="isFieldInvalid('total_bike_slots')"
                          >
                        </div>
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('total_bike_slots')">
                          <div *ngIf="lotForm.get('total_bike_slots')?.errors?.['required']">Bike slots required</div>
                          <div *ngIf="lotForm.get('total_bike_slots')?.errors?.['min']">Must be 0 or greater</div>
                        </div>
                        <div class="form-text">Bike Slots</div>
                      </div>
                    </div>
                  </div>

                  <!-- Pricing -->
                  <div class="pricing-section">
                    <label class="form-label">Hourly Rates ($)</label>
                    <div class="row">
                      <div class="col-6">
                        <div class="input-group">
                          <span class="input-group-text">$</span>
                          <input 
                            type="number" 
                            class="form-control" 
                            formControlName="hourly_rate_car"
                            placeholder="Car rate"
                            min="0.01"
                            step="0.01"
                            [class.is-invalid]="isFieldInvalid('hourly_rate_car')"
                          >
                        </div>
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('hourly_rate_car')">
                          <div *ngIf="lotForm.get('hourly_rate_car')?.errors?.['required']">Car rate required</div>
                          <div *ngIf="lotForm.get('hourly_rate_car')?.errors?.['min']">Must be greater than 0</div>
                        </div>
                        <div class="form-text">Per hour for cars</div>
                      </div>
                      <div class="col-6">
                        <div class="input-group">
                          <span class="input-group-text">$</span>
                          <input 
                            type="number" 
                            class="form-control" 
                            formControlName="hourly_rate_bike"
                            placeholder="Bike rate"
                            min="0.01"
                            step="0.01"
                            [class.is-invalid]="isFieldInvalid('hourly_rate_bike')"
                          >
                        </div>
                        <div class="invalid-feedback" *ngIf="isFieldInvalid('hourly_rate_bike')">
                          <div *ngIf="lotForm.get('hourly_rate_bike')?.errors?.['required']">Bike rate required</div>
                          <div *ngIf="lotForm.get('hourly_rate_bike')?.errors?.['min']">Must be greater than 0</div>
                        </div>
                        <div class="form-text">Per hour for bikes</div>
                      </div>
                    </div>
                  </div>

                  <!-- Total Capacity Preview -->
                  <div class="mt-4 p-3 bg-light rounded" *ngIf="totalCapacity > 0">
                    <div class="text-center">
                      <div class="h5 mb-1 text-primary">{{ totalCapacity }}</div>
                      <div class="text-muted small">Total Parking Slots</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Form Validation Summary -->
              <div class="alert alert-danger" *ngIf="lotForm.invalid && (lotForm.dirty || lotForm.touched)">
                <div class="fw-bold mb-2">Please fix the following errors:</div>
                <ul class="mb-0">
                  <li *ngIf="lotForm.get('name')?.invalid">Parking lot name is required</li>
                  <li *ngIf="lotForm.get('address')?.invalid">Address is required</li>
                  <li *ngIf="lotForm.get('latitude')?.invalid">Valid latitude is required</li>
                  <li *ngIf="lotForm.get('longitude')?.invalid">Valid longitude is required</li>
                  <li *ngIf="lotForm.get('total_car_slots')?.invalid">Car slots count is required</li>
                  <li *ngIf="lotForm.get('total_bike_slots')?.invalid">Bike slots count is required</li>
                  <li *ngIf="lotForm.get('hourly_rate_car')?.invalid">Car hourly rate is required</li>
                  <li *ngIf="lotForm.get('hourly_rate_bike')?.invalid">Bike hourly rate is required</li>
                </ul>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" (click)="onCancel()">
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                [disabled]="lotForm.invalid || processing">
                <span *ngIf="processing" class="spinner-border spinner-border-sm me-2" role="status">
                  <span class="visually-hidden">Processing...</span>
                </span>
                <i *ngIf="!processing" class="fas" [class]="isEditMode ? 'fa-save' : 'fa-plus'"></i>
                {{ isEditMode ? 'Update Lot' : 'Create Lot' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-content {
      border-radius: 12px;
      border: none;
      box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .modal-header {
      border-bottom: 1px solid #dee2e6;
      background-color: #f8f9fa;
    }

    .modal-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 600;
    }

    .required::after {
      content: " *";
      color: #dc3545;
    }

    .form-control {
      border-radius: 8px;
      border: 1px solid #d1d5db;
      padding: 0.5rem 0.75rem;
    }

    .form-control:focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 0.2rem rgba(59, 130, 246, 0.25);
    }

    .input-group-text {
      background-color: #f3f4f6;
      border: 1px solid #d1d5db;
      border-radius: 8px 0 0 8px;
    }

    .capacity-section,
    .pricing-section {
      padding: 1rem;
      background-color: #f8fafc;
      border-radius: 8px;
      border: 1px solid #e5e7eb;
    }

    .form-text {
      font-size: 0.75rem;
      color: #6b7280;
      margin-top: 0.25rem;
    }

    .btn {
      border-radius: 8px;
      font-weight: 500;
      padding: 0.5rem 1rem;
    }

    .alert {
      border-radius: 8px;
      border: none;
    }

    .invalid-feedback {
      display: block;
    }

    .is-invalid {
      border-color: #dc3545;
    }

    .bg-light {
      background-color: #f8f9fa !important;
    }

    h6 {
      color: #374151;
      font-weight: 600;
      margin-bottom: 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 2px solid #e5e7eb;
    }

    @media (max-width: 768px) {
      .modal-dialog {
        margin: 0.5rem;
        max-width: calc(100% - 1rem);
      }
      
      .row > .col-6 {
        margin-bottom: 1rem;
      }
    }
  `]
})
export class ParkingLotFormComponent implements OnInit, OnChanges {
  @Input() modalId: string = 'lotFormModal';
  @Input() lot: ParkingLot | null = null;
  @Input() processing: boolean = false;

  @Output() save = new EventEmitter<CreateLotData | UpdateLotData>();
  @Output() cancel = new EventEmitter<void>();

  lotForm: FormGroup;
  isEditMode: boolean = false;

  constructor(private fb: FormBuilder) {
    this.lotForm = this.createForm();
  }

  ngOnInit(): void {
    this.setupForm();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['lot'] && this.lot) {
      this.isEditMode = true;
      this.populateForm();
    } else if (changes['lot'] && !this.lot) {
      this.isEditMode = false;
      this.resetForm();
    }
  }

  private createForm(): FormGroup {
    return this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      address: ['', [Validators.required]],
      latitude: ['', [Validators.required, Validators.min(-90), Validators.max(90)]],
      longitude: ['', [Validators.required, Validators.min(-180), Validators.max(180)]],
      total_car_slots: [0, [Validators.required, Validators.min(0)]],
      total_bike_slots: [0, [Validators.required, Validators.min(0)]],
      hourly_rate_car: ['', [Validators.required, Validators.min(0.01)]],
      hourly_rate_bike: ['', [Validators.required, Validators.min(0.01)]]
    });
  }

  private setupForm(): void {
    // Set default coordinates (New Delhi as example)
    if (!this.isEditMode) {
      this.lotForm.patchValue({
        latitude: 28.6139,
        longitude: 77.2090
      });
    }
  }

  private populateForm(): void {
    if (this.lot) {
      this.lotForm.patchValue({
        name: this.lot.name,
        address: this.lot.address,
        latitude: this.lot.latitude,
        longitude: this.lot.longitude,
        total_car_slots: this.lot.total_car_slots,
        total_bike_slots: this.lot.total_bike_slots,
        hourly_rate_car: this.lot.hourly_rate_car,
        hourly_rate_bike: this.lot.hourly_rate_bike
      });
    }
  }

  private resetForm(): void {
    this.lotForm.reset();
    this.setupForm();
  }

  get totalCapacity(): number {
    const carSlots = this.lotForm.get('total_car_slots')?.value || 0;
    const bikeSlots = this.lotForm.get('total_bike_slots')?.value || 0;
    return carSlots + bikeSlots;
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.lotForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  onSubmit(): void {
    if (this.lotForm.valid) {
      const formData = this.lotForm.value;
      
      // Convert string numbers to actual numbers
      const lotData = {
        ...formData,
        latitude: Number(formData.latitude),
        longitude: Number(formData.longitude),
        total_car_slots: Number(formData.total_car_slots),
        total_bike_slots: Number(formData.total_bike_slots),
        hourly_rate_car: Number(formData.hourly_rate_car),
        hourly_rate_bike: Number(formData.hourly_rate_bike)
      };

      this.save.emit(lotData);
    } else {
      // Mark all fields as touched to show validation errors
      this.lotForm.markAllAsTouched();
    }
  }

  onCancel(): void {
    this.resetForm();
    this.cancel.emit();
  }
}
